; UXDOS16 memory map, PLAN section 3, and the I/O registers in use.

; Zero page
RAM_BANK      = $00             ; selects the RAM bank at $A000-$BFFF
ROM_BANK      = $01             ; selects the ROM bank at $C000-$FFFF
r0            = $02             ; r0-r15: the API registers, 2 bytes each
r1            = $04
r2            = $06
r3            = $08
r4            = $0A
r5            = $0C
r6            = $0E
r7            = $10
r8            = $12
r9            = $14
r10           = $16
r11           = $18
r12           = $1A
r13           = $1C
r14           = $1E
r15           = $20
PROGRAM_ZP    = $22             ; $22-$7F: the program
KERNEL_ZP     = $80             ; $80-$FF: the kernel

; RAM
STACK         = $0100
MONITOR_LINE  = $0200           ; the monitor's input line: maximum, length, text
MONITOR_OUT   = $0280           ; the monitor's output line, and its byte list for E and F
GATE_PAGE     = $0300           ; $0300-$030B free, then SYS_A to SYS_P, the gate, the call entries
; Trap: UXCBASIC's SYS loads A, X, Y and P from these four bytes and stores them back.
; The gate and the vectors must not use them.
SYS_A         = $030C
SYS_X         = $030D
SYS_Y         = $030E
SYS_P         = $030F
; The gate code runs at $0310-$033F. GATE_ENTRIES, the first call entry, is in api.inc.
KERNEL_RAM    = $0600           ; $0600-$06F7: kernel variables, segment KERNELRAM
; The request of a block driver's input command. The kernel fills it before each call.
BLK_UNIT      = $06F8           ; the unit
BLK_COUNT     = $06F9           ; the number of sectors, 1 to 255
BLK_BUFFER    = $06FA           ; where the sectors go, 2 bytes
BLK_SECTOR    = $06FC           ; the first sector, 4 bytes, the low byte first
PSP           = $0700           ; the PSP of the running program
PSP_STACK     = $0700           ; the stack pointer exec called the program with
PSP_HEAP      = $0701           ; the RAM bank of the program's string heap
PSP_TOP       = $0702           ; the program's last page, the last one exec saves; >PROGRAM_END
                                ; until the program sets it
PSP_BREAK     = $0703           ; what Ctrl+C does: a BREAK_ mode of api.inc
PSP_HANDLES   = $0718           ; 20 handles, each an SFT entry number, $FF when closed
HANDLES       = 20
COMMAND_TAIL  = $0780           ; a length byte, then the text after the program's name, then CR
TAIL_MAX      = 126             ; the longest command tail
PROGRAM       = $0801           ; $0801-$9EFF: the program
PROGRAM_END   = $9EFF
; exec saves the parent's PSP to PROGRAM_END, then r0 to PROGRAM_ZP_END, to SAVE_BANKS RAM banks
; from bank 1 + SAVE_BANKS * the level. EXEC_LEVELS programs run one inside another.
PROGRAM_ZP_END = $7F
SAVE_BANKS    = 5
EXEC_LEVELS   = 4
BANKED_RAM    = $A000           ; $A000-$BFFF, the bank in RAM_BANK
ROM           = $C000           ; $C000-$FFFF, the bank in ROM_BANK

; A string heap (strings.s): a RAM bank of string blocks. VARBANK is the shared one.
VARBANK       = 1 + SAVE_BANKS * EXEC_LEVELS
HEAP_BUMP     = $A000           ; the address of the next block
HEAP_FLOORS   = $A002           ; a word for each exec depth: the lowest block GC moves
HEAP_SYSTEM   = $A00C           ; VARBANK: the system descriptors, SYSTEM_STRINGS words
SYSTEM_STRINGS = 32
VARBANK_BLOCKS = HEAP_SYSTEM + 2 * SYSTEM_STRINGS
.assert HEAP_FLOORS + 2 * (EXEC_LEVELS + 1) = HEAP_SYSTEM, error, "a floor for each exec depth"

; RAM bank 0
SFT           = $A000           ; the system file table: SFT_COUNT entries of SFT_SIZE bytes
SFT_COUNT     = 8
SFT_SIZE      = 32
SFT_REFS      = 0               ; the number of handles that refer to the entry, 0 when free
SFT_ACCESS    = 1               ; 0 read, 1 write, 2 read and write
SFT_DRIVER    = 2               ; the address of the driver header, 2 bytes
SFT_FLAGS     = 4               ; SFT_DEVICE for a device, SFT_LIB for a file
SFT_CONTEXT   = 5               ; a file: its context in the FAT32 library
SFT_POS       = 6               ; a file: the position, 4 bytes
SFT_FILE_SIZE = 10              ; a file: the size, 4 bytes
SFT_STATE     = 9               ; the bytes from SFT_CONTEXT to the end of SFT_FILE_SIZE
SFT_DEVICE    = $80
SFT_LIB       = $01
FAT32_RAM     = $A100           ; $A100-$A7FF: the FAT32 library's variables, FATRAM in rom.cfg
FAT32_BUFFER  = $A900           ; $A900-$AAFF: the FAT32 library's sector buffer, FATBUFRAM
RENAME_PATH   = $AB00           ; $AB00-$ABFF: api_rename's new path

; Directory entry attributes
ATTR_READ_ONLY = $01
ATTR_HIDDEN   = $02
ATTR_SYSTEM   = $04
ATTR_LABEL    = $08
ATTR_DIR      = $10
ATTR_ARCHIVE  = $20
ATTR_LONG_NAME = $0F

; Directory entry fields
DIR_ATTR      = 11
DIR_CLUSTER_HIGH = 20
DIR_TIME      = 22
DIR_CLUSTER_LOW = 26
DIR_FILE_SIZE = 28
; Trap: x16emu -bas pastes characters into KBD_QUEUE and counts them in KBD_COUNT, the stock
; KERNAL's keyboard queue. It starts once the PC reaches CHRIN, $FFCF.
KBD_QUEUE     = $A800           ; 10 characters, the oldest first
KBD_QUEUE_SIZE = 10
KBD_COUNT     = $A80A

; Driver header, PLAN section 6
DRV_NEXT      = 0               ; the next driver in the chain, $FFFF for the last
DRV_ATTR      = 2               ; DEV_ bits
DRV_ABI       = 3               ; the ABI version, DRV_ABI_VERSION
DRV_COUNT     = 4               ; the number of vectors
DRV_NAME      = 5               ; a character device's name: 8 bytes, padded with spaces
DRV_VECTORS   = 13              ; a vector for each command, 0 when the driver lacks it
DRV_ABI_VERSION = 1
DEV_CHAR      = $80             ; a character device
DEV_IOCTL     = $40
DEV_CLOCK     = $08
DEV_NUL       = $04
DEV_STDOUT    = $02
DEV_STDIN     = $01
; Driver commands: the vector slots
DRV_INIT      = 0
DRV_INPUT     = 4               ; r0 buffer, r1 count; returns r1 bytes read
DRV_INPUT_STATUS = 6            ; a character device: returns A = $FF when input waits, else 0
DRV_OUTPUT    = 8               ; r0 buffer, r1 count; returns r1 bytes written
; A block driver: DRV_ATTR has DEV_CHAR clear, and DRV_NAME holds the number of units. Its
; input and output commands take the BLK_ request and return carry set and A = the error on a
; fault. They may change BLK_COUNT.

; Drives
DRIVES        = 4               ; A: to D:
FIRST_DRIVE   = 2               ; C:, the drive of the first block unit
; The fields of a drive's DPB, in kernel.s
DPB_DRIVER    = 0               ; the block driver header, 2 bytes; 0 when the drive does not exist
DPB_CWD       = 2               ; the current directory's first cluster, 4 bytes; 0 for the root
DPB_SIZE      = 8

; VIA 1
VIA1_PRA      = $9F01           ; bit 0 I2C data, bit 1 I2C clock
VIA1_DDRA     = $9F03

; VERA
VERA_ADDR_L   = $9F20
VERA_ADDR_M   = $9F21
VERA_ADDR_H   = $9F22
VERA_DATA0    = $9F23
VERA_CTRL     = $9F25
VERA_IEN      = $9F26
VERA_ISR      = $9F27
VERA_DC_VIDEO = $9F29           ; DC_ registers: with DCSEL 0 in VERA_CTRL
VERA_DC_HSCALE = $9F2A
VERA_DC_VSCALE = $9F2B
VERA_DC_BORDER = $9F2C
VERA_L1_CONFIG = $9F34
VERA_L1_MAPBASE = $9F35
VERA_L1_TILEBASE = $9F36
VERA_L1_HSCROLL_L = $9F37
VERA_L1_HSCROLL_H = $9F38
VERA_L1_VSCROLL_L = $9F39
VERA_L1_VSCROLL_H = $9F3A
VERA_SPI_DATA = $9F3E
VERA_SPI_CTRL = $9F3F           ; bit 0 selects the SD card, bit 1 the slow clock, bit 7 busy

; VRAM
SCREEN_MAP    = $10000          ; layer 1 text: 64 rows of 128 cells, a character and a color
CHARSET       = $1F000          ; the font: 256 glyphs of 8 bytes
PALETTE       = $1FA00          ; palette entry 0

; I2C
SMC           = $42             ; the I2C address of the SMC
SMC_KEYCODE   = $07             ; SMC register: the next keycode, 0 when none
