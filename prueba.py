import re

MODULE_PREAMBLE_RE = re.compile(
    r"""
    module\s+\w+          # module name
    \s*\([^;]*?\)\s*;     # port list
    (?P<body>.*?)         # capture body lazily
    (?=
        \b(always(_comb|_ff|_latch)?|
           initial|
           generate)\b
    )
    """,
    re.DOTALL | re.VERBOSE | re.IGNORECASE
)

DECL_ASSIGN_FUNC_RE = re.compile(
    r"""
    (
        # -----------------------------
        # Net / variable declarations
        # -----------------------------
        ^\s*
        (?:logic|wire|reg|bit|byte|int|integer|shortint|longint)
        (?:\s+signed|\s+unsigned)?
        (?:\s*\[[^]]+\])*
        \s+\w+(?:\s*,\s*\w+)*
        \s*;
    |
        # -----------------------------
        # Continuous assignments
        # -----------------------------
        ^\s*
        assign
        \s+[^;]+
        ;
    |
        # -----------------------------
        # Function / task declarations
        # -----------------------------
        ^\s*
        (?:automatic\s+)?
        (?:function|task)
        \b[\s\S]*?
        end(?:function|task)
    )
    """,
    re.VERBOSE | re.MULTILINE | re.IGNORECASE
)

code = '''
module ex_dense (
    input logic a,b,c,
    output logic y
);

logic x1,x2 , x3;
wire [1:0] w1 ,w2;
assign x1=a&b;
assign x2 = b | c;
assign x3 =
    (a & c) |
    (b & ~c);

always_comb y = x1 ^ x2 ^ x3;

endmodule

'''

m = MODULE_PREAMBLE_RE.search(code)
if not m:
    raise ValueError("Module preamble not found")

preamble = m.group("body")

matches = [m.group(0).strip() for m in DECL_ASSIGN_FUNC_RE.finditer(preamble)]

for item in matches:
    print(item)
