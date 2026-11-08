# Build the MS BASIC 6502 targets with ca65/ld65.
# Run from Git Bash: make [all|test|clean|<target>|run]

CC65    ?= ../tools/cc65/bin
CA65    := $(CC65)/ca65
LD65    := $(CC65)/ld65
SIM65   := $(CC65)/sim65
PYTHON  ?= /c/Users/Admin/AppData/Local/Programs/Python/Python313/python.exe
SRC     := src
BUILD   := build
DOSREPO := ..

TARGETS := sim 6502dos

# A ca65 symbol cannot start with a digit: the 6502dos target is -D DOS6502.
# It takes mem.inc and far.inc from the 6502DOS sources and api.inc from its build.
DEFINE_6502dos   := DOS6502
INCLUDES_6502dos := -I $(DOSREPO)/src/asm -I $(DOSREPO)/build/gen

SOURCES := $(wildcard $(SRC)/*.s)

all: $(TARGETS)

$(TARGETS): %: $(BUILD)/%.bin

$(BUILD)/%.bin: $(SOURCES) $(SRC)/%.cfg | $(BUILD)
	$(CA65) -D $(or $(DEFINE_$*),$*) $(INCLUDES_$*) $(SRC)/msbasic.s -o $(BUILD)/$*.o -l $(BUILD)/$*.lst
	$(LD65) -C $(SRC)/$*.cfg $(BUILD)/$*.o -o $@ -Ln $(BUILD)/$*.lbl

$(BUILD)/6502dos.bin: $(DOSREPO)/build/gen/api.inc $(DOSREPO)/src/asm/mem.inc $(DOSREPO)/src/asm/far.inc

$(DOSREPO)/build/gen/api.inc: $(DOSREPO)/tools/api.py $(DOSREPO)/tools/genapi.py
	$(PYTHON) $(DOSREPO)/tools/genapi.py

$(BUILD):
	mkdir -p $(BUILD)

# Run tests/*.bas in sim65 and diff with tests/*.out; prints only failures.
test: $(BUILD)/sim.bin
	@$(PYTHON) tests/run.py

# Interactive BASIC in sim65 (stdin/stdout). EOF (Ctrl-Z, Enter) exits.
run: $(BUILD)/sim.bin
	$(SIM65) $<

clean:
	rm -rf $(BUILD)

.PHONY: all test clean run $(TARGETS)
