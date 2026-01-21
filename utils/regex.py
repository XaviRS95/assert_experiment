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
        (?:logic|wire|reg|bit|byte|int|integer|shortint|longint|localparam)
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


def extract_func_var_assign(code: str)-> str:
    '''
    Extracts auxiliar internal functions, variables and their assigns from inside the module to include them in the test module.
    :param code: SystemVerilog code of the whole module
    :return str: combined code of the previously-mentioned elements
    '''
    m = MODULE_PREAMBLE_RE.search(code)
    if not m:
        raise ValueError("Module preamble not found")
    preamble = m.group("body")
    matches = [m.group(0).strip() for m in DECL_ASSIGN_FUNC_RE.finditer(preamble)]
    result = '\n'.join(matches)
    return result

def extract_code(output: str)-> str:
    '''Auxiliar function to extract the systemverilog code from the LLM output. This is just a safeguard in case the model decides to putput something else than SystemVerilog code.'''
    match = re.search(r"```systemverilog\s*([\s\S]*?)\s*```", output)
    sv_code = match.group(1) if match else ""
    return sv_code

def extract_module_ports(code: str):
    '''Extracts the module name and its parameters'''
    # Regex to capture module name and parameters
    pattern = r"module\s+(\w+)\s*\((.*?)\)\s*;"

    match = re.search(pattern, code, re.DOTALL)
    if match:
        module_name = match.group(1)
        parameters = match.group(2).strip()
        return module_name, parameters
    else:
        return "", ""