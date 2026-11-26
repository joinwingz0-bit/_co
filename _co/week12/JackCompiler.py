import os
import sys
from typing import Optional, Tuple, List, Dict


# ==========================================
# 1. 詞法分析器 (JackTokenizer)
# ==========================================
class JackTokenizer:
    KEYWORDS = {
        "class", "constructor", "function", "method", "field", "static",
        "var", "int", "char", "boolean", "void", "true", "false", "null",
        "this", "let", "do", "if", "else", "while", "return"
    }
    SYMBOLS = {
        "{", "}", "(", ")", "[", "]", ".", ",", ";",
        "+", "-", "*", "/", "&", "|", "<", ">", "=", "~"
    }

    def __init__(self, source_code: str):
        self.tokens: List[Tuple[str, str]] = self._tokenize(source_code)
        self.pos: int = 0

    def _tokenize(self, code: str) -> List[Tuple[str, str]]:
        tokens: List[Tuple[str, str]] = []
        i = 0
        n = len(code)

        while i < n:
            ch = code[i]

            # 跳過空白字元
            if ch.isspace():
                i += 1
                continue

            # 單行註解 //
            if ch == "/" and i + 1 < n and code[i + 1] == "/":
                i += 2
                while i < n and code[i] != "\n":
                    i += 1
                continue

            # 多行或文件註解 /* ... */ 或 /** ... */
            if ch == "/" and i + 1 < n and code[i + 1] == "*":
                i += 2
                while i + 1 < n and not (code[i] == "*" and code[i + 1] == "/"):
                    i += 1
                i += 2
                continue

            # 字串常數 "..."
            if ch == '"':
                i += 1
                start = i
                while i < n and code[i] != '"':
                    i += 1
                tokens.append(("STRING_CONST", code[start:i]))
                i += 1  # 跳過結尾引號
                continue

            # 符號
            if ch in self.SYMBOLS:
                tokens.append(("SYMBOL", ch))
                i += 1
                continue

            # 整數常數
            if ch.isdigit():
                start = i
                while i < n and code[i].isdigit():
                    i += 1
                tokens.append(("INT_CONST", code[start:i]))
                continue

            # 識別字或關鍵字
            if ch.isalpha() or ch == "_":
                start = i
                while i < n and (code[i].isalnum() or code[i] == "_"):
                    i += 1
                word = code[start:i]
                if word in self.KEYWORDS:
                    tokens.append(("KEYWORD", word))
                else:
                    tokens.append(("IDENTIFIER", word))
                continue

            raise SyntaxError(f"無法辨識的字元: {ch!r} (位置 {i})")

        return tokens

    def has_more_tokens(self) -> bool:
        return self.pos < len(self.tokens)

    def current(self) -> Tuple[str, str]:
        if not self.has_more_tokens():
            raise SyntaxError("意外到達檔案結尾 (EOF)")
        return self.tokens[self.pos]

    def peek(self, offset: int = 1) -> Optional[Tuple[str, str]]:
        idx = self.pos + offset
        return self.tokens[idx] if idx < len(self.tokens) else None

    def advance(self) -> Tuple[str, str]:
        tok = self.current()
        self.pos += 1
        return tok


# ==========================================
# 2. 符號表 (SymbolTable)
# ==========================================
class SymbolTable:
    KIND_TO_SEGMENT = {
        "STATIC": "static",
        "FIELD": "this",
        "ARG": "argument",
        "VAR": "local",
    }

    def __init__(self):
        self.class_scope: Dict[str, Tuple[str, str, int]] = {}
        self.subroutine_scope: Dict[str, Tuple[str, str, int]] = {}
        self.indices: Dict[str, int] = {
            "STATIC": 0,
            "FIELD": 0,
            "ARG": 0,
            "VAR": 0,
        }

    def start_subroutine(self) -> None:
        self.subroutine_scope.clear()
        self.indices["ARG"] = 0
        self.indices["VAR"] = 0

    def define(self, name: str, var_type: str, kind: str) -> None:
        kind = kind.upper()
        idx = self.indices[kind]
        self.indices[kind] += 1
        entry = (var_type, kind, idx)
        if kind in ("STATIC", "FIELD"):
            self.class_scope[name] = entry
        else:
            self.subroutine_scope[name] = entry

    def var_count(self, kind: str) -> int:
        return self.indices[kind.upper()]

    def _lookup(self, name: str) -> Optional[Tuple[str, str, int]]:
        if name in self.subroutine_scope:
            return self.subroutine_scope[name]
        if name in self.class_scope:
            return self.class_scope[name]
        return None

    def kind_of(self, name: str) -> Optional[str]:
        entry = self._lookup(name)
        return entry[1] if entry else None

    def type_of(self, name: str) -> Optional[str]:
        entry = self._lookup(name)
        return entry[0] if entry else None

    def index_of(self, name: str) -> Optional[int]:
        entry = self._lookup(name)
        return entry[2] if entry else None

    def segment_of(self, name: str) -> Optional[str]:
        kind = self.kind_of(name)
        return self.KIND_TO_SEGMENT[kind] if kind else None


# ==========================================
# 3. VM 碼生成器 (VMWriter)
# ==========================================
class VMWriter:
    def __init__(self, output_path: str):
        self.file = open(output_path, "w", encoding="utf-8")

    def write_push(self, segment: str, index: int) -> None:
        self.file.write(f"push {segment} {index}\n")

    def write_pop(self, segment: str, index: int) -> None:
        self.file.write(f"pop {segment} {index}\n")

    def write_arithmetic(self, command: str) -> None:
        self.file.write(f"{command}\n")

    def write_label(self, label: str) -> None:
        self.file.write(f"label {label}\n")

    def write_goto(self, label: str) -> None:
        self.file.write(f"goto {label}\n")

    def write_if(self, label: str) -> None:
        self.file.write(f"if-goto {label}\n")

    def write_call(self, name: str, n_args: int) -> None:
        self.file.write(f"call {name} {n_args}\n")

    def write_function(self, name: str, n_locals: int) -> None:
        self.file.write(f"function {name} {n_locals}\n")

    def write_return(self) -> None:
        self.file.write("return\n")

    def close(self) -> None:
        self.file.close()


# ==========================================
# 4. 語法與語意編譯引擎 (CompilationEngine)
# ==========================================
class CompilationEngine:
    BINARY_OPS = {
        "+": ("add", False),
        "-": ("sub", False),
        "*": ("Math.multiply", True),
        "/": ("Math.divide", True),
        "&": ("and", False),
        "|": ("or", False),
        "<": ("lt", False),
        ">": ("gt", False),
        "=": ("eq", False),
    }

    def __init__(self, tokenizer: JackTokenizer, vm_writer: VMWriter):
        self.tk = tokenizer
        self.vm = vm_writer
        self.symbols = SymbolTable()
        self.class_name: str = ""
        self.label_counter: int = 0

    def _new_label(self, prefix: str) -> str:
        lbl = f"{prefix}_{self.label_counter}"
        self.label_counter += 1
        return lbl

    def _eat(self, expected_type: str, expected_val: Optional[str] = None) -> str:
        tok_type, tok_val = self.tk.advance()
        if tok_type != expected_type:
            raise SyntaxError(f"預期 Token 類型 {expected_type}，但得到 {tok_type} ({tok_val})")
        if expected_val is not None and tok_val != expected_val:
            raise SyntaxError(f"預期 '{expected_val}'，但得到 '{tok_val}'")
        return tok_val

    def _eat_type(self) -> str:
        tok_type, tok_val = self.tk.advance()
        if tok_type == "KEYWORD" and tok_val in ("int", "char", "boolean"):
            return tok_val
        if tok_type == "IDENTIFIER":
            return tok_val
        raise SyntaxError(f"無效的型別宣告: {tok_val}")

    # class: 'class' className '{' classVarDec* subroutineDec* '}'
    def compile_class(self) -> None:
        self._eat("KEYWORD", "class")
        self.class_name = self._eat("IDENTIFIER")
        self._eat("SYMBOL", "{")

        while self.tk.has_more_tokens():
            tok_type, tok_val = self.tk.current()
            if tok_type == "KEYWORD" and tok_val in ("static", "field"):
                self.compile_class_var_dec()
            elif tok_type == "KEYWORD" and tok_val in ("constructor", "function", "method"):
                self.compile_subroutine()
            else:
                break

        self._eat("SYMBOL", "}")

    # classVarDec: ('static' | 'field') type varName (',' varName)* ';'
    def compile_class_var_dec(self) -> None:
        kind = self._eat("KEYWORD")  # static 或 field
        var_type = self._eat_type()
        var_name = self._eat("IDENTIFIER")
        self.symbols.define(var_name, var_type, kind)

        while self.tk.current() == ("SYMBOL", ","):
            self._eat("SYMBOL", ",")
            var_name = self._eat("IDENTIFIER")
            self.symbols.define(var_name, var_type, kind)

        self._eat("SYMBOL", ";")

    # subroutineDec: ('constructor' | 'function' | 'method') ('void' | type)
    #                subroutineName '(' parameterList ')' subroutineBody
    def compile_subroutine(self) -> None:
        self.symbols.start_subroutine()
        sub_kind = self._eat("KEYWORD")  # constructor, function, method

        # 若為 method，argument 0 保留給呼叫端傳入的 this 物件位址
        if sub_kind == "method":
            self.symbols.define("this", self.class_name, "ARG")

        if self.tk.current() == ("KEYWORD", "void"):
            self._eat("KEYWORD", "void")
        else:
            self._eat_type()

        sub_name = self._eat("IDENTIFIER")
        self._eat("SYMBOL", "(")
        self.compile_parameter_list()
        self._eat("SYMBOL", ")")

        # subroutineBody: '{' varDec* statements '}'
        self._eat("SYMBOL", "{")
        while self.tk.current() == ("KEYWORD", "var"):
            self.compile_var_dec()

        n_locals = self.symbols.var_count("VAR")
        self.vm.write_function(f"{self.class_name}.{sub_name}", n_locals)

        if sub_kind == "constructor":
            # 配置物件所需的欄位記憶體並將基底位址存入 pointer 0 (this)
            n_fields = self.symbols.var_count("FIELD")
            self.vm.write_push("constant", n_fields)
            self.vm.write_call("Memory.alloc", 1)
            self.vm.write_pop("pointer", 0)
        elif sub_kind == "method":
            # 將 argument 0 設定為目前物件的 this 指標
            self.vm.write_push("argument", 0)
            self.vm.write_pop("pointer", 0)

        self.compile_statements()
        self._eat("SYMBOL", "}")

    # parameterList: ((type varName) (',' type varName)*)?
    def compile_parameter_list(self) -> None:
        if self.tk.current() == ("SYMBOL", ")"):
            return

        var_type = self._eat_type()
        var_name = self._eat("IDENTIFIER")
        self.symbols.define(var_name, var_type, "ARG")

        while self.tk.current() == ("SYMBOL", ","):
            self._eat("SYMBOL", ",")
            var_type = self._eat_type()
            var_name = self._eat("IDENTIFIER")
            self.symbols.define(var_name, var_type, "ARG")

    # varDec: 'var' type varName (',' varName)* ';'
    def compile_var_dec(self) -> None:
        self._eat("KEYWORD", "var")
        var_type = self._eat_type()
        var_name = self._eat("IDENTIFIER")
        self.symbols.define(var_name, var_type, "VAR")

        while self.tk.current() == ("SYMBOL", ","):
            self._eat("SYMBOL", ",")
            var_name = self._eat("IDENTIFIER")
            self.symbols.define(var_name, var_type, "VAR")

        self._eat("SYMBOL", ";")

    # statements: statement*
    def compile_statements(self) -> None:
        while self.tk.has_more_tokens():
            tok_type, tok_val = self.tk.current()
            if tok_type != "KEYWORD":
                break
            if tok_val == "let":
                self.compile_let()
            elif tok_val == "if":
                self.compile_if()
            elif tok_val == "while":
                self.compile_while()
            elif tok_val == "do":
                self.compile_do()
            elif tok_val == "return":
                self.compile_return()
            else:
                break

    # letStatement: 'let' varName ('[' expression ']')? '=' expression ';'
    def compile_let(self) -> None:
        self._eat("KEYWORD", "let")
        var_name = self._eat("IDENTIFIER")
        seg = self.symbols.segment_of(var_name)
        idx = self.symbols.index_of(var_name)
        if seg is None or idx is None:
            raise NameError(f"未宣告的變數: {var_name}")

        is_array = False
        if self.tk.current() == ("SYMBOL", "["):
            is_array = True
            self._eat("SYMBOL", "[")
            self.vm.write_push(seg, idx)
            self.compile_expression()
            self._eat("SYMBOL", "]")
            self.vm.write_arithmetic("add")  # 堆疊頂端為目標位址 (base + offset)

        self._eat("SYMBOL", "=")
        self.compile_expression()
        self._eat("SYMBOL", ";")

        if is_array:
            # 使用 temp 0 暫存右側運算結果，避免計算右側時覆蓋 pointer 1 (THAT)
            self.vm.write_pop("temp", 0)
            self.vm.write_pop("pointer", 1)
            self.vm.write_push("temp", 0)
            self.vm.write_pop("that", 0)
        else:
            self.vm.write_pop(seg, idx)

    # ifStatement: 'if' '(' expression ')' '{' statements '}' ('else' '{' statements '}')?
    def compile_if(self) -> None:
        else_label = self._new_label("IF_ELSE")
        end_label = self._new_label("IF_END")

        self._eat("KEYWORD", "if")
        self._eat("SYMBOL", "(")
        self.compile_expression()
        self._eat("SYMBOL", ")")

        self.vm.write_arithmetic("not")
        self.vm.write_if(else_label)

        self._eat("SYMBOL", "{")
        self.compile_statements()
        self._eat("SYMBOL", "}")

        if self.tk.current() == ("KEYWORD", "else"):
            self.vm.write_goto(end_label)
            self.vm.write_label(else_label)
            self._eat("KEYWORD", "else")
            self._eat("SYMBOL", "{")
            self.compile_statements()
            self._eat("SYMBOL", "}")
            self.vm.write_label(end_label)
        else:
            self.vm.write_label(else_label)

    # whileStatement: 'while' '(' expression ')' '{' statements '}'
    def compile_while(self) -> None:
        exp_label = self._new_label("WHILE_EXP")
        end_label = self._new_label("WHILE_END")

        self.vm.write_label(exp_label)
        self._eat("KEYWORD", "while")
        self._eat("SYMBOL", "(")
        self.compile_expression()
        self._eat("SYMBOL", ")")

        self.vm.write_arithmetic("not")
        self.vm.write_if(end_label)

        self._eat("SYMBOL", "{")
        self.compile_statements()
        self._eat("SYMBOL", "}")

        self.vm.write_goto(exp_label)
        self.vm.write_label(end_label)

    # doStatement: 'do' subroutineCall ';'
    def compile_do(self) -> None:
        self._eat("KEYWORD", "do")
        self._compile_subroutine_call()
        self._eat("SYMBOL", ";")
        self.vm.write_pop("temp", 0)  # 丟棄 void 或未使用的回傳值

    # returnStatement: 'return' expression? ';'
    def compile_return(self) -> None:
        self._eat("KEYWORD", "return")
        if self.tk.current() == ("SYMBOL", ";"):
            self.vm.write_push("constant", 0)
        else:
            self.compile_expression()
        self._eat("SYMBOL", ";")
        self.vm.write_return()

    # expression: term (op term)*
    def compile_expression(self) -> None:
        self.compile_term()
        while self.tk.has_more_tokens():
            tok_type, tok_val = self.tk.current()
            if tok_type == "SYMBOL" and tok_val in self.BINARY_OPS:
                op = self._eat("SYMBOL")
                self.compile_term()
                cmd, is_call = self.BINARY_OPS[op]
                if is_call:
                    self.vm.write_call(cmd, 2)
                else:
                    self.vm.write_arithmetic(cmd)
            else:
                break

    # term: integerConstant | stringConstant | keywordConstant | varName |
    #       varName '[' expression ']' | subroutineCall | '(' expression ')' | unaryOp term
    def compile_term(self) -> None:
        tok_type, tok_val = self.tk.current()

        if tok_type == "INT_CONST":
            val = int(self._eat("INT_CONST"))
            self.vm.write_push("constant", val)

        elif tok_type == "STRING_CONST":
            s = self._eat("STRING_CONST")
            self.vm.write_push("constant", len(s))
            self.vm.write_call("String.new", 1)
            for ch in s:
                self.vm.write_push("constant", ord(ch))
                self.vm.write_call("String.appendChar", 2)

        elif tok_type == "KEYWORD":
            kw = self._eat("KEYWORD")
            if kw == "true":
                self.vm.write_push("constant", 0)
                self.vm.write_arithmetic("not")  # -1 (0xFFFF)
            elif kw in ("false", "null"):
                self.vm.write_push("constant", 0)
            elif kw == "this":
                self.vm.write_push("pointer", 0)
            else:
                raise SyntaxError(f"運算式中出現非預期的關鍵字: {kw}")

        elif tok_type == "SYMBOL" and tok_val == "(":
            self._eat("SYMBOL", "(")
            self.compile_expression()
            self._eat("SYMBOL", ")")

        elif tok_type == "SYMBOL" and tok_val in ("-", "~"):
            op = self._eat("SYMBOL")
            self.compile_term()
            self.vm.write_arithmetic("neg" if op == "-" else "not")

        elif tok_type == "IDENTIFIER":
            next_tok = self.tk.peek()
            if next_tok == ("SYMBOL", "["):
                # 陣列取值: varName '[' expression ']'
                var_name = self._eat("IDENTIFIER")
                seg = self.symbols.segment_of(var_name)
                idx = self.symbols.index_of(var_name)
                if seg is None or idx is None:
                    raise NameError(f"未宣告的陣列變數: {var_name}")
                self.vm.write_push(seg, idx)
                self._eat("SYMBOL", "[")
                self.compile_expression()
                self._eat("SYMBOL", "]")
                self.vm.write_arithmetic("add")
                self.vm.write_pop("pointer", 1)
                self.vm.write_push("that", 0)

            elif next_tok in (("SYMBOL", "("), ("SYMBOL", ".")):
                # 副程式呼叫
                self._compile_subroutine_call()

            else:
                # 一般變數讀取
                var_name = self._eat("IDENTIFIER")
                seg = self.symbols.segment_of(var_name)
                idx = self.symbols.index_of(var_name)
                if seg is None or idx is None:
                    raise NameError(f"未宣告的變數: {var_name}")
                self.vm.write_push(seg, idx)

        else:
            raise SyntaxError(f"無效的運算項 (term): {tok_type} ({tok_val})")

    # subroutineCall: subroutineName '(' expressionList ')' |
    #                 (className | varName) '.' subroutineName '(' expressionList ')'
    def _compile_subroutine_call(self) -> None:
        first_name = self._eat("IDENTIFIER")

        if self.tk.current() == ("SYMBOL", "("):
            # 呼叫同一類別內的 method: methodName(args)
            self.vm.write_push("pointer", 0)
            self._eat("SYMBOL", "(")
            n_args = self.compile_expression_list()
            self._eat("SYMBOL", ")")
            self.vm.write_call(f"{self.class_name}.{first_name}", n_args + 1)

        elif self.tk.current() == ("SYMBOL", "."):
            self._eat("SYMBOL", ".")
            sub_name = self._eat("IDENTIFIER")

            obj_type = self.symbols.type_of(first_name)
            if obj_type is not None:
                # 透過物件變數呼叫 method: objVar.methodName(args)
                seg = self.symbols.segment_of(first_name)
                idx = self.symbols.index_of(first_name)
                assert seg is not None and idx is not None
                self.vm.write_push(seg, idx)
                self._eat("SYMBOL", "(")
                n_args = self.compile_expression_list()
                self._eat("SYMBOL", ")")
                self.vm.write_call(f"{obj_type}.{sub_name}", n_args + 1)
            else:
                # 呼叫外部類別的 function 或 constructor: ClassName.funcName(args)
                self._eat("SYMBOL", "(")
                n_args = self.compile_expression_list()
                self._eat("SYMBOL", ")")
                self.vm.write_call(f"{first_name}.{sub_name}", n_args)
        else:
            raise SyntaxError(f"副程式呼叫語法錯誤: {first_name}")

    # expressionList: (expression (',' expression)*)?
    def compile_expression_list(self) -> int:
        count = 0
        if self.tk.current() == ("SYMBOL", ")"):
            return count

        self.compile_expression()
        count += 1

        while self.tk.current() == ("SYMBOL", ","):
            self._eat("SYMBOL", ",")
            self.compile_expression()
            count += 1

        return count


# ==========================================
# 5. 主程式進入點 (支援單檔或整個專案資料夾)
# ==========================================
def compile_file(jack_path: str) -> None:
    vm_path = os.path.splitext(jack_path)[0] + ".vm"
    with open(jack_path, "r", encoding="utf-8") as f:
        source = f.read()

    tokenizer = JackTokenizer(source)
    writer = VMWriter(vm_path)
    try:
        engine = CompilationEngine(tokenizer, writer)
        engine.compile_class()
    finally:
        writer.close()


def main() -> None:
    if len(sys.argv) != 2:
        print("用法: python JackCompiler.py <檔案.jack 或 專案資料夾路徑>")
        sys.exit(1)

    target = sys.argv[1]
    if os.path.isdir(target):
        jack_files = [
            os.path.join(target, fname)
            for fname in sorted(os.listdir(target))
            if fname.endswith(".jack")
        ]
        if not jack_files:
            print(f"資料夾中找不到任何 .jack 檔案: {target}")
            sys.exit(1)
        for jf in jack_files:
            compile_file(jf)
            print(f"已編譯: {jf} -> {os.path.splitext(jf)[0]}.vm")
    elif os.path.isfile(target) and target.endswith(".jack"):
        compile_file(target)
        print(f"已編譯: {target} -> {os.path.splitext(target)[0]}.vm")
    else:
        print(f"無效的輸入路徑: {target}")
        sys.exit(1)


if __name__ == "__main__":
    main()