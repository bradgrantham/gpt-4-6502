; paste into https://skilldrick.github.io/easy6502/
define index $10
define fizzcounter $11
define buzzcounter $12
define table $00

    ; org $600
    LDA #1
    STA index ; index = 1
    LDA #2
    STA fizzcounter ; fizzcounter = 2
    LDA #4
    STA buzzcounter ; buzzcounter = 4

loop:
    LDX index
    LDA fizzcounter     ; A = fizzcounter; // sets flags
    ORA buzzcounter     ; A |= buzzcounter; // A |= buzzcounter , set flags
    BNE notfizzbuzz     ; if(A != 0) goto notfizzbuzz; // (buzzcounter | fizzcounter) != 0), one or both are != 0
    LDA #$FB            ; A = 0xFB; // sets flags!
    STA table,X         ; printf("fizzbuzz\n");
    JMP finishloop      ; goto finishloop;

notfizzbuzz:
    LDA fizzcounter     ; A = fizzcounter; // set flags
    BNE notfizz         ; if((A != 0) goto notfizz; // fizzcounter is != 0
    LDA #$F0            ; A = 0xF0; // sets flags!
    STA table,X         ; printf("fizz\n");
    JMP finishloop      ; goto finishloop;

notfizz:
    LDA buzzcounter     ; A = buzzcounter; // set flags
    BNE neither         ; if(A != ) goto neither;
    LDA #$B0            ; A = 0xB0
    STA table,X         ; printf("buzz\n");
    JMP finishloop      ; goto finishloop;

neither:
    LDA index           ; A = index;
    STA table,X         ; printf("%d\n", index);

finishloop:
    DEC fizzcounter     ; fizzcounter--;
    BPL dobuzzcounter   ; if(fizzcounter >= 0) goto dobuzzcounter;
    LDA #2              ; A = 0x02;
    STA fizzcounter     ; fizzcounter = A;

dobuzzcounter:
    DEC buzzcounter     ; buzzcounter--;
    BPL doindex         ; if(buzzcounter >= 0) goto doindex;
    LDA #4              ; A = 0x04;
    STA buzzcounter     ; buzzcounter = A;

doindex:
    INC index           ; index++;
    LDA #$10            ; A = 0x10;
    AND index           ; A &= index;
    BEQ loop            ; if(A == 0) goto loop;

    BRK                 ; stop.
