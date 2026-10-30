"""DBDO's card: DBDOT's, with command files. MAIN.PRG passes 255 bytes before its DO, SUB.PRG
ends its lines in CR LF, NEST.PRG has no LF at its end. IF.PRG nests IFs in taken and skipped
branches; IFEND.PRG ends while it skips.
LOOP.PRG nests loops, skips a loop in a loop, and RETURNs from loops in two files. ASK.PRG
reads the keyboard."""
import os
import runpy

FILL = "".join('? "fill %02d ...................."\n' % n for n in range(1, 13))
FILES = {
    "MAIN.PRG": FILL + "USE CLUB\nDO SUB\n? \"main back\", RECNO()\nDO SUB.PRG\n? \"main end\"\n",
    "SUB.PRG": "? \"sub\", NAME\r\nSKIP\r\nDO NEST\r\n? \"sub back\"\r\nRETURN\r\n? \"sub never\"\r\n",
    "NEST.PRG": "? \"nest\"",
    "ERR.PRG": "? \"err 1\"\nDO ERR2\n? \"err never\"\n",
    "ERR2.PRG": "? \"err2\"\nBOGUS\n? \"err2 never\"\n",
    "DEEP.PRG": "? \"deep\"\nDO DEEP\n",
    "CAN.PRG": "DO CAN2\n? \"can never\"\n",
    "CAN2.PRG": "? \"can2\"\nCANCEL\n? \"can2 never\"\n",
    "IF.PRG": "STORE 5 TO N\nIF N > 3\n? \"big\"\nIF N > 10\n? \"never 1\"\nELSE\n? \"not huge\"\n"
              "ENDIF\nELSE\n? \"never 2\"\nIF .T.\n? \"never 3\"\nELSE\n? \"never 4\"\nENDIF\n"
              "ENDIF\nif N = 1\n? \"never 5\"\nelse\n? \"else\", N\nDO NEST\nendif\nIF .F.\n"
              "RETURN\nENDI\n? \"if end\"\n",
    "IFBAD.PRG": "IF 1\n? \"bad never\"\n",
    "IFSYN.PRG": "IF .T. 2\n? \"syn never\"\n",
    "IFEND.PRG": "IF .F.\n? \"end never\"\n",
    "LOOP.PRG": "STORE 1 TO N\nDO WHILE N < 4\nSTORE 1 TO M\ndo while M < N\n? \"inner\", N, M\n"
                 "M = M + 1\nENDD\nIF N = 2\nDO WHILE .F.\nDO WHILE .T.\nENDDO\n? \"never 1\"\nENDDO\n"
                 "ELSE\n? \"outer\", N\nENDIF\nDO NEST\nN = N + 1\nENDDO\n? \"while end\", N\n"
                 "DO WHILE .T.\nDO WRET\nRETURN\nENDDO\n",
    "WRET.PRG": "DO WHILE .T.\n? \"wret\"\nRETURN\nENDDO\n",
    "WBAD.PRG": "DO WHILE 1\n? \"bad never\"\nENDDO\n",
    "ASK.PRG": "ACCEPT \"Who? \" TO WHO\nINPUT \"Age? \" TO AGE\n? \"ask\", WHO, AGE + 1\n",
}

_dbdot = runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "DBDOT.PY"))["card"]


def card(image):
    _dbdot(image, {name: text.encode("ascii") for name, text in FILES.items()})
