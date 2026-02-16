from ..regex_utils.text_processing import clean_whitespace
import re

def extract_module_name_parms_ports(code: str)-> dict:
    """
    Parses the module header to extract the name, parameter list, and port list.
    Handles optional parameter blocks (#) and multi-line declarations.
    """
    # Your specified regex pattern
    # Group 1: Name, Group 2: Parameters (Optional), Group 3: Ports
    pattern = r"module\s+(\w+)\s*(?:#\s*\(([\s\S]*?)\)\s*)?\(([\s\S]*?)\)\s*;"

    # re.DOTALL is essential for multi-line headers
    match = re.search(pattern, code, re.DOTALL)

    if match:
        module_name = match.group(1)
        # .group(2) will be None if there is no #(...) block
        raw_params = clean_whitespace(raw_text=match.group(2))
        raw_ports = clean_whitespace(raw_text=match.group(3))

        # Clean up whitespace for better readability
        return {
            "module_name": module_name.strip(),
            "parameters": raw_params.strip(),
            "ports": raw_ports.strip()
        }

    return {}

def extract_module_interface_and_decls(code: str, comb_blocks: list, seq_blocks: list, func_blocks: list)-> dict:
    """
    Isolates the module header and internal variable declarations/assignments.
    This works by 'carving out' the procedural blocks (always, functions) from the
    raw code to reveal the structural 'Gaps' (logic, wire, assign).
    """

    header_pattern = r'\bmodule\b[\s\S]*?;'
    extractable_code = code.strip()

    #Extract combinational & sequential blocks
    for block in comb_blocks+seq_blocks:
        extractable_code = extractable_code.replace(block, '')

    #Extract internal auxiliar functions
    for block in func_blocks:
        extractable_code = extractable_code.replace(block, '')

    #Extracts the module name and ports
    module_header = re.search(header_pattern, extractable_code)
    header_text = ''

    if module_header:
        header_text = module_header.group(0)
        extractable_code = extractable_code.replace(header_text, '')

    #leaving only the inner variables to extract:
    inner_vars = extractable_code.replace('endmodule', '').strip()

    header = extract_module_name_parms_ports(code=header_text)

    return {
        'header': header,
        'inner_vars': inner_vars
    }

def extract_functions(code: str)-> list:
    """
    Captures all function definitions within a module.
    Uses a multi-line anchor to ignore 'function' keywords appearing in mid-line comments.
    """
    pattern = r'(?m)^[ \t]*function\b[\s\S]*?\bendfunction\b'
    functions = []
    for match in re.finditer(pattern, code):
        function = match.group(0)
        functions.append(function)

    return functions

def get_blocks(code:str, pattern: str):
    """
    Entry point to find all procedural blocks (always_ff, always_comb, etc.)
    within a module based on a starting keyword pattern.
    """
    blocks = []
    for match in re.finditer(pattern, code):
        block_data = begin_end_extractor(code=code, start_match=match)
        if block_data:
            blocks.append(block_data)
    return blocks

def begin_end_extractor(code:str, start_match)-> str:
    """
    Analyzes a code slice to find the balanced 'end' keyword for a given block.
    Uses a stack-based counting approach to handle nested begin/end pairs correctly.
    """
    start_pos = start_match.start()
    # 2. Search for 'begin' or 'end' only AFTER the always_comb
    # We use finditer to get the positions (match.start() and match.end())
    search_area = code[start_pos:]
    stack = 0
    first_begin_found = False
    block_end_pos = -1

    # This regex finds 'begin' and 'end' as whole words
    for match in re.finditer(r'\b(begin|end)\b', search_area):
        word = match.group(1)

        if word == 'begin':
            if not first_begin_found:
                first_begin_found = True
            stack += 1

        elif word == 'end':
            stack -= 1

        # 3. When stack hits 0, we've found the matching 'end'
        if first_begin_found and stack == 0:
            block_end_pos = start_pos + match.end()
            break

    if block_end_pos != -1:
        return code[start_pos:block_end_pos]

    return ''

def extract_block_content(block: str):
    # 1. Identify the header: always_ff/comb/latch + optional @(...) + begin
    # This regex looks for the first occurrence of the always block start
    header_pattern = re.compile(
        r"always_(?:ff|comb|latch)\s*(?:@\s*\(.*?\))?\s*begin",
        re.DOTALL
    )

    header_match = header_pattern.search(block)

    if not header_match:
        return "No always block found."

    # The starting point of our content is right after the 'begin'
    content_start = header_match.end()

    # 2. Find the index of the absolute LAST 'end' in the string
    # We use rfind to search backwards from the end of the file
    last_end_match = list(re.finditer(r'\bend\b(?!\s*\w)', block))

    if not last_end_match:
        return "No closing 'end' found."

    # We take the start position of the very last 'end' keyword found
    content_end = last_end_match[-1].start()

    # 3. Slice the string to extract only the internal content
    extracted_logic = block[content_start:content_end]

    return extracted_logic.strip('\n\r')

def extract_sensitivity_list(block: str):
    match = re.search(r'@\((.*?)\)', block)
    clk = ''
    rst = ''
    if match:
        block_triggers = match.group(1)
        if " or " in block_triggers:
            clk_and_rst = block_triggers.split(' or ')
            clk = clk_and_rst[0]
            rst = clk_and_rst[1]
        else:
            clk = block_triggers
    return {
        'clk': clk,
        'rst': rst
    }