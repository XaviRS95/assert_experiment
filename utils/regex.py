import re
import uuid


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

def extract_code(output: str)-> str:
    '''
    Auxiliar function to extract the systemverilog code from the LLM output.
    This is just a safeguard in case the model decides to putput something else than SystemVerilog code.
    '''
    match = re.search(r"```systemverilog\s*([\s\S]*?)\s*```", output)
    sv_code = match.group(1) if match else ""
    return sv_code

def extract_tgts_rules(model_response: str)-> list:
    '''
    Auxiliar function to extract the systemverilog code from the LLM output.
    This is just a safeguard in case the model decides to putput something else than SystemVerilog code.
    '''
    # Regex breakdown:
    # RULE + name
    # WHEN + everything until the THEN keyword (non-greedy)
    # THEN + the full assignment logic
    pattern = r"RULE\s+(?P<name>\w+)\s+WHEN\s+(?P<clauses>[\s\S]+?)\s+THEN\s+(?P<check>.+)"

    matches = []

    # re.MULTILINE is used to handle the start/end of the string correctly
    for match in re.finditer(pattern, model_response):
        # .groupdict() maps the (?P<name>) syntax directly to keys
        rule_dict = match.groupdict()

        # Clean up whitespace/newlines from the captured clauses
        rule_dict['clauses'] = rule_dict['clauses'].strip()
        rule_dict['check'] = rule_dict['check'].strip()

        matches.append(rule_dict)

    return matches


def immediate_asserts_from_tgts(tgts_rules: list):
    sva_lines = []

    for rule in tgts_rules:
        # 1. Clean up the name for the property label
        assert_label = get_alpha_uuid()
        #assert_label = f"assert_label_{rule['name']}"

        if rule['clauses'] not in ['true', 'TRUE'] and rule['check'] not in ['true', 'TRUE']:
            clauses = rule['clauses']
            clauses = clauses.replace(' AND ', '&&').replace(' and ', '').replace(' NOT ', '!').replace(' not ','').replace(' OR ','||').replace(' or ','')
            check = rule['check']
            check = check.replace(' AND ', '&&').replace(' and ', '').replace(' NOT ', '!').replace(' not ','').replace(' OR ','||').replace(' or ','')
            error_message = f'$error("Error in immediate assert {assert_label}"'
            sva_block = (
                f"{assert_label}: assert( ({clauses}) ? ({check}) : 1 )"
                f"  else {error_message});\n"
            )

            sva_lines.append(sva_block)

    return "\n".join(sva_lines)

def extract_sequential_clock_trigger(block: str):
    match = re.search(r'@\((.*?)\)', block)
    if match:
        block_triggers = match.group(1)
        if " or " in block_triggers:
            return block_triggers.split('or')[0][:-1]
        else:
            return block_triggers


import re


def sequential_properties_from_tgts(tgts_rules: list, clock_trigger: str):
    sva_lines = []

    for rule in tgts_rules:
        if rule['clauses'] not in ['true', 'TRUE'] and rule['check'] not in ['true', 'TRUE']:
            property_label = get_alpha_uuid()
            # property_label = f"property_label_{rule['name']}"
            # 1. Clean up logical operators in clauses
            clauses = rule['clauses'].replace(' AND ', '&&').replace(' and ', '').replace(' NOT ', '!').replace(' not ','').replace(' OR ','||').replace(' or ','')
            checks = rule['check'].replace(' AND ', '&&').replace(' and ', '').replace(' NOT ', '!').replace(' not ','').replace(' OR ','||').replace(' or ','')

            #Eliminate same-cycle notations
            clauses = clauses.replace('[t]', '').replace('[ t ]', '')
            checks = checks.replace('[t]', '').replace('[ t ]', '')

            # 2. Extract variable and delay from rule['check']
            match = re.search(r'(\w+)\s*\[\s*t\s*\+\s*(\d+)\s*\]', checks)
            if match:
                var_name = match.group(1)
                delay_val = int(match.group(2))

                # The part after the index, e.g., " == count_reg + 1"
                val_part = checks.split(']')[-1]

                # 3. Apply $past logic:
                # If the variable name (e.g., count_reg) appears in val_part, wrap it in $past()
                # This handles increments: count_reg == $past(count_reg) + 1
                if var_name in val_part:
                    # Regex replaces the standalone variable name with $past(name)
                    val_part = re.sub(rf'\b{var_name}\b', f'$past({var_name})', val_part)

                # 4. Determine SVA delay syntax
                if delay_val == 1:
                    check_sva = var_name
                else:
                    check_sva = f"##{delay_val - 1} {var_name}"

                final_check = f"{check_sva}{val_part}"
            else:
                final_check = checks

            # 5. Generate the SVA block with corrected parentheses
            sva_block = (f"property {property_label};\n"
                         f"    @({clock_trigger}) ({clauses}) |=> ({final_check});\n"
                         f"endproperty\n"
                         f"assert property ({property_label});\n")

            sva_lines.append(sva_block)

    return "\n".join(sva_lines)

def get_alpha_uuid():
    # Generate a standard UUID4
    raw_uuid = uuid.uuid4().hex

    # Create a mapping table: 0-9 -> g-p
    # This ensures no overlap with the existing a-f letters
    mapping = str.maketrans("0123456789", "ghijklmnop")

    return raw_uuid.translate(mapping)