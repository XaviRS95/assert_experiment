import re

# Example usage:
sv_code = """
module tlul_access_ctrl (
    input  logic        tl_i_a_valid,
    input  logic [2:0]  tl_i_a_opcode,
    input  logic [2:0]  tl_i_a_param,
    input  logic [2:0]  tl_i_a_size,
    output logic        tl_o_d_error,
    output logic        tl_o_d_valid
);

    always_comb begin
        tl_o_d_valid = 1'b0;
        tl_o_d_error = 1'b0;

        if (tl_i_a_valid) begin
            tl_o_d_valid = 1'b1;

            unique case (tl_i_a_opcode)
                3'b000: begin // Get
                    case (tl_i_a_size)
                        3'b000, 3'b001, 3'b010: ;
                        default: tl_o_d_error = 1'b1;
                    endcase
                end

                3'b001: begin // PutFullData
                    case (tl_i_a_param)
                        3'b000: begin
                            case (tl_i_a_size)
                                3'b001, 3'b010: ;
                                default: tl_o_d_error = 1'b1;
                            endcase
                        end
                        default: tl_o_d_error = 1'b1;
                    endcase
                end

                3'b010: begin // PutPartialData
                    case (tl_i_a_param)
                        3'b001: ;
                        default: tl_o_d_error = 1'b1;
                    endcase
                end

                default: tl_o_d_error = 1'b1;
            endcase
        end
    end

endmodule

"""


def clean_whitespace(raw_text:str) -> str:
    """
    Standardizes formatting by collapsing vertical and horizontal whitespace.
    Useful for turning jagged port/parameter lists into a clean, readable format.
    """
    if raw_text:
        clean_lines = []
        for line in raw_text.splitlines():
            # 1. Strip leading/trailing whitespace from the line
            line = line.strip()

            # 2. Replace 2 or more whitespace characters (\s{2,}) with a single space
            # This preserves the single space between 'input' and 'logic'
            line = re.sub(r'\s{2,}', ' ', line)

            if line:  # Only add if the line isn't empty
                clean_lines.append(line)

        return "\n".join(clean_lines)
    else:
        return ''

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

def commentless_code(code: str) -> str:
    """
    Removes both single-line (//) and multi-line (/* */) comments.
    Also cleans up leftover empty lines to prevent 'swiss cheese' code formatting.
    """
    pattern = r'(\/\*[\s\S]*?\*\/|\/\/.*)'
    clean_code = code
    for match in re.finditer(pattern, code):
        clean_code = clean_code.replace(match.group(0), '')
    clean_code = re.sub(r'(?m)^[ \t]*\n', '', clean_code)
    return clean_code


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

def extract_header_and_vars(code: str, comb_blocks: list, seq_blocks: list, func_blocks: list)-> dict:
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

clean_code = commentless_code(code=sv_code)
clean_comb_blocks = get_blocks(code=clean_code, pattern=r'always_comb')
clean_seq_blocks = get_blocks(code=clean_code, pattern=r'always_(?:ff|latch)')
clean_func_blocks = extract_functions(code=clean_code)
header_and_vars = extract_header_and_vars(code=clean_code, comb_blocks=clean_comb_blocks, seq_blocks=clean_seq_blocks, func_blocks=clean_func_blocks)

print("Comb blocks:")
[print(block) for block in clean_comb_blocks]
print('---------------------------------------------------------------------')
print("Seq blocks:")
[print(block) for block in clean_seq_blocks]
print('---------------------------------------------------------------------')
print('Functions blocks:')
[print(block) for block in clean_func_blocks]
print('---------------------------------------------------------------------')
print('Header and vars:')
print('Module name:', header_and_vars['header']['module_name'])
print('Parameters:', header_and_vars['header']['parameters'])
print('Ports:', header_and_vars['header']['ports'])