import re


def get_module_name(module: str):
    # Look for 'module' followed by the name
    match = re.search(r'module\s+(\w+)', module)
    return match.group(1) if match else None

def extract_ports_names(signals_list: list):
    '''
    Auxiliar function that extracts the names of the signals used in the dut and assert modules.
    :param signals_list:
    :return:
    '''
    signals_names = []
    for signal in signals_list:
        signals_names.append(signal.split(' ')[-1])

    return signals_names

def generate_instantiate_section(dut_module_name: str, assert_module_name: str, signals_list: list, section_type: str, internal_variables_names: list= []):
    '''
    Generates the binding of the dut and assert modules with their port signals.
    :param module_name:
    :param signals_list:
    :param section_type:
    :return:
    '''
    if section_type == 'dut':
        dut_module = f'\t{dut_module_name} {section_type} (\n'
    else:
        dut_module = f'\tbind {dut_module_name} {assert_module_name} checker_inst (\n'
    signals = ''
    for i in range(len(signals_list)):
        signals += f'\t\t.{signals_list[i]}({signals_list[i]}){"," if i < len(signals_list) - 1 else ""}'
    if internal_variables_names:
        signals +=',\n'
        for i in range(len(internal_variables_names)):
            signals += f'\t\t.{internal_variables_names[i]}({internal_variables_names[i]}){"," if i < len(internal_variables_names) - 1 else ""}'

    dut_module += signals
    dut_module +=  f'\t);\n'

    return dut_module



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

def extract_inner_vars(code: str, comb_blocks: list, seq_blocks: list, func_blocks: list)-> str:
    """
    Isolates the module header and internal variable declarations/assignments.
    This works by 'carving out' the procedural blocks (always, functions) from the
    raw code to reveal the structural 'Gaps' (logic, wire, assign).
    """

    extractable_code = code.strip()

    #Extract combinational & sequential blocks
    for block in comb_blocks+seq_blocks:
        extractable_code = extractable_code.replace(block, '')

    #Extract internal auxiliar functions
    for block in func_blocks:
        extractable_code = extractable_code.replace(block, '')

    #Extracts the module name and ports
    header_pattern = r'\bmodule\b[\s\S]*?;'

    # 3. Remove the header (replace with empty string)
    extractable_code = re.sub(header_pattern, '', extractable_code, count=1, flags=re.MULTILINE).strip()

    #leaving only the inner variables to extract:
    inner_vars = extractable_code.replace('endmodule', '').strip()

    return inner_vars



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


def get_port_signals(module: str):
    # Captures everything between 'module name (...);'
    # Handles multi-line port lists
    port_block = re.search(r'module\s+\w+\s*\((.*?)\)\s*;', module, re.DOTALL)
    if not port_block:
        return []

    # Split by comma and clean up whitespace/newlines
    raw_ports = port_block.group(1).split(',')
    clean_ports = [re.sub(r'\s+', ' ', p).strip() for p in raw_ports]
    return [p for p in clean_ports if p]

def get_triggers(module: str):
    # Find all always blocks and capture their trigger/type

    # 1. Capture sequential blocks: always_ff @(...) or always_latch @(...)
    seq_matches = re.finditer(r'always_(?:ff|latch) @(.*) begin', module)

    clk_trigger = ''
    rst_trigger = ''

    for m in seq_matches:
        trigger = m.group(1).strip().replace('(','').replace(')','').split(' or ')
        if trigger:
            clk_trigger = trigger[0]
            if len(trigger) > 1:
                rst_trigger = trigger[1]
        continue

    return clk_trigger, rst_trigger

def normalize_ports_with_range(input_signals: list)-> list:
    '''
    Includes the input|output type and the port type for all the variables.
    :param input_signals:
    :return:
    '''
    # Remove outer module parentheses/semicolon

    normalized = []

    # Persistent State
    curr_dir = "input"
    curr_type = "logic"
    curr_range = ""

    for part in input_signals:
        part = part.strip()
        if not part: continue

        # Regex breakdown:
        # 1. (dir)?    -> Optional input/output/inout
        # 2. (type)?   -> Optional logic/reg/wire
        # 3. (range)?  -> Optional [3:0]
        # 4. (name)    -> Signal name (Required)
        pattern = r'^(?P<dir>input|output|inout)?\s*(?P<type>logic|reg|wire|bit|byte|shortint|int|longint)?\s*(?P<range>\[.*?\])?\s*(?P<name>\w+)$'
        match = re.search(pattern, part)

        if match:
            # Update state if a NEW direction or type is explicitly mentioned
            # If a new direction/type appears, we usually reset the range
            # UNLESS a new range is also provided in the same part.
            new_dir = match.group('dir')
            new_type = match.group('type')
            new_range = match.group('range')

            if new_dir:
                curr_dir = new_dir
                curr_range = ""  # Reset range on direction change
            if new_type:
                curr_type = new_type
                curr_range = ""  # Reset range on type change
            if new_range:
                curr_range = new_range

            p_name = match.group('name')

            # Construct the explicit string using the current persistent state
            full_decl = f"{curr_dir} {curr_type} {curr_range}".replace("  ", " ").strip()
            normalized.append(f"{full_decl} {p_name}")

    return normalized

def extract_sequential_sensitivity_list_variables(dut_module: str, reset_signal: str)-> list:
    '''
    Identifies the signals used in the sensitivity list of all sequential blocks from the original module.
    :param dut_module:
    :return:
    '''
    block_pattern = r'(always_ff|always_latch)\s*@\s*\((.*?)\)'
    raw_lists = re.findall(block_pattern, dut_module, re.DOTALL)

    all_elements = []

    for _, list_content in raw_lists:
        # 2. Split by 'or' OR ',' (with optional surrounding whitespace)
        # The '|' in the regex acts as the "OR" operator
        elements = re.split(r'\s+or\s+|\s*,\s*', list_content.strip())
        for element in elements:
            if reset_signal in element:
                elements.remove(element)
        all_elements.extend(elements)


    sequential_sensitivity_list = list(set(all_elements))
    # Return unique elements, cleaned of any trailing/leading whitespace
    return sequential_sensitivity_list

def get_combinational_sensitivity_lists(test_module: str, sequential_sensitivity_list: list, clock_signal:str, reset_signal: str)-> list:
    '''
    Extracts the sensitivity list from all testing that are combinational (do not rely on clock nor reset activations)
    :param test_module:
    :param sequential_sensitivity_list:
    :return:
    '''
    PATTERN = r'@\((.*?)\)'
    combinational_sensitivity_list = []

    # Find all matches
    matches = re.findall(PATTERN, test_module)

    for sensitivity_list in matches:
        sensitivity_list = sensitivity_list.split(',')
        for signal in sensitivity_list:
            signal = signal.strip()
            #Avoid by mistake including the reset activation or clock activation.
            if (not reset_signal or reset_signal not in signal) and (not clock_signal or clock_signal not in signal) and signal not in sequential_sensitivity_list:
                combinational_sensitivity_list.append(signal)

    return list(set(combinational_sensitivity_list))


def group_clock_activations(test_module: str, clock_signal: str)-> dict:
    '''
    Extracts the sensitivity list that activates each port from all the clock-related tests.
    This is crucial to later understand what ports stimulate under what sensitivity lists,
    to build each stimulating testing block.
    :param test_module:
    :return:
    '''
    prop_pattern = r'@\(([^)]+)\)\s*(.*?)\s*;'
    matches = re.findall(prop_pattern, test_module, re.DOTALL)

    results = {}

    for activation, body in matches:

        all_extracted_vars = []

        if clock_signal in activation:

            pattern = r'disable\s+iff\s*\([^)]+\)'
            cleaned_text = re.sub(pattern, '', body)
            parts = re.split(r'\|->|\|=>', cleaned_text)

            for part in parts:

                # 3. Split by logical && or ||
                logical_groups = re.split(r'&&|\|\|', part)

                for group in logical_groups:
                    # 4. Remove parentheses to simplify the string
                    clean_group = group.replace('(', '').replace(')', '').strip()

                    # 5. Split by comparison operators to isolate the LHS
                    # This handles ==, >=, <=, !=, >, <
                    comparisons = re.split(r'==|>=|<=|!=|>|<', clean_group)

                    for comparison_part in comparisons:

                        lhs = comparison_part.strip()

                        # 6. Extract Variable Names
                        # We look for words starting with alpha/underscore.
                        # We specifically exclude matches that look like SV constants (e.g., 8'hFF)
                        # by checking if they are preceded by a tick (').

                        # Regex breakdown:
                        # (?<!['\d])  -> Negative lookbehind: Don't match if preceded by a tick or digit (filters 1'b1)
                        # \b[a-zA-Z_]\w*\b -> Standard identifier pattern
                        found_vars = re.findall(r"\b(?<!['\d])[a-zA-Z_][a-zA-Z0-9_$]*\b", lhs)

                        for v in found_vars:
                            all_extracted_vars.append(v)

            if activation not in results:
                results[activation] = all_extracted_vars
            else:
                results[activation] = list(set(results[activation]).union(set(all_extracted_vars)))

    return results

def separate_grouped_activations_in_seq_or_comb(dut_module:str, test_module: str, reset_signal: str, clock_signal: str) -> tuple:
    '''
    Groups the ports with their activation variables.
    :param dut_module:
    :param test_module:
    :return:
    '''

    #All the sequential blocks activation combinations are stored.
    sequential_sensitivity_list_variables = extract_sequential_sensitivity_list_variables(dut_module=dut_module, reset_signal=reset_signal)

    # All the combinations of the combinational blocks activation are stored.
    combinational_sensitivity_lists_variables = get_combinational_sensitivity_lists(test_module = test_module, sequential_sensitivity_list=sequential_sensitivity_list_variables, clock_signal=clock_signal, reset_signal=reset_signal)

    #Clock scenario:
    clock_related_activations = group_clock_activations(test_module=test_module, clock_signal=clock_signal)

    return combinational_sensitivity_lists_variables, clock_related_activations

#print(group_activations_with_signal_names(dut_module=dut_module, test_module=test_module))


def extract_variable_names(text):
    # 1. Strip out the 'typedef struct' blocks entirely first
    # This prevents 'data', 'keep', 'last' from being caught
    text = re.sub(r'typedef\s+struct[\s\S]*?\}\s*\w+;', '', text)

    # 2. Strip out 'assign' lines
    text = re.sub(r'assign\s+[\s\S]*?;', '', text)

    # 3. Improved Regex for Declarations:
    # It looks for a type (logic, reg, or a custom type like fifo_entry_t)
    # Then it captures the variable names, but stops if it sees an '='
    # (to avoid grabbing assignment logic).
    declaration_pattern = r'^\s*(?!\b(?:assign|parameter|typedef|module|endmodule)\b)(\w+)\s+(?:\[.*?\]\s*)?([^;=]+);'

    # We use MULTILINE so ^ matches the start of each line
    matches = re.findall(declaration_pattern, text, re.MULTILINE)

    variable_names = []
    for _, var_list in matches:
        # Split by comma for multi-variable lines: logic a, b, c;
        parts = var_list.split(',')
        for p in parts:
            # Remove array dimensions like [0:1024]
            name = re.sub(r'\[.*?\]', '', p).strip()
            # Double check to ensure we didn't grab an empty string
            # or a stray bit of logic
            if name and not any(c in name for c in '?:><+-'):
                variable_names.append(name)

    return variable_names




def extract_internal_variables_names(dut_module: str)-> list:
    '''
    Extracts all the internal variable names from the dut module to be used in the assert bind of the testbench.
    :param dut_module:
    :return:
    '''

    internal_variables_names = []

    stripped_module = dut_module

    comments_pattern = r'(\/\*[\s\S]*?\*\/)|(\/\/[^\r\n]*(\r?\n)?)'
    header_pattern = r'(module)'
    # re.sub replaces matches with an empty string
    stripped_module = re.sub(comments_pattern, '', stripped_module)

    comb_blocks = get_blocks(code=stripped_module, pattern=r'always_comb')
    seq_blocks = get_blocks(code=stripped_module, pattern=r'always_(?:ff|latch)')
    func_blocks = extract_functions(code=stripped_module)


    inner_vars = extract_inner_vars(code=stripped_module,
                                                    comb_blocks=comb_blocks,
                                                    seq_blocks=seq_blocks,
                                                    func_blocks=func_blocks)

    internal_variables_names = extract_variable_names(text = inner_vars)


    return internal_variables_names