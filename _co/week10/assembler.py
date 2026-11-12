import sys
import os

# 1. 預定義符號表 (Predefined Symbols)
 def create_symbol_table():
    table = {
        "SP": 0, "LCL": 1, "ARG": 2, "THIS": 3, "THAT": 4,
        "SCREEN": 16384, "KBD": 24576
    }
    for i in range(16):
        table[f"R{i}"] = i
    return table

# 2. C-Instruction 對照表 (comp, dest, jump)
COMP_TABLE = {
    # a = 0
    "0":   "0101010", "1":   "0111111", "-1":  "0111010",
    "D":   "0001100", "A":   "0110000", "!D":  "0001101",
    "!A":  "0110001", "-D":  "0001111", "-A":  "0110011",
    "D+1": "0011111", "A+1": "0110111", "D-1": "0001110",
    "A-1": "0110010", "D+A": "0000010", "D-A": "0010011",
    "A-D": "0000111", "D&A": "0000000", "D|A": "0010101",
    # a = 1 (將 A 替換為 M)
    "M":   "1110000", "!M":  "1110001", "-M":  "1110011",
    "M+1": "1110111", "M-1": "1110010", "D+M": "1000010",
    "D-M": "1010011", "M-D": "1000111", "D&M": "1000000",
    "D|M": "1010101"
}

DEST_TABLE = {
    "":    "000", "M":   "001", "D":   "010", "MD":  "011",
    "DM":  "011", "A":   "100", "AM":  "101", "MA":  "101",
    "AD":  "110", "DA":  "110", "AMD": "111", "ADM": "111"
}

JUMP_TABLE = {
    "":    "000", "JGT": "001", "JEQ": "010", "JGE": "011",
    "JLT": "100", "JNE": "101", "JLE": "110", "JMP": "111"
}


def clean_lines(raw_lines):
    """移除註解與空白字元，僅保留有效指令與標籤"""
    cleaned = []
    for line in raw_lines:
        # 移除 // 之後的註解並清除前後空白與指令內空白
        code = line.split("//")[0].strip().replace(" ", "")
        if code:
            cleaned.append(code)
    return cleaned


def first_pass(lines, symbol_table):
    """
    第一階段：掃描所有 (LABEL) 標籤，記錄其對應的 ROM 位址，
    並回傳不含 (LABEL) 偽指令的純指令列表。
    """
    instructions = []
    rom_address = 0
    for line in lines:
        if line.startswith("(") and line.endswith(")"):
            label = line[1:-1]
            symbol_table[label] = rom_address
        else:
            instructions.append(line)
            rom_address += 1
    return instructions


def translate_a_instruction(inst, symbol_table, next_ram_address):
    """翻譯 A 指令 (@value 或 @symbol) 為 16-bit 二進位字串"""
    symbol = inst[1:]
    if symbol.isdigit():
        address = int(symbol)
    else:
        if symbol not in symbol_table:
            symbol_table[symbol] = next_ram_address
            next_ram_address += 1
        address = symbol_table[symbol]
    
    return f"0{address:015b}", next_ram_address


def translate_c_instruction(inst):
    """翻譯 C 指令 (dest=comp;jump) 為 16-bit 二進位字串"""
    dest, comp, jump = "", inst, ""
    
    if "=" in comp:
        dest, comp = comp.split("=", 1)
    if ";" in comp:
        comp, jump = comp.split(";", 1)
        
    comp_bits = COMP_TABLE[comp]
    dest_bits = DEST_TABLE[dest]
    jump_bits = JUMP_TABLE[jump]
    
    return f"111{comp_bits}{dest_bits}{jump_bits}"


def second_pass(instructions, symbol_table):
    """第二階段：將所有指令翻譯為 16-bit 機器碼"""
    machine_code = []
    next_ram_address = 16  # 自訂變數從 RAM[16] 開始配置
    
    for inst in instructions:
        if inst.startswith("@"):
            binary, next_ram_address = translate_a_instruction(
                inst, symbol_table, next_ram_address
            )
        else:
            binary = translate_c_instruction(inst)
        machine_code.append(binary)
        
    return machine_code


def assemble(input_path):
    with open(input_path, "r", encoding="utf-8") as f:
        raw_lines = f.readlines()
        
    symbol_table = create_symbol_table()
    cleaned = clean_lines(raw_lines)
    instructions = first_pass(cleaned, symbol_table)
    machine_code = second_pass(instructions, symbol_table)
    
    output_path = os.path.splitext(input_path)[0] + ".hack"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(machine_code) + "\n")
        
    print(f"組譯完成：{output_path}（共 {len(machine_code)} 行機器碼）")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python assembler.py Prog.asm")
        sys.exit(1)
    assemble(sys.argv[1])