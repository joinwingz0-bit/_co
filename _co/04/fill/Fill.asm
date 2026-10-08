// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/4/Fill.asm

// Runs an infinite loop that listens to the keyboard input. 
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel. When no key is pressed, 
// the screen should be cleared.

//// Replace this comment with your code.
(LOOP)
    // 1. 讀取鍵盤輸入狀態
    @KBD
    D=M
    @BLACK
    D;JNE   // 若 KBD != 0 (有按鍵按下)，跳轉至 BLACK

(WHITE)
    @color
    M=0     // 設定顏色為白色 (全 0)
    @CHECK
    0;JMP

(BLACK)
    @color
    M=-1    // 設定顏色為黑色 (全 1，二補數即 -1)

(CHECK)
    // 2. 初始化螢幕繪製的起始位址
    @SCREEN
    D=A
    @address
    M=D     // address = SCREEN (16384)

(FILL_LOOP)
    // 3. 將顏色寫入當前記憶體位置
    @color
    D=M
    @address
    A=M
    M=D     // RAM[address] = color

    // 移動到下一個字組 (Word)
    @address
    M=M+1

    // 判斷是否填滿整個螢幕記憶體區塊 (SCREEN ~ KBD 之前)
    @address
    D=M
    @KBD    // KBD 位址為 24576 (即 SCREEN + 8192)
    D=D-A
    @FILL_LOOP
    D;JLT   // 若 address < 24576，繼續填色

    // 4. 完成一輪塗色後，重新回主迴圈監聽鍵盤
    @LOOP
    0;JMP
