; The clock: the calls getdate, setdate, gettime and settime on the MCP7940N RTC, I2C device
; $6F. Its time and date registers hold BCD. Its year register holds the year less 2000, so the
; calls take the years 2000 to 2099.

.setcpu "65C02"

.include "mem.inc"
.include "api.inc"

.export api_getdate, api_setdate, api_gettime, api_settime
.import i2c_read_byte, i2c_write_byte

RTC           = $6F
RTC_SECONDS   = 0               ; bit 7, ST, runs the oscillator
RTC_MINUTES   = 1
RTC_HOURS     = 2               ; bit 6 clear: 24 hours
RTC_WEEKDAY   = 3               ; 1 to 7; bit 3, VBATEN, keeps the clock running on the battery
RTC_DAY       = 4
RTC_MONTH     = 5               ; bit 5, LPYR, is read only
RTC_YEAR      = 6
RTC_ST        = $80
RTC_VBATEN    = $08

.segment "KERNELRAM"

clock_value:  .res 1            ; rtc_get: the BCD; clock_weekday: the year, then the day
clock_twice:  .res 1            ; rtc_get: the tens times 2
clock_year:   .res 1            ; api_setdate: the year less 2000

.segment "CODE"

api_gettime:
        ldy #RTC_SECONDS
        jsr rtc_triple          ; A seconds, Y minutes, X hours
        clc
        rts

api_getdate:
        ldy #RTC_DAY
        jsr rtc_triple          ; A day, Y month, X year less 2000
        stx r0
        phy
        plx                     ; the month
        tay                     ; the day
        lda r0
        jsr clock_weekday
        pha
        lda r0
        clc
        adc #<2000
        sta r0
        lda #>2000
        adc #0                  ; carry clear after it
        sta r0+1
        pla
        rts

; api_settime writes the seconds as 0 first, so no minute carries in while the minutes and the
; hours are written.
api_settime:
        cmp #60
        bcs bad_data
        cpy #60
        bcs bad_data
        cpx #24
        bcs bad_data
        pha                     ; the seconds
        phx                     ; the hours
        phy                     ; the minutes
        lda #0
        ldy #RTC_SECONDS
        jsr rtc_put
        pla
        ldy #RTC_MINUTES
        jsr rtc_put
        pla
        ldy #RTC_HOURS
        jsr rtc_put
        pla
        ldy #RTC_SECONDS
        bra rtc_last

bad_data:
        lda #ERR_BAD_DATA
        sec
        rts

; api_setdate also writes the weekday, with VBATEN set.
api_setdate:
        sec
        lda r0
        sbc #<2000
        sta clock_year
        lda r0+1
        sbc #>2000
        bne bad_data            ; before 2000, or past 2255
        lda clock_year
        cmp #100
        bcs bad_data
        txa
        beq bad_data
        cpx #13
        bcs bad_data
        tya
        beq bad_data
        cmp month_ends - 1,x
        bcc @valid
        cmp #29                 ; past the end of its month, only February 29 can be valid
        bne bad_data
        lda clock_year
        and #3
        bne bad_data            ; not a leap year
@valid:
        lda clock_year
        jsr clock_weekday
        inc                     ; the RTC counts the weekday from 1
        ora #RTC_VBATEN
        phx                     ; the month
        phy                     ; the day
        ldx #RTC
        ldy #RTC_WEEKDAY
        jsr i2c_write_byte
        pla
        ldy #RTC_DAY
        jsr rtc_put
        pla
        ldy #RTC_MONTH
        jsr rtc_put
        lda clock_year
        ldy #RTC_YEAR
rtc_last:
        jsr rtc_put
        clc
        rts

; rtc_triple: reads RTC registers Y, Y + 1 and Y + 2 with rtc_get, then Y again, and starts
; over when Y changed: a minute or a day began between the reads. Returns register Y in A,
; Y + 1 in Y and Y + 2 in X.
rtc_triple:
        jsr rtc_get
        pha
        iny
        jsr rtc_get
        pha
        iny
        jsr rtc_get
        pha
        dey
        dey
        jsr rtc_get
        tsx
        cmp STACK+3,x           ; register Y, first read
        beq @same
        pla
        pla
        pla
        bra rtc_triple
@same:
        plx
        ply
        pla
        rts

; rtc_get: reads RTC register Y, drops its flag bits and gives it from BCD in A. Keeps Y.
; Changes X.
rtc_get:
        phy
        ldx #RTC
        jsr i2c_read_byte
        ply
        and rtc_masks,y
        sta clock_value         ; tens * 16 + ones
        and #$F0
        lsr
        lsr
        lsr                     ; tens * 2, carry clear
        sta clock_twice
        asl
        adc clock_twice         ; tens * 6
        eor #$FF
        sec
        adc clock_value         ; less tens * 6: tens * 10 + ones
        rts

; rtc_put: writes A, 0 to 99, as BCD to RTC register Y. The seconds get ST set. Changes A, X
; and Y.
rtc_put:
        tax
        lda #0
        sed
        inx
@count:
        dex
        beq @done
        clc
        adc #1
        bra @count
@done:
        cld
        cpy #RTC_SECONDS
        bne @write
        ora #RTC_ST
@write:
        ldx #RTC
        jmp i2c_write_byte

; clock_weekday: the day of the week, 0 Sunday, of day Y of month X of the year 2000 + A. Keeps
; X and Y. Sakamoto's method, with y the year less 1972, less 1 more in January and February:
; in 2000 to 2099 the century terms cancel, and the weekdays repeat every 28 years.
clock_weekday:
        cpx #3
        adc #27                 ; carry set from March on: plus 28
        sta clock_value
        lsr
        lsr
        clc
        adc clock_value         ; y + y / 4
        adc month_codes - 1,x
        sty clock_value
        adc clock_value
        sec
@mod:
        sbc #7
        bcs @mod
        adc #7                  ; carry clear
        rts

.segment "RODATA"

rtc_masks:
        .byte $7F, $7F, $3F, $07, $3F, $1F, $FF
month_codes:
        .byte 0, 3, 2, 5, 0, 3, 5, 1, 4, 6, 2, 4
month_ends:                     ; the last day + 1, February 28
        .byte 32, 29, 32, 31, 32, 31, 32, 32, 31, 32, 31, 32
