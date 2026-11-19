const fs = require("fs");
const path = require("path");

function translateVmFiles(fileMap) {
  const out = [];
  let cmpId = 0;
  let callId = 0;
  let currentFile = "";
  let currentFunc = "";

  const BASE_SEG = { local: "LCL", argument: "ARG", this: "THIS", that: "THAT" };
  const ARITH_OPS = new Set(["add", "sub", "neg", "eq", "gt", "lt", "and", "or", "not"]);

  const emit = (...lines) => out.push(...lines);
  const pushD = () => emit("@SP", "A=M", "M=D", "@SP", "M=M+1");
  const popToD = () => emit("@SP", "AM=M-1", "D=M");
  const scoped = (lbl) => (currentFunc ? `${currentFunc}$${lbl}` : lbl);

  const parsedFiles = Object.entries(fileMap).map(([name, text]) => {
    const stem = name.replace(/\.vm$/i, "");
    const cmds = text
      .split(/\r?\n/)
      .map((line) => line.split("//")[0].trim())
      .filter(Boolean)
      .map((line) => line.split(/\s+/));
    return { stem, cmds };
  });

  const hasSysInit = parsedFiles.some(({ cmds }) =>
    cmds.some(([op, fn]) => op === "function" && fn === "Sys.init")
  );

  function writeCall(fnName, nArgs) {
    const retLabel = `${currentFunc || "Bootstrap"}$ret.${callId++}`;
    emit(`// call ${fnName} ${nArgs}`, `@${retLabel}`, "D=A");
    pushD();
    for (const reg of ["LCL", "ARG", "THIS", "THAT"]) {
      emit(`@${reg}`, "D=M");
      pushD();
    }
    emit("@SP", "D=M", "@5", "D=D-A", `@${nArgs}`, "D=D-A", "@ARG", "M=D");
    emit("@SP", "D=M", "@LCL", "M=D");
    emit(`@${fnName}`, "0;JMP", `(${retLabel})`);
  }

  if (hasSysInit) {
    emit("// Bootstrap", "@256", "D=A", "@SP", "M=D");
    writeCall("Sys.init", 0);
  }

  for (const { stem, cmds } of parsedFiles) {
    currentFile = stem;
    for (const tokens of cmds) {
      const [op, a1, a2] = tokens;
      const idx = Number(a2);

      if (ARITH_OPS.has(op)) {
        emit(`// ${op}`);
        if (op === "add" || op === "sub" || op === "and" || op === "or") {
          popToD();
          emit("A=A-1", { add: "M=M+D", sub: "M=M-D", and: "M=D&M", or: "M=D|M" }[op]);
        } else if (op === "neg" || op === "not") {
          emit("@SP", "A=M-1", op === "neg" ? "M=-M" : "M=!M");
        } else {
          const id = cmpId++;
          const jmp = { eq: "JEQ", gt: "JGT", lt: "JLT" }[op];
          popToD();
          emit(
            "A=A-1", "D=M-D", `@TRUE_${id}`, `D;${jmp}`,
            "@SP", "A=M-1", "M=0", `@END_${id}`, "0;JMP",
            `(TRUE_${id})`, "@SP", "A=M-1", "M=-1", `(END_${id})`
          );
        }
      } else if (op === "push") {
        emit(`// push ${a1} ${idx}`);
        if (a1 === "constant") {
          emit(`@${idx}`, "D=A");
        } else if (BASE_SEG[a1]) {
          emit(`@${idx}`, "D=A", `@${BASE_SEG[a1]}`, "A=D+M", "D=M");
        } else if (a1 === "temp") {
          emit(`@${5 + idx}`, "D=M");
        } else if (a1 === "pointer") {
          emit(`@${idx === 0 ? "THIS" : "THAT"}`, "D=M");
        } else if (a1 === "static") {
          emit(`@${currentFile}.${idx}`, "D=M");
        }
        pushD();
      } else if (op === "pop") {
        emit(`// pop ${a1} ${idx}`);
        if (BASE_SEG[a1]) {
          emit(`@${idx}`, "D=A", `@${BASE_SEG[a1]}`, "D=D+M", "@R13", "M=D");
          popToD();
          emit("@R13", "A=M", "M=D");
        } else if (a1 === "temp") {
          popToD();
          emit(`@${5 + idx}`, "M=D");
        } else if (a1 === "pointer") {
          popToD();
          emit(`@${idx === 0 ? "THIS" : "THAT"}`, "M=D");
        } else if (a1 === "static") {
          popToD();
          emit(`@${currentFile}.${idx}`, "M=D");
        }
      } else if (op === "label") {
        emit(`// label ${a1}`, `(${scoped(a1)})`);
      } else if (op === "goto") {
        emit(`// goto ${a1}`, `@${scoped(a1)}`, "0;JMP");
      } else if (op === "if-goto") {
        emit(`// if-goto ${a1}`);
        popToD();
        emit(`@${scoped(a1)}`, "D;JNE");
      } else if (op === "function") {
        currentFunc = a1;
        emit(`// function ${a1} ${idx}`, `(${a1})`);
        for (let i = 0; i < idx; i++) emit("@SP", "A=M", "M=0", "@SP", "M=M+1");
      } else if (op === "call") {
        writeCall(a1, idx);
      } else if (op === "return") {
        emit("// return", "@LCL", "D=M", "@R13", "M=D", "@5", "A=D-A", "D=M", "@R14", "M=D");
        popToD();
        emit("@ARG", "A=M", "M=D", "@ARG", "D=M+1", "@SP", "M=D");
        for (const reg of ["THAT", "THIS", "ARG", "LCL"]) {
          emit("@R13", "AM=M-1", "D=M", `@${reg}`, "M=D");
        }
        emit("@R14", "A=M", "0;JMP");
      }
    }
  }

  return out.join("\n") + "\n";
}

function main() {
  const inputArg = process.argv[2];
  if (!inputArg) {
    console.error("用法: node vm.js <file.vm | directory>");
    process.exit(1);
  }

  const target = path.resolve(inputArg);
  if (!fs.existsSync(target)) {
    console.error(`找不到路徑: ${target}`);
    process.exit(1);
  }

  const stat = fs.statSync(target);
  const fileMap = {};
  let outputAsm = "";

  if (stat.isFile()) {
    if (path.extname(target) !== ".vm") {
      console.error("輸入檔案必須為 .vm 格式");
      process.exit(1);
    }
    fileMap[path.basename(target)] = fs.readFileSync(target, "utf8");
    outputAsm = target.replace(/\.vm$/i, ".asm");
  } else if (stat.isDirectory()) {
    const vmFiles = fs.readdirSync(target).filter((f) => f.endsWith(".vm")).sort();
    if (vmFiles.length === 0) {
      console.error(`資料夾內找不到 .vm 檔案: ${target}`);
      process.exit(1);
    }
    for (const file of vmFiles) {
      fileMap[file] = fs.readFileSync(path.join(target, file), "utf8");
    }
    outputAsm = path.join(target, `${path.basename(target)}.asm`);
  }

  const asmCode = translateVmFiles(fileMap);
  fs.writeFileSync(outputAsm, asmCode, "utf8");
  console.log(`已產生: ${outputAsm}`);
}

if (require.main === module) {
  main();
}

module.exports = { translateVmFiles };