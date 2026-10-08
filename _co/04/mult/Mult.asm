// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/4/Mult.asm

// Multiplies R0 and R1 and stores the result in R2.
// (R0, R1, R2 refer to RAM[0], RAM[1], and RAM[2], respectively.)
// The algorithm is based on repetitive addition.

//// Replace this comment with your code.
// 1. 初始化結果 R2 為 0
    @R2
    M=0

// 2. 將 R1 的值複製到計數器 i 中
    @R1
    D=M
    @i
    M=D

(LOOP)
// 3. 檢查計數器 i 是否小於等於 0
    @i
    D=M
    @END
    D;JLE    // 若 i <= 0，跳轉至 END

// 4. 將 R0 加到累加器 R2
    @R0
    D=M
    @R2
    M=M+D    // R2 = R2 + R0

// 5. 計數器減 1
    @i
    M=M-1    // i = i - 1

// 6. 重複迴圈
    @LOOP
    0;JMP    // 無條件跳轉回 LOOP

(END)
// 7. 無限迴圈（程式結束標準寫法）
    @END
    0;JMP
