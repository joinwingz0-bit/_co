import sys
from enum import Enum, auto
from pathlib import Path


class CommandType(Enum):
    C_ARITHMETIC = auto()
    C_PUSH = auto()
    C_POP = auto()
    C_LABEL = auto()
    C_GOTO = auto()
    C_IF = auto()
    C_FUNCTION = auto()
    C_RETURN = auto()
    C_CALL = auto()


class Parser:
    """解析單一 .vm 檔案，移除 // 註解與空白行。"""

    ARITHMETIC_OPS = {
        "add", "sub", "neg",
        "eq", "gt", "lt",
        "and", "or", "not",
    }

    COMMAND_MAP = {
        "push": CommandType.C_PUSH,
        "pop": CommandType.C_POP,
        "label": CommandType.C_LABEL,
        "goto": CommandType.C_GOTO,
        "if-goto": CommandType.C_IF,
        "function": CommandType.C_FUNCTION,
        "return": CommandType.C_RETURN,
        "call": CommandType.C_CALL,
    }

    def __init__(self, vm_path: Path):
        self.lines: list[str] = []
        with vm_path.open("r", encoding="utf-8") as f:
            for raw in f:
                clean = raw.split("//", 1)[0].strip()
                if clean:
                    self.lines.append(clean)

        self.index = -1
        self.current_command = ""
        self.tokens: list[str] = []

    def has_more_lines(self) -> bool:
        return self.index + 1 < len(self.lines)

    def advance(self) -> None:
        self.index += 1
        self.current_command = self.lines[self.index]
        self.tokens = self.current_command.split()

    def command_type(self) -> CommandType:
        op = self.tokens[0]
        if op in self.ARITHMETIC_OPS:
            return CommandType.C_ARITHMETIC
        if op in self.COMMAND_MAP:
            return self.COMMAND_MAP[op]
        raise ValueError(f"無效的 VM 指令: {self.current_command}")

    def arg1(self) -> str:
        ctype = self.command_type()
        if ctype == CommandType.C_RETURN:
            raise RuntimeError("C_RETURN 不接受 arg1()")
        return self.tokens[0] if ctype == CommandType.C_ARITHMETIC else self.tokens[1]

    def arg2(self) -> int:
        ctype = self.command_type()
        if ctype not in {
            CommandType.C_PUSH,
            CommandType.C_POP,
            CommandType.C_FUNCTION,
            CommandType.C_CALL,
        }:
            raise RuntimeError(f"{ctype} 不接受 arg2()")
        return int(self.tokens[2])


class CodeWriter:
    """將 VM 指令翻譯為 Hack 組合語言（.asm）。"""

    BASE_SEGMENTS = {
        "local": "LCL",
        "argument": "ARG",
        "this": "THIS",
        "that": "THAT",
    }

    def __init__(self, output_path: Path):
        self.out = output_path.open("w", encoding="utf-8")
        self.file_name = ""
        self.function_name = ""
        self.cmp_id = 0
        self.call_id = 0

    def set_file_name(self, file_name: str) -> None:
        self.file_name = file_name

    def _write(self, *asm_lines: str) -> None:
        for line in asm_lines:
            self.out.write(line + "\n")

    def _push_d(self) -> None:
        """*SP = D; SP++"""
        self._write("@SP", "A=M", "M=D", "@SP", "M=M+1")

    def _pop_to_d(self) -> None:
        """SP--; D = *SP"""
        self._write("@SP", "AM=M-1", "D=M")

    def write_init(self) -> None:
        """Bootstrap 開機引導碼：SP = 256 並呼叫 Sys.init。"""
        self._write("// Bootstrap", "@256", "D=A", "@SP", "M=D")
        self.write_call("Sys.init", 0)

    def write_arithmetic(self, command: str) -> None:
        self._write(f"// {command}")

        if command in {"add", "sub", "and", "or"}:
            self._pop_to_d()
            self._write("A=A-1")
            alu_op = {
                "add": "M=M+D",
                "sub": "M=M-D",
                "and": "M=D&M",
                "or": "M=D|M",
            }[command]
            self._write(alu_op)

        elif command in {"neg", "not"}:
            self._write("@SP", "A=M-1", "M=-M" if command == "neg" else "M=!M")

        elif command in {"eq", "gt", "lt"}:
            uid = self.cmp_id
            self.cmp_id += 1
            jmp = {"eq": "JEQ", "gt": "JGT", "lt": "JLT"}[command]

            self._pop_to_d()
            self._write(
                "A=A-1",
                "D=M-D",
                f"@TRUE_{uid}",
                f"D;{jmp}",
                "@SP",
                "A=M-1",
                "M=0",
                f"@END_CMP_{uid}",
                "0;JMP",
                f"(TRUE_{uid})",
                "@SP",
                "A=M-1",
                "M=-1",
                f"(END_CMP_{uid})",
            )

    def write_push_pop(self, command: CommandType, segment: str, index: int) -> None:
        action = "push" if command == CommandType.C_PUSH else "pop"
        self._write(f"// {action} {segment} {index}")

        if command == CommandType.C_PUSH:
            if segment == "constant":
                self._write(f"@{index}", "D=A")
                self._push_d()
            elif segment in self.BASE_SEGMENTS:
                base = self.BASE_SEGMENTS[segment]
                self._write(f"@{index}", "D=A", f"@{base}", "A=D+M", "D=M")
                self._push_d()
            elif segment == "temp":
                self._write(f"@{5 + index}", "D=M")
                self._push_d()
            elif segment == "pointer":
                ptr = "THIS" if index == 0 else "THAT"
                self._write(f"@{ptr}", "D=M")
                self._push_d()
            elif segment == "static":
                self._write(f"@{self.file_name}.{index}", "D=M")
                self._push_d()
            else:
                raise ValueError(f"不支援的記憶體區段: {segment}")

        elif command == CommandType.C_POP:
            if segment in self.BASE_SEGMENTS:
                base = self.BASE_SEGMENTS[segment]
                self._write(f"@{index}", "D=A", f"@{base}", "D=D+M", "@R13", "M=D")
                self._pop_to_d()
                self._write("@R13", "A=M", "M=D")
            elif segment == "temp":
                self._pop_to_d()
                self._write(f"@{5 + index}", "M=D")
            elif segment == "pointer":
                ptr = "THIS" if index == 0 else "THAT"
                self._pop_to_d()
                self._write(f"@{ptr}", "M=D")
            elif segment == "static":
                self._pop_to_d()
                self._write(f"@{self.file_name}.{index}", "M=D")
            else:
                raise ValueError(f"不支援的 pop 區段: {segment}")

    def _scoped_label(self, label: str) -> str:
        return f"{self.function_name}${label}" if self.function_name else label

    def write_label(self, label: str) -> None:
        self._write(f"// label {label}", f"({self._scoped_label(label)})")

    def write_goto(self, label: str) -> None:
        self._write(f"// goto {label}", f"@{self._scoped_label(label)}", "0;JMP")

    def write_if(self, label: str) -> None:
        self._write(f"// if-goto {label}")
        self._pop_to_d()
        self._write(f"@{self._scoped_label(label)}", "D;JNE")

    def write_function(self, function_name: str, n_vars: int) -> None:
        self.function_name = function_name
        self._write(f"// function {function_name} {n_vars}", f"({function_name})")
        for _ in range(n_vars):
            self._write("@SP", "A=M", "M=0", "@SP", "M=M+1")

    def write_call(self, function_name: str, n_args: int) -> None:
        caller = self.function_name or "Bootstrap"
        ret_label = f"{caller}$ret.{self.call_id}"
        self.call_id += 1

        self._write(f"// call {function_name} {n_args}")
        self._write(f"@{ret_label}", "D=A")
        self._push_d()

        for reg in ("LCL", "ARG", "THIS", "THAT"):
            self._write(f"@{reg}", "D=M")
            self._push_d()

        # ARG = SP - 5 - nArgs
        self._write(
            "@SP", "D=M",
            "@5", "D=D-A",
            f"@{n_args}", "D=D-A",
            "@ARG", "M=D",
        )
        # LCL = SP
        self._write("@SP", "D=M", "@LCL", "M=D")
        self._write(f"@{function_name}", "0;JMP", f"({ret_label})")

    def write_return(self) -> None:
        self._write("// return")
        # endFrame (R13) = LCL
        self._write("@LCL", "D=M", "@R13", "M=D")
        # retAddr (R14) = *(endFrame - 5) —— 必須在 *ARG = pop() 之前先保存
        self._write("@5", "A=D-A", "D=M", "@R14", "M=D")
        # *ARG = pop()
        self._pop_to_d()
        self._write("@ARG", "A=M", "M=D")
        # SP = ARG + 1
        self._write("@ARG", "D=M+1", "@SP", "M=D")
        # 依序還原 THAT, THIS, ARG, LCL
        for reg in ("THAT", "THIS", "ARG", "LCL"):
            self._write("@R13", "AM=M-1", "D=M", f"@{reg}", "M=D")
        # 跳轉回呼叫端
        self._write("@R14", "A=M", "0;JMP")

    def close(self) -> None:
        self.out.close()


def has_sys_init(vm_files: list[Path]) -> bool:
    """檢查輸入的 .vm 檔案中是否定義了 function Sys.init。"""
    for vm_file in vm_files:
        parser = Parser(vm_file)
        while parser.has_more_lines():
            parser.advance()
            if parser.command_type() == CommandType.C_FUNCTION and parser.arg1() == "Sys.init":
                return True
    return False


def translate(input_path: Path) -> Path:
    if input_path.is_file():
        vm_files = [input_path]
        output_asm = input_path.with_suffix(".asm")
    elif input_path.is_dir():
        vm_files = sorted(input_path.glob("*.vm"))
        if not vm_files:
            raise FileNotFoundError(f"資料夾內找不到 .vm 檔案: {input_path}")
        output_asm = input_path / f"{input_path.name}.asm"
    else:
        raise FileNotFoundError(f"路徑不存在: {input_path}")

    need_bootstrap = has_sys_init(vm_files)
    writer = CodeWriter(output_asm)

    try:
        if need_bootstrap:
            writer.write_init()

        for vm_file in vm_files:
            writer.set_file_name(vm_file.stem)
            parser = Parser(vm_file)
            while parser.has_more_lines():
                parser.advance()
                ctype = parser.command_type()
                if ctype == CommandType.C_ARITHMETIC:
                    writer.write_arithmetic(parser.arg1())
                elif ctype in {CommandType.C_PUSH, CommandType.C_POP}:
                    writer.write_push_pop(ctype, parser.arg1(), parser.arg2())
                elif ctype == CommandType.C_LABEL:
                    writer.write_label(parser.arg1())
                elif ctype == CommandType.C_GOTO:
                    writer.write_goto(parser.arg1())
                elif ctype == CommandType.C_IF:
                    writer.write_if(parser.arg1())
                elif ctype == CommandType.C_FUNCTION:
                    writer.write_function(parser.arg1(), parser.arg2())
                elif ctype == CommandType.C_CALL:
                    writer.write_call(parser.arg1(), parser.arg2())
                elif ctype == CommandType.C_RETURN:
                    writer.write_return()
    finally:
        writer.close()

    return output_asm


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python VMTranslator.py <file.vm | directory>")
        sys.exit(1)
    out = translate(Path(sys.argv[1]).resolve())
    print(f"已產生: {out}")