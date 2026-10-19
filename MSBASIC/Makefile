# Build MS BASIC 6502 targets with ca65/ld65 and check them against the original ROM dumps.
# Run from Git Bash: make [all|verify|test|clean|<target>|run|pet|pet-check]

CC65    ?= /c/8bitProgramming/cc65/bin
CA65    := $(CC65)/ca65
LD65    := $(CC65)/ld65
SIM65   := $(CC65)/sim65
VICE    ?= /c/8bitProgramming/GTK3VICE-3.8-win32
XPET    := $(VICE)/bin/xpet.exe
PYTHON  ?= /c/Users/Admin/AppData/Local/Programs/Python/Python313/python.exe
SRC     := src
BUILD   := build
ORIG    := ref/msbasic/orig

# Targets with an original ROM dump in $(ORIG)
VERIFY_TARGETS := cbmbasic1 cbmbasic2
TARGETS := $(VERIFY_TARGETS) sim

SOURCES := $(wildcard $(SRC)/*.s)

all: $(TARGETS)

$(TARGETS): %: $(BUILD)/%.bin

$(BUILD)/%.bin: $(SOURCES) $(SRC)/%.cfg | $(BUILD)
	$(CA65) -D $* $(SRC)/msbasic.s -o $(BUILD)/$*.o -l $(BUILD)/$*.lst
	$(LD65) -C $(SRC)/$*.cfg $(BUILD)/$*.o -o $@ -Ln $(BUILD)/$*.lbl

$(BUILD):
	mkdir -p $(BUILD)

# Print only mismatches; exit non-zero if any target differs from its ROM dump.
verify: $(addprefix $(BUILD)/,$(addsuffix .bin,$(VERIFY_TARGETS)))
	@fail=0; for t in $(VERIFY_TARGETS); do \
	  cmp -s $(BUILD)/$$t.bin $(ORIG)/$$t.bin || { echo "DIFF $$t"; fail=1; }; \
	done; [ $$fail = 0 ] && echo "verify: all $(words $(VERIFY_TARGETS)) targets match"

# Run tests/*.bas in sim65 and diff with tests/*.out; prints only failures.
test: $(BUILD)/sim.bin
	@$(PYTHON) tests/run.py

# Interactive BASIC in sim65 (stdin/stdout). EOF (Ctrl-Z, Enter) exits.
run: $(BUILD)/sim.bin
	$(SIM65) $<

# PET BASIC 2 ROM is the first 8K of the cbmbasic2 build; the rest is the
# start of the editor ROM, which VICE supplies itself.
$(BUILD)/cbmbasic2-pet.bin: $(BUILD)/cbmbasic2.bin
	head -c 8192 $< > $@

# Start xpet (PET 3032) with our BASIC ROM.
pet: $(BUILD)/cbmbasic2-pet.bin
	$(XPET) -default -model 3032 -basic "$$(cygpath -w $<)"

# Headless PET check: type a program, run it, save a screenshot to build/pet.png.
pet-check: $(BUILD)/cbmbasic2-pet.bin
	-$(XPET) -default -model 3032 -basic "$$(cygpath -w $<)" -warp \
	  -keybuf '10 print "hello from ca65";2+2\nrun\n' \
	  -limitcycles 8000000 -exitscreenshot "$$(cygpath -w $(BUILD)/pet.png)" >/dev/null 2>&1
	@echo "pet-check: see $(BUILD)/pet.png"

clean:
	rm -rf $(BUILD)

.PHONY: all verify test clean run pet pet-check $(TARGETS)
