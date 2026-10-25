# GUI Forms V1

GUI Forms is the text-mode user interface library of 6502DOS's own utilities. It is keyboard
driven. A control is laid out automatically with `GUI.AUTO`, or placed at a row and column. It is
not a desktop and not a widget set.

The GUI's code, tables and text run from RAM banks at `$A000`, in pyuxc regions. Low RAM holds
the gates and veneers of the calls across, the theme, and the tables that two regions name.

## Status

- Built: V1, phases 0 to 4; the list steps L1 to L3; `GUI.PICKMENU`.
- Built on it: `HELPED` (`src/utils/helped`), `THEMED` (`src/utils/themed`) and `GUIDEMO`
  (`src/utils/guidemo`), which shows every part in seven demos: Forms, Controls, Memo, Lists,
  Dialogs, Files and Look.
- Not planned: `GUI.GRID`, `GUI.BROWSE`.

## Where it lives

- `lib/GUI.UXI`, namespace `GUI`: the engine, the controls, the menus and the dialogs.
- `lib/PICKFILE.UXI` reopens namespace `GUI` for `PICKFILE` and `PICKMANAGE`. A program without
  it carries no file dialog.
- `lib/VERA.UXI`, namespace `VERA`: the screen cells and the stack of saved screen boxes.
- An included file cannot include another file. A program includes `KEYS.UXI`, `VERA.UXI`, then
  `GUI.UXI`. `PICKFILE.UXI` comes after `DOS.UXI`, `BANK.UXI` and `GUI.UXI`. `GUI.UXI` needs
  neither `CONS.UXI` nor `DOS.UXI`.
- pyuxc drops each `SUB` and `FUNCTION` that nothing reaches. Three pointers keep code out of a
  program that does not use it:
  - `KIND_EDITOR`, one `EDITOR` a control kind, set by the routine that makes a control of that
    kind. A program links the editor of a kind only when it makes a control of that kind.
  - `RUN_MENU`, set to `PULL_MENU` by `MENUBAR`. A program with no `MENUBAR` links no menu code.
  - `PICK_HANDLER`, set to `MANAGE` by `PICKMANAGE`. `PICKFILE` alone links no file manager.
- Every program that makes a control links `INPUT2`, as `SAYGET` names `EDIT_TEXT`.
- The tests are 6502DOS tests in `tests/`: `GUI*.UXB`, with `.IN` files for the keys, run one
  at a time with `tools/tests.py NAME`. `HELPED` and `THEMED` have `.IN` tests too. No test
  covers `GUIDEMO`.
- Drawing goes through the console: `PRINT`, `POS`, `CURSOR ON` and `CURSOR OFF`. The boxes use
  the CP437 line characters. `POS(2)` and `POS(3)` give the screen's rows and columns. `VERA.UXI`
  saves and restores the screen under a list, a menu or a dialog, and writes the status line's
  last cell.

### Regions

| Slot | What runs there |
|---|---|
| 0, low RAM | `PRINT_RECORD`; `PICKFILE.UXI`'s `SORTS_BEFORE` and `COPY_RECORD`. Each selects another RAM bank. |
| 1 | `INPUT2`, the themes, `BOX`, `HLINE`, `VLINE`, the form engine, `SHOW`, `REFUSE`, `STATUS_LINE`, every control's constructor, `PICK_CHOICE`, `PUSH_BUTTON`, `HOT_BUTTON`, and the editors `EDIT_TEXT`, `EDIT_CBO`, `EDIT_MEMO`, `EDIT_LIST` |
| 2 | `PRINT_HOT`, `ALT_LETTER`, `DRAW_SHADOW`, a CBO's list (`DROP_LIST`, `PRINT_ITEM`), the menus, `PICKMENU`, the dialogs |
| 3 | `VERA.UXI`, the lists (`LIST`, `LIST_EDIT`, `MARKED`), `PICKFILE.UXI`'s dialog |
| 4 | The memo (`MEMO_EDIT`, `MEMO_CLEAR`, `MEMO_LOAD`, `MEMO_SAVE`) and its text at `$B800` |

A program takes one RAM bank for each region it uses. `PICKFILE` takes one more while it is open.

## Compiler and kernel features it uses

| Feature | Use |
|---|---|
| `#REGION_SLOT n`, n 0 to 63 | the GUI's code in RAM banks (D0) |
| Default parameter values, `name AS type = constant` | `MASK$` and `FLAGS` left out of a call |
| `T$ AS CONST` | a literal caption passed by its own address, not copied |
| `StringAt(a)` | `SHOW` passes a field's kept addresses to `INPUT2` |
| `DECLARE`, `@SUB`, `CALL p WITH (...)` | `KIND_EDITOR`, `RUN_MENU`, `PICK_HANDLER` |
| `CURSOR ON`, `CURSOR OFF` | a field and the memo show the cursor; the other controls hide it |
| API call 51 `bank_call`, `$03D9` | every call across a region's edge |
| API call 52 `exec_rest`, `$03DC` | the start reads a region's image past `$9EFF` from the file |
| `lib/BANK.UXI` | `PICKFILE` takes and frees its RAM bank with `BANK.ALLOC` and `BANK.FREE` |

`BANK.UXI`'s routines are `ALLOC`, `FREE`, `FREE_COUNT`, `USE`, `CURRENT`, `GET_BYTE`, `PUT_BYTE`
and `FAR_CALL`.

## Decisions

**D0. Code in RAM banks.**
- `#REGION_SLOT n` puts the `SUB`s and `FUNCTION`s that follow it in region n, until the next
  `#REGION_SLOT`. Slot 0 is low RAM. An included file starts in its includer's slot, and the
  includer's slot holds again after it.
- Each slot used is a region with a RAM bank of its own, taken at the start. The region's code
  runs at `$A000`. A region holds at most 8192 bytes; past that the compile stops with
  `REGION n FULL`.
- A call across a region's edge goes through a 7-byte veneer in low RAM (`T_FARCALL`), the
  region's 9-byte gate (`T_RGGATE`), and `bank_call`. It keeps the caller's bank: the caller may
  leave any bank selected. It costs about 145 cycles more than a `JSR`.
- A literal, a global variable or a runtime record that only one region's code names moves into
  that region. What low code or two regions name stays in low RAM.
- Region code may not write `$00`. A `GOTO` or an `ON` across a region's edge stops the compile.
  A run-time error in a region prints the bank with the address, as `$06:A018`.
- The images of the regions follow the low part in the program file. At the start `R_RGLOAD`
  copies each into its bank, and reads the part past `$9EFF` with `exec_rest`. A program file may
  pass `$9EFF`.

**D1. Optional arguments.** Default parameter values in pyuxc. A call may leave out the trailing
arguments that have defaults, and compiles to the same bytes as a call that writes them.

**D2. Validation.** An event in place of a callback. A control made with `GUI.VALIDATE` in its
`FLAGS` ends `SHOW` when the user leaves it: `SHOW` returns `EV_LEAVE`, with the control in
`GUI.LEFT_FIELD` and the key in `GUI.LEFT_KEY`. `GUI.REFUSE(MESSAGE$)` puts the focus back on
the control at the next `SHOW`.

**D3. The types a field edits.** Strings only. `INPUT2` edits a `STRING`, and the most characters
come from the string's size. `CHECK`, `RADIO`, `CBO` and `LIST` take a `UBYTE` by its address,
`@NAME`.

**D4. Captions and choices.** The form keeps the address of each caption, title, target, mask
and set of choices, not a copy. Each must stay put until the form is freed. The choices of a
`RADIO`, a `CBO` and `PICKMENU` are one string with `|` between them, `"Red|Green|Blue"`, at most
255 characters. A `LIST`'s items are records in a RAM bank or in low RAM.

**D5. Names.** `GUI.ONE_COL` 0 and `GUI.TWO_COL` 2. `GUI.CENTER` 255 is a position only; there
are no alignment flags, and captions are left-aligned. `GUI.AUTO` 254. The themes are
`ENUM THEMES` (`DARK`, `LIGHT`, `GRAY`), and a theme file has its own routine, `THEME_FILE`.
`GUI.FRAMED` 1 is the form flag that draws a box; `GUI.BOX` is the drawing `SUB`.

**D6. Themes.** A theme is 13 bytes, one color a role, background * 16 + foreground, in `ENUM
ROLE`'s order: `PAGE`, `FRAME`, `TITLE`, `TEXT`, `FIELD`, `FIELD_FOCUS`, `BUTTON`,
`BUTTON_FOCUS`, `HOT_KEY`, `DISABLED`, `MENU`, `MENU_SELECTED`, `STATUS`.
- The current theme is `GUI.COLORS$`, a `STRING * 13` in low RAM, as regions 1 and 2 both read
  it. It is empty until the first `THEME`, `THEME_FILE` or `USE_COLOR`; `USE_COLOR` loads `DARK`
  then.
- The built-in themes are the string `CONST`s `DARK_COLORS$`, `LIGHT_COLORS$` and
  `GRAY_COLORS$`. As background, foreground:

  ```
  DARK  0,0 0,12 0,2 0,15 15,0 1,0 12,0 1,0 0,2 0,12 11,1 12,0 11,1
  LIGHT 1,1 1,11 1,6 1,0 15,0 12,1 6,12 6,1 1,14 1,12 15,0 6,1 6,1
  GRAY  11,0 14,0 14,0 14,1 15,0 1,0 11,1 1,0 0,2 14,12 12,1 14,1 12,0
  ```

- A theme file holds up to 13 bytes in that order. `THEMED` writes one, and gives a name with no
  extension the extension `.GTH`. A role past the file's end takes `DARK`'s color, and so does every role when the file does not
  open.
- Each theme's `PAGE` color has the same foreground as background, so a box drawn in `PAGE`
  clears its cells.

**D7. What sits under a list, a menu or a dialog.** It saves the screen under it with
`VERA.SAVE_RECT` before it draws, and puts it back with `VERA.RESTORE_RECT` when it closes. The
saved boxes are a stack in VRAM `$00000` to `$0FFFF`. A dialog saves its form and its shadow:
the form's width + 2 by its height + 1. When `SAVE_RECT` returns 0, the stack being full, the
box is cleared in the `PAGE` color on close, `SHOWN_FORM` is set to 0, and the next `SHOW` draws
the form whole.

**D8. Limits.**

| Table | Most | Where |
|---|---|---|
| Panels: forms and sections together | 12 (`MOST_PANELS`) | region 1; `PANEL_ROW`, `_COLUMN`, `_WIDTH`, `_HEIGHT` in low RAM, as region 2 names them |
| Controls | 48 (`MOST_CONTROLS`) | region 1 |
| Lists | 4 (`MOST_LISTS`) | region 3 |
| Menus, items | 8 (`MOST_MENUS`), 40 (`MOST_ITEMS`) | region 2 |
| Memo text | one text, 2047 bytes (`MEMO_SIZE`) | region 4's bank at `$B800` |
| `LIST_MULTI` marks | one list's, 32 bytes | region 3 |
| Dialogs open | one between `PUT_DIALOG` and `SHUT_DIALOG` | region 2 |

- The tables are parallel arrays, one element more than the most; element 0 is unused.
- A form's handle is its panel. `CREATEFORM` takes panels from 12 down. A form and its sections
  are freed together by `FREE`.

**D9. Which code goes in which bank.** As the table under "Regions". `EDIT_FIELD` calls a
control's editor through `KIND_EDITOR`, so `SHOW` links only the editors of the kinds a program
makes. The editors `EDIT_CBO`, `EDIT_MEMO` and `EDIT_LIST` read the control tables in region 1
and pass what they read to the code in regions 2, 3 and 4 as parameters.

**D10. The memo.** A flat buffer of 2047 bytes at `MEMO_TEXT`, `$B800`, in region 4's bank past
the region's code and data. One memo text a program. A line ends in LF. `MEMO_LOAD` drops each
CR.
- Trap: region 4's code and data must end below `$B800`: 6144 bytes. The compile's `REGION 4`
  line gives their size.
- Trap: a kernel `read` that fills `$BFFF` returns with the next RAM bank selected. The text ends
  at `$BFFE`.

## Steps

All are done. Each step names its tests in `tests/`, or in `UXCBASIC/tests/` where marked.

### Phase 0: compiler and kernel

- **0a.** Default parameter values. `UXCBASIC/tests`: `SUBDEF`, `ERRDEFORDER`, `ERRDEFFEW`,
  `ERRDEFCONST`.
- **0b.** The traps of code in a bank: each kernel call gives back the caller's RAM bank, and a
  child run by `exec` starts with it. Tests `BANKTRAP`, `BANKEXEC`.
- **0c.** `bank_call`, API call 51. Test `BANKCALL`.
- **0d.** `lib/BANK.UXI`. Test `BANKLIB`.
- **0e to 0g.** `#REGION_SLOT n`, data and runtime records moved into a region, `STRING`
  arguments passed out of a region kept in low RAM. Tests `RGCALL`, `RGERR`, `RGDATA`, `RGMULTI`,
  `RGPASS`, `RGRUN`.

### Phase 1: INPUT2

```
FUNCTION INPUT2(ROW AS UBYTE, COLUMN AS UBYTE, TARGET$, WIDTH AS UBYTE,
                MASK$ AS CONST = "", FLAGS AS UBYTE = 0) AS UWORD
```

Edits `TARGET$` in a field at `ROW` and `COLUMN`, counted from 0, `WIDTH` characters wide.
Region 1. Tests `GUIEDIT`, `GUIFLAGS`, `GUIMASK`.

- **1a. Editing.** Left, Right, Home, End, Backspace, Delete, and Insert, which switches insert
  and overwrite in `GUI.OVERWRITE_MODE`, kept from one call to the next. The text scrolls inside
  the field. `TARGET$` takes at most its own size in characters. Enter, Tab, Esc and every other
  extended key end the edit, and `INPUT2` returns that key as `WAITKEY()` gives it; `KEYMODS()`
  tells Shift+Tab from Tab. Esc puts back the text the field started with.
- **1b. Flags.** `PASSWORD` 1 shows `*`. `READ_ONLY` 2: the cursor moves and the field ends, but
  the text does not change. `UPPER` 4, `LOWER` 8, and `PROPER` 16, upper case at the start or
  after a space and lower case elsewhere, act on typed letters. `VALIDATE` 32 is `SHOW`'s.
  `DRAW_ONLY` 64 draws the field from its first character and returns `DRAW_ONLY`, with no key
  read.
- **1c. Masks.** `#` a digit, `A` a letter, `X` any character. The mask fixes the field's length,
  at most `TARGET$`'s size; `TARGET$` is cut or padded to it, with the mask's other characters
  and a space where the mask takes one. The cursor skips the mask's other characters. A masked
  field types over, and Delete and Backspace put a space. `"(###)-###-####"` is a phone number.
- Trap: a field that ends in the screen's last column moves the cursor to the next line.

### Phase 2: the form engine

- **2a. Themes** (D6). `GUI.THEME(KIND AS ENUM.THEMES)`, `GUI.THEME_FILE(FILE_NAME$)`,
  `GUI.USE_COLOR(WHICH AS ENUM.ROLE)`, which sets the console color for what is printed next.
  Test `GUITHEME`.
- **2b. Drawing.** `GUI.BOX(ROW, COLUMN, WIDTH, HEIGHT, STYLE = SINGLE)`,
  `GUI.HLINE(ROW, COLUMN, LENGTH, STYLE = SINGLE)`, `GUI.VLINE(ROW, COLUMN, LENGTH, STYLE =
  SINGLE)`. `ENUM LINES` is `SINGLE` and `DOUBLE`. All take the current console color. `BOX`
  clears its inside. `WIDTH`, `HEIGHT` and `HLINE`'s `LENGTH` are at least 2. Trap: a box that
  ends in the screen's last column moves the cursor to the next line, and on the last row that
  scrolls the screen. Test `GUIBOX`.
- **2c. Forms.**

  ```
  FUNCTION CREATEFORM(TITLE$ AS CONST, ROW AS UBYTE, COLUMN AS UBYTE, WIDTH AS UBYTE,
                      HEIGHT AS UBYTE, FLAGS AS UBYTE = 0) AS UBYTE
  ```

  Returns a handle, or 0 when 12 panels are in use. `CENTER` as `ROW` or `COLUMN` centers the
  form on the screen. `FLAGS`: `FRAMED` 1 draws a box of double lines; `NO_SHADOW` 4 (4c).
  `WIDTH` is at least 6 and `HEIGHT` at least 2. A section still open is ended first, and the
  controls made from then on go in the new form.
  - `GUI.FREE(HANDLE)` frees the form, its sections and its controls. `FREE(0)` does nothing.
  - `GUI.DRAW_FORM(HANDLE)` draws the shadow, then the form, then each section. A `FRAMED` panel
    is a box in the `FRAME` color, else its area is cleared in `PAGE`. The title is centered on
    the panel's top row between spaces, in the `TITLE` color, cut to the panel's width - 4. An
    empty title draws nothing.
  - The form code runs under `ERRORS OFF`: a handle is one `CREATEFORM` returned, or 0.
  - Test `GUIFORM`.
- **2d. Sections and automatic layout.** `GUI.STARTSECTION(HANDLE, TITLE$ AS CONST, FLAGS = 0)`
  and `GUI.ENDSECTION()`. Test `GUISECT`.
  - A section opens on the form's next automatic line, 1 column in from each side of the form.
    Its top row is the title row, with or without a frame or a title. A section still open is
    ended first. With 12 panels in use no section opens, and the controls go on the form's
    lines.
  - `ENDSECTION` runs the section's height to the form's next automatic line, + 1 when `FRAMED`,
    + 1 after a half-used `TWO_COL` line.
  - `GUI.PLACE(ROW, COLUMN, CAPTION_LENGTH)` lays out each control and sets `PLACED_ROW`,
    `PLACED_COLUMN` and `PLACED_SECTION`. `ROW` and `COLUMN` count from the form's top left
    corner. `AUTO` as `ROW` takes the form's next automatic line. `AUTO` as `COLUMN` takes the
    column 3 in from the form's edge, or in a `TWO_COL` section that column and the form's
    middle (`WIDTH / 2`) in turn. Only a control with an `AUTO` column joins the open section,
    and its caption counts toward the section's longest.
- **2e. GUI.SHOW.** `FUNCTION SHOW(HANDLE AS UBYTE) AS UBYTE`. Test `GUISHOW`.
  - A form new to `SHOW` is drawn whole with `GUI.DRAW_WHOLE(HANDLE)`: the form, its menu bar,
    and each control's caption and field. The focus goes to its first control. A form is new
    after `EV_DONE`, `EV_CANCEL` or `FREE`, and when another form was shown last.
  - Tab, Down and Enter move the focus to the next control; Shift+Tab and Up to the one before.
    The focus wraps, and skips each `SAY`.
  - Events: `EV_DONE` 253 for Enter on the last control, or a form with no control but `SAY`s;
    `EV_LEAVE` 254 (D2); `EV_CANCEL` 255 for Esc; a button's id or a menu item's id, 1 to 252.
    `SHOW(0)` returns `EV_CANCEL`.
  - A key a `VALIDATE` control passes on that `SHOW` does not know, such as F2, returns
    `EV_LEAVE` too, and the next `SHOW` keeps the focus on the control.
  - `GUI.REFUSE(MESSAGE$ AS CONST)` shows the message on the status line until the user leaves
    the control. `GUI.STATUS_LINE(MESSAGE$ AS CONST)` prints a message on the screen's last row
    in the `STATUS` color.
  - `GUI.EDIT_FIELD(CONTROL, DRAW_ONLY)` draws one control again. A memo or a list on the screen
    shows new contents only when it next takes the focus, or after this call.

### Phase 3: controls

Each constructor returns the control's number, or 0 when 48 controls are in use. A form's
controls take the focus in the order they were made. `ROW` and `COLUMN` place the control as
`PLACE` does.

- **3a. Fields and captions.** Test `GUISAY`.

  ```
  FUNCTION SAYGET(ROW AS UBYTE, COLUMN AS UBYTE, CAPTION$ AS CONST, TARGET$,
                  WIDTH AS UBYTE, MASK$ AS CONST = "", FLAGS AS UBYTE = 0) AS UBYTE
  FUNCTION GET(ROW AS UBYTE, COLUMN AS UBYTE, TARGET$, WIDTH AS UBYTE,
               MASK$ AS CONST = "", FLAGS AS UBYTE = 0) AS UBYTE
  FUNCTION SAY(ROW AS UBYTE, COLUMN AS UBYTE, CAPTION$ AS CONST) AS UBYTE
  ```

  - `GET` is `SAYGET` with the caption `""`. `SAY` is `SAYGET` with `WIDTH` 0, a control that
    takes no focus. `WIDTH` is required. `MASK$` and `FLAGS` are `INPUT2`'s.
  - The field starts one space after the caption. In a section, with `AUTO` as `COLUMN`, it
    starts one space after the section's longest caption, so a `GET` lines up with the
    `SAYGET`s. A field with no caption has no space. A `SAY`'s caption does not count toward the
    longest.
  - Captions are drawn in the `TEXT` color. A field takes `FIELD`, and `FIELD_FOCUS` while it
    has the focus.
- **3b. Check boxes and radio buttons.** Test `GUICHECK`.

  ```
  FUNCTION CHECK(ROW AS UBYTE, COLUMN AS UBYTE, CAPTION$ AS CONST, VALUE_AT AS UWORD,
                 FLAGS AS UBYTE = 0) AS UBYTE
  FUNCTION RADIO(ROW AS UBYTE, COLUMN AS UBYTE, CAPTION$ AS CONST, CHOICES$ AS CONST,
                 VALUE_AT AS UWORD, FLAGS AS UBYTE = 0) AS UBYTE
  ```

  - `CHECK` draws `[X] Caption` or `[ ] Caption`; the `UBYTE` at `VALUE_AT` is 1 or 0. Its box
    lines up with a section's fields.
  - `RADIO` is one control for a whole set. `"Red|Green|Blue"` draws
    `(*) Red ( ) Green ( ) Blue`; the `UBYTE` is the chosen one, 0 for the first. The choices
    start where `SAYGET`'s field would.
  - Space and Right choose the next choice, wrapping, and Left the one before. Space, Left and
    Right toggle a `CHECK`. Esc does not put back a choice. The cursor sits on the chosen mark.
    The whole control takes the field's color. `FLAGS` may be `VALIDATE`.
- **3c. Buttons.** `FUNCTION BUTTON(ROW AS UBYTE, COLUMN AS UBYTE, CAPTION$ AS CONST, ID AS
  UBYTE) AS UBYTE`. Test `GUIBTN`.
  - `"&Save"` draws `< Save >`. The `&` is not drawn; the letter after it takes the button's
    background and `HOT_KEY`'s foreground. The button is in `BUTTON_FOCUS` with the focus, else
    `BUTTON`.
  - Enter on the button, or Alt with its hot letter from any control of the form, makes `SHOW`
    return `ID`. A hot key is a letter. A hot key pressed in a `VALIDATE` field presses the
    button with no `EV_LEAVE`. Space does not press a button.
  - The next `SHOW` keeps the form drawn and the focus on the button.
  - A button's hot key wins over a menu's.
- **3d. Combo box.** Test `GUICBO`.

  ```
  FUNCTION CBO(ROW AS UBYTE, COLUMN AS UBYTE, CAPTION$ AS CONST, CHOICES$ AS CONST,
               VALUE_AT AS UWORD, WIDTH AS UBYTE, FLAGS AS UBYTE = 0) AS UBYTE
  ```

  - The field is the chosen choice, `WIDTH - 1` columns, then a down arrow, CP437 31. The
    `UBYTE` at `VALUE_AT` is the choice, 0 for the first.
  - Space or Enter opens the list: a box in the `MENU` color under the field, the choice in
    `MENU_SELECTED`. Up and Down move through it, wrapping; Enter chooses; Esc leaves the choice
    as it was. The screen under the list is put back (D7), and the focus stays on the `CBO`.
  - Trap: the list takes the rows from `ROW + 1` to `ROW + 2` + the number of choices, and the
    columns from `COLUMN - 1` to `COLUMN + WIDTH`. It drops below the field only, and does not
    scroll.
  - Split: the constructor and `EDIT_CBO` are in region 1, `DROP_LIST` in region 2.
- **3e. Memo** (D10). Test `GUIMEMO`.

  ```
  FUNCTION MEMO(ROW AS UBYTE, COLUMN AS UBYTE, CAPTION$ AS CONST, WIDTH AS UBYTE,
                HEIGHT AS UBYTE, FLAGS AS UBYTE = 0) AS UBYTE
  SUB MEMO_CLEAR()
  FUNCTION MEMO_LOAD(FILE_NAME$ AS CONST) AS UBYTE
  FUNCTION MEMO_SAVE(FILE_NAME$ AS CONST) AS UBYTE
  ```

  - A field of lines `WIDTH` by `HEIGHT`, the caption before its first row. With `AUTO` as
    `ROW`, the form's next automatic line is below the memo.
  - Keys: a character or Enter inserts; Backspace and Delete delete; Left and Right move, across
    a line's end; Up and Down keep the column, cut to the line; Home and End; PgUp and PgDn move
    `HEIGHT` lines. Any other key, such as Tab, Shift+Tab or Esc, goes back to `SHOW`. Esc does
    not put the text back. A full memo takes no more.
  - The whole memo is drawn at each key, scrolled down and across to show the cursor. A
    character below 32 shows as a space.
  - `MEMO_LOAD` returns 0; `MEMO_MISSING` 1 when the file does not open, the memo then empty; or
    `MEMO_CUT` 2 when the file is longer than 2047 bytes, the memo then the first 2047.
  - `MEMO_SAVE` writes the text, each line ending in LF, and returns 0 or `MEMO_MISSING`.
- **End of phase 3.** `HELPED [name]` edits a text file in a form with every kind of V1
  control. Test `HELPED`.

### Phase 4: menus, dialogs and shadows

- **4a. Menus.** Region 2. Test `GUIMENU`.

  ```
  SUB MENUBAR(HANDLE AS UBYTE)
  SUB BEGINMENU(TITLE$ AS CONST)
  SUB MENUITEM(CAPTION$ AS CONST, ID AS UBYTE)
  SUB ENDMENU()
  ```

  - `MENUBAR` gives the form an empty bar on the screen's top row; `MENUBAR(0)` takes it away.
    The bar is drawn after the form in the `MENU` color, each title from column 2 between
    spaces. `&` marks a hot letter. An item's `ID` is 1 to 252.
  - F10 opens the first menu, and Alt with a title's hot letter its menu. The title takes
    `MENU_SELECTED`, and the items drop down under it in a box 3 columns wider than the longest
    caption, & counted, kept off the screen's last column. Up and Down move, wrapping; Left and
    Right open the menu before or after, wrapping; Enter, or an item's hot letter alone,
    chooses; Esc closes. `SHOW` returns the item's id, and the focus stays.
  - Trap: a menu takes the rows from 1 to 2 + its number of items, and does not scroll. A menu
    needs one item at least.
  - Trap: `FREE` leaves the bar to the handle, and the next form made may take that handle.
- **4b. Dialogs.** Region 2. Tests `GUIDLG`, `GUIINP`.

  ```
  FUNCTION MSGBOX(TITLE$ AS CONST, LINE1$ AS CONST, LINE2$ AS CONST = "",
                  LINE3$ AS CONST = "", BUTTON1$ AS CONST = "&OK",
                  BUTTON2$ AS CONST = "") AS UBYTE
  FUNCTION YESNO(TITLE$ AS CONST, LINE1$ AS CONST, LINE2$ AS CONST = "",
                 LINE3$ AS CONST = "") AS UBYTE
  FUNCTION INPUTBOX(TITLE$ AS CONST, PROMPT$ AS CONST, TARGET$, WIDTH AS UBYTE,
                    MASK$ AS CONST = "", FLAGS AS UBYTE = 0) AS UBYTE
  FUNCTION INPUTBOX2(TITLE$ AS CONST, PROMPT1$ AS CONST, TARGET1$, PROMPT2$ AS CONST,
                     TARGET2$, WIDTH AS UBYTE, MASK$ AS CONST = "",
                     FLAGS AS UBYTE = 0) AS UBYTE
  ```

  - Layout, from `OPEN_DIALOG(TITLE$, ROWS, BUTTON1$, BUTTON2$)`: a framed form centered on the
    screen, `DIALOG_WIDTH` + 6 columns by `ROWS` + 6 rows. `DIALOG_WIDTH` is the widest of the
    lines, the title and the buttons. The lines start at row 2, column 3. The buttons are
    centered on row `ROWS` + 3, 2 columns apart, with ids 1 and 2. A blank row runs above the
    lines and below the buttons, and 2 blank columns each side.
  - `MSGBOX` shows up to 3 lines over 1 or 2 buttons. It returns 1 or 2 for the button pressed,
    or `EV_CANCEL` for Esc.
  - `YESNO` is `MSGBOX` with `&Yes` and `&No`. It returns 1 for Yes, and 0 for No or Esc.
  - `INPUTBOX` puts the prompt on row 2 and the field on row 3, over `&OK` and `&Cancel`. The
    focus starts in the field. It returns 1 for OK or Enter in the field, 2 for Cancel, or
    `EV_CANCEL` for Esc. Esc puts back the text of the field, as `INPUT2` does; otherwise
    `TARGET$` keeps what was typed.
  - `INPUTBOX2` puts each prompt before its field. The prompts are right-aligned, so the fields
    line up. Both fields take `WIDTH`, `MASK$` and `FLAGS`. Enter in the first field moves to
    the second, and Enter in the second is OK.
  - `INPUTBOX` and `INPUTBOX2` make the buttons first and the fields last, so Enter in the last
    field ends the form.
  - A dialog runs as `PUT_DIALOG(FOCUS)`, `SHOW(DIALOG_FORM)`, `SHUT_DIALOG(RESULT)`;
    `RUN_DIALOG(FOCUS)` does all three. `PUT_DIALOG` keeps `NEXT_FOCUS`, `SHOWN_FORM` and the
    screen (D7). `SHUT_DIALOG` frees the form, puts them back, and returns the event with
    `EV_DONE` as 1. A form shown before the dialog keeps its focus and is not drawn again.
  - Trap: one dialog at a time between `PUT_DIALOG` and `SHUT_DIALOG`. A dialog run between them
    overwrites `DIALOG_FORM`, `KEPT_FOCUS`, `KEPT_FORM` and `KEPT_SCREEN`.
- **4c. Shadows.** Every form drops a shadow in black on black: 2 columns down the form's right
  side from its second row, and the row under it from its third column. It is trimmed at the
  screen's right and bottom edges, and leaves out the screen's last cell. `NO_SHADOW` 4 in
  `CREATEFORM`'s `FLAGS` leaves it out. Sections have none. `CENTER` centers the form without
  its shadow. `DRAW_SHADOW` is in region 2. Test `GUISHADOW`.

## After V1

### L1. GUI.LIST

```
FUNCTION LIST(ROW AS UBYTE, COLUMN AS UBYTE, CAPTION$ AS CONST, ITEMS_AT AS UWORD,
              ITEMS_BANK AS UBYTE, ITEM_LENGTH AS UBYTE, COUNT AS UBYTE, VALUE_AT AS UWORD,
              ROWS AS UBYTE, WIDTH AS UBYTE, FLAGS AS UBYTE = 0) AS UBYTE
FUNCTION MARKED(INDEX AS UBYTE) AS UBYTE
```

A control of kind `KIND_LIST` 6, in region 3. Test `GUILIST`.

- The items are `COUNT` records of `ITEM_LENGTH` bytes from `ITEMS_AT`, each a string padded with
  zeros. `ITEMS_BANK` is the RAM bank of records at `$A000` to `$BFFF`, or 0 for low RAM.
  `PRINT_RECORD`, in low RAM, selects that bank to print an item.
- The `UBYTE` at `VALUE_AT` is the item chosen, 1 for the first, or 0 for none.
- The list is `ROWS` rows of `WIDTH` columns. The last column holds `^` on the top row for items
  above and `v` on the bottom row for items below. The list scrolls by the fewest rows that show
  the item chosen. The item chosen takes `MENU_SELECTED`. The cursor is hidden.
- Keys: Up, Down, PgUp and PgDn (`ROWS` items), Home, End. A plain key above Space moves to the
  next item that starts with it, case ignored, wrapping. Any other key goes back to `SHOW`.
- `LIST_MULTI` 128 in `FLAGS`: Space marks and unmarks the item chosen, a `*` in the first
  column shows a mark, and `MARKED(INDEX)` reads item `INDEX`'s mark. The marks are 32 bytes, one
  bit an item. One list at a time has marks; `LIST` with `LIST_MULTI` clears them.
- With `AUTO` as `ROW`, the form's next automatic line is below the list.
- A list takes one of 4 slots, which hold its arguments. A slot is free when its control is no
  longer a list that holds it, so `FREE` frees it. `LIST` returns 0 when the 4 are in use.

### L2. GUI.LISTBOX

```
FUNCTION LISTBOX(TITLE$ AS CONST, ITEMS_AT AS UWORD, ITEMS_BANK AS UBYTE,
                 ITEM_LENGTH AS UBYTE, COUNT AS UBYTE, ROWS AS UBYTE,
                 FLAGS AS UBYTE = 0) AS UBYTE
```

A dialog in region 2, laid out as 4b's. Test `GUILBOX`.

- A `LIST` at row 2, column 3, `ITEM_LENGTH` + 1 columns wide, + 1 more with `LIST_MULTI`, `ROWS`
  rows, over `&OK` and `&Cancel`. The items and `FLAGS` are `LIST`'s. The focus starts in the
  list, on the first item.
- It returns the item chosen for OK or Enter in the list, and 0 for Cancel, Esc, or a `COUNT` of
  0. With `LIST_MULTI`, `MARKED` reads the marks after it returns.
- Trap: with 4 lists in use the dialog has no list, and OK returns 1.

### L3. GUI.PICKFILE and GUI.PICKMANAGE

```
FUNCTION PICKFILE(TITLE$ AS CONST, MASK$ AS CONST, TARGET$) AS UBYTE
FUNCTION PICKMANAGE(TITLE$ AS CONST, MASK$ AS CONST, TARGET$) AS UBYTE
```

In `lib/PICKFILE.UXI`, region 3. Test `GUIPICK`.

- Layout, a dialog 74 columns wide laid out as the Open dialog of MS-DOS's EDIT: the field
  `File name:`, 57 wide, which edits `TARGET$`; the path of the folder shown; the list of files
  at column 3 and the list of folders and drives at column 38, each 33 columns by 10 rows; then
  `&OK` and `&Cancel`. A path past 68 characters shows as its drive, `...` and its last 62
  characters.
- The dialog opens on the current drive and folder, with the field holding `MASK$` and the focus
  in the field. The current drive and folder never change: the dialog reads
  `DOS.CALL_TEXT + "*.*"` and `DOS.CALL_TEXT` + the mask.
- Names: the dialog takes a RAM bank with `BANK.ALLOC` while it is open, and frees it before it
  returns. The names are records of 32 bytes, 255 at most, read with `DOS.FINDFIRST` and
  `DOS.FINDNEXT`. The folders, `..` among them and `.` left out, are sorted with case ignored,
  then come the drives, `[-A-]` for A:, then the files, sorted. A drive is listed when
  `DOS.GETCWD` knows it, A: to H:.
- OK and Enter in the field take what the field holds:
  - An empty field gets `MASK$` back.
  - A mask, a name with `*` or `?` and no `\` or `:`: Enter reads the names again with it; OK
    takes the file chosen in the list.
  - Else the text is a path from the folder shown: from the drive's root after a first `\`, from
    drive X:'s current folder after `X:`, and from its root after `X:\`. Empty names and `.` go,
    and `..` takes the name before it. Then the last name decides: a mask becomes the mask and
    its folder is shown; a folder is shown, the field back to `MASK$`; else it is a file, and
    `PICKFILE` returns 1 with `TARGET$` its full path.
- Enter in the list of files returns 1 with `TARGET$` the full path of the file chosen. Enter in
  the list of folders opens the folder; `..` opens the folder above, and a drive its current
  folder.
- It returns 0 for Cancel, for Esc, with no file chosen, or when no RAM bank is free. It changes
  `DOS.CALL_TEXT` and the `DOS.FOUND_` variables.
- `PICKMANAGE` is `PICKFILE` with the keys of a file manager. It sets `PICK_HANDLER` to `MANAGE`,
  calls `PICKFILE`, and sets it back to 0.
  - Del in a list deletes the file or folder after a `YESNO`, with `DOS.DELETE` or `DOS.RMDIR`.
  - F2 in a list renames the item, with `DOS.RENAME`, to a name asked with an `INPUTBOX`.
  - F5 in the list of files copies the file, with `DOS.COPY`, to a name asked with an
    `INPUTBOX`. A copy onto the same path is refused with `DOS.ERR_ACCESS`.
  - F7 in a list or the field makes a folder, with `DOS.MKDIR`, named in an `INPUTBOX`.
  - A name asked is up to 32 characters: a name or path from the folder shown, or a path with a
    drive. `..` is not deleted or renamed. Del, F2 and F5 do nothing on a drive.
  - After a key that calls DOS the names are read again, and the focus goes back to the control
    it left. A DOS error shows on the status line, by `REFUSE`.
- The field and both lists take `VALIDATE`. `PICKFILE` runs its own `SHOW` loop: after
  `EV_LEAVE` it shows the form again, unless the key was Enter or `PICK_HANDLER`'s key called
  DOS. `LEFT_KEY`'s high byte, the scan code, goes to `PICK_HANDLER`.
- Trap: `DOS.COPY` takes `DOS.CALL_TEXT` as its buffer, so `MOVE_FILE` keeps the path's 256
  bytes at `$A000` in the names' bank, over the records, for the copy.
- Trap: the dialogs `MANAGE` runs overwrite what `PUT_DIALOG` kept for `PICKFILE`, so `MANAGE`
  keeps and puts back `DIALOG_FORM`, `KEPT_FOCUS`, `KEPT_FORM` and `KEPT_SCREEN`.

### GUI.PICKMENU

```
FUNCTION PICKMENU(ROW AS UBYTE, COLUMN AS UBYTE, TITLE$ AS CONST, CHOICES$ AS CONST,
                  START AS UBYTE = 1) AS UBYTE
```

A box that closes itself, as a `CBO`'s list does. Region 2; only a program that calls it links
it. Test `GUIPMENU`.

- The box is in the `MENU` color at `ROW` and `COLUMN`, with `TITLE$` centered in its top edge.
  It holds the choices of `CHOICES$`, separated by `|`. `&` marks a hot letter.
- The box is 3 columns wider than the longest choice, & counted, or `TITLE$` + 4 when that is
  wider. It stays off the screen's last column.
- `START` is the choice selected first, in `MENU_SELECTED`. Up and Down move, wrapping. Enter, or
  a choice's hot letter, chooses. It returns the choice's number, from 1, or 0 for Esc.
- The screen under the box is put back (D7).
- Trap: the box takes the rows from `ROW` to `ROW + 1` + the number of choices, and does not
  scroll.
- `PRINT_HOT(CAPTION_AT, WHICH, NUMBER = 1)` prints item `NUMBER` of a `|` list, so `PICKMENU`
  prints each choice with it.

### GRID and BROWSE

Not planned.

## Size

Bytes of each region, from pyuxc's `REGION` lines, compiled 2026-10-24. The test programs hold
their own test code too. Region 3 holds `VERA.UXI`'s routines; 44 bytes is `VERA.PUT_CELL`,
which `STATUS_LINE` calls.

| Program | What it uses | File | Region 1 | Region 2 | Region 3 | Region 4 |
|---|---|---|---|---|---|---|
| `GUIEDIT` | `INPUT2` | 3422 | 2314 | | | |
| `GUIFORM` | forms, no controls | 3059 | 1475 | 271 | | |
| `GUISHOW` | fields and `SHOW` | 8559 | 6411 | 349 | 44 | |
| `GUICBO` | a `CBO` | 9539 | 6457 | 1174 | 451 | |
| `GUIMENU` | menus | 10475 | 6575 | 2312 | 451 | |
| `GUIDLG` | `MSGBOX`, `YESNO` | 10216 | 6748 | 1408 | 451 | |
| `GUIMEMO` | a memo | 12014 | 6705 | 596 | 44 | 2231 |
| `GUILBOX` | `LISTBOX` | 12099 | 6873 | 1322 | 2202 | |
| `GUIPICK` | `PICKFILE`, `PICKMANAGE` | 19512 | 6761 | 1552 | 7489 | |
| `GUIPMENU` | `PICKMENU`, no `SHOW` | 3128 | 418 | 1166 | 407 | |
| `THEMED` | dialogs | 14364 | 6964 | 1557 | 401 | |
| `HELPED` | every V1 control | 15743 | 7810 | 1414 | 401 | 2597 |
| `GUIDEMO` | every part | 42133 | 8094 | 5440 | 7443 | 2263 |

- A region holds 8192 bytes. `GUIDEMO` leaves 98 free in region 1 and 749 in region 3.
- Region 4's code and data must end below `$B800`, 6144 bytes (D10).
- Low RAM, a program's 38655 bytes from `$0801` to `$9EFF`, holds for each region a 9-byte gate
  and a 10-byte call of the loader, and for each `SUB` called across a region's edge a 7-byte
  veneer on the caller's side.

## Example

```
#INCLUDE "KEYS.UXI"
#INCLUDE "VERA.UXI"
#INCLUDE "GUI.UXI"
CONST BTN_SAVE AS UBYTE = 1, BTN_CANCEL AS UBYTE = 2
DIM TITLE AS STRING * 40, H AS UBYTE, EVENT AS UBYTE
GUI.THEME(GUI.THEMES.DARK)
H = GUI.CREATEFORM("Help Editor", GUI.CENTER, GUI.CENTER, 76, 21, GUI.FRAMED)
GUI.STARTSECTION(H, "Page", GUI.FRAMED)
GUI.SAYGET(GUI.AUTO, GUI.AUTO, "Title", TITLE, 40)
GUI.STARTSECTION(H, "Contents", GUI.FRAMED)
GUI.MEMO(GUI.AUTO, GUI.AUTO, "Text", 64, 12)
GUI.ENDSECTION()
GUI.BUTTON(19, 3, "&Save", BTN_SAVE)
GUI.BUTTON(19, 14, "&Cancel", BTN_CANCEL)
GUI.MEMO_LOAD("HELP.TXT")
EVENT = GUI.SHOW(H)
IF EVENT = BTN_SAVE THEN GUI.MEMO_SAVE("HELP.TXT")
GUI.FREE(H)
```
