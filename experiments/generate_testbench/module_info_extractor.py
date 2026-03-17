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

def generate_instantiate_section(module_name: str, signals_list: list, section_type: str):
    '''
    Generates the binding of the dut and assert modules with their port signals.
    :param module_name:
    :param signals_list:
    :param section_type:
    :return:
    '''
    dut_module = f'\t{module_name} {section_type} (\n'
    signals = ''
    for i in range(len(signals_list)):
        signals += f'\t\t.{signals_list[i]}({signals_list[i]}){"," if i < len(signals_list) - 1 else ""}\n'

    dut_module += signals
    dut_module +=  f'\t);\n'

    return dut_module

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
        pattern = r'^(?P<dir>input|output|inout)?\s*(?P<type>logic|reg|wire)?\s*(?P<range>\[.*?\])?\s*(?P<name>\w+)$'
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

def get_combinational_sensitivity_lists(test_module: str, sequential_sensitivity_list: list, reset_signal: str)-> list:
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

    for event in matches:
        #Avoid by mistake including the reset activation.
        if (not reset_signal or reset_signal not in event) and event not in sequential_sensitivity_list:
            combinational_sensitivity_list.append(event.strip())

    return list(set(combinational_sensitivity_list))


def group_activations_with_ports_names(test_module: str)-> dict:
    '''
    Extracts the sensitivity list that activates each port from all the tests.
    This is crucial to later understand what ports stimulate under what sensitivity lists,
    to build each stimulating testing block.
    :param test_module:
    :return:
    '''
    prop_pattern = r'assert\s+property\s*\(@\((.*?)\)(.*?)\)(?:\s+else|;)'
    matches = re.findall(prop_pattern, test_module, re.DOTALL)

    results = {}

    all_extracted_vars = set()

    for activation, body in matches:
        # 2. Split by implication operators |-> or |=>
        parts = re.split(r'\|->|\|=>', body)

        if len(parts) > 1:

            antecedent = parts[0]

            #Remove all disable iff() references in the antecedent:
            pattern = r'disable\s+iff\s*\([^)]+\)'
            # Replace with an empty string and clean up double spaces if necessary
            cleaned_text = re.sub(pattern, '', antecedent)
            # Optional: clean up extra internal spaces left behind
            antecedent = re.sub(r'\s{2,}', ' ', cleaned_text).strip()

            # 3. Split by logical && or ||
            logical_groups = re.split(r'&&|\|\|', antecedent)

            for group in logical_groups:
                # 4. Remove parentheses to simplify the string
                clean_group = group.replace('(', '').replace(')', '').strip()

                # 5. Split by comparison operators to isolate the LHS
                # This handles ==, >=, <=, !=, >, <
                comparisons = re.split(r'==|>=|<=|!=|>|<', clean_group)
                lhs = comparisons[0].strip()

                # 6. Extract Variable Names
                # We look for words starting with alpha/underscore.
                # We specifically exclude matches that look like SV constants (e.g., 8'hFF)
                # by checking if they are preceded by a tick (').

                # Regex breakdown:
                # (?<!['\d])  -> Negative lookbehind: Don't match if preceded by a tick or digit (filters 1'b1)
                # \b[a-zA-Z_]\w*\b -> Standard identifier pattern
                found_vars = re.findall(r"(?<!['\d\w])\b([a-zA-Z_]\w*)\b", lhs)

                for v in found_vars:
                    all_extracted_vars.add(v)

            if activation not in results:
                results[activation] = list(all_extracted_vars)
            else:
                new_list = sorted(list(set(results[activation] + list(all_extracted_vars))))
                results[activation] = new_list

    return results

def separate_grouped_activations_in_seq_or_comb(dut_module:str, test_module: str, reset_signal: str) -> tuple:
    '''
    Groups the ports with their activation variables.
    :param dut_module:
    :param test_module:
    :return:
    '''

    #All the sequential blocks activation combinations are stored.
    sequential_sensitivity_list_variables = extract_sequential_sensitivity_list_variables(dut_module=dut_module, reset_signal=reset_signal)

    # All the combinations of the combinational blocks activation are stored.
    combinational_sensitivity_lists_variables = get_combinational_sensitivity_lists(test_module = test_module, sequential_sensitivity_list=sequential_sensitivity_list_variables, reset_signal=reset_signal)

    #Groups all the activations with the ports that are involved in that block.
    activations_with_ports_names = group_activations_with_ports_names(test_module=test_module)

    combinational_grouped_variables_by_testing = dict.fromkeys(combinational_sensitivity_lists_variables, [])
    sequential_grouped_variables_by_testing = dict.fromkeys(sequential_sensitivity_list_variables, [])

    for activation in activations_with_ports_names.keys():
        #Check if it's an activation condition previously recognized
        if activation in combinational_grouped_variables_by_testing.keys():
            combinational_grouped_variables_by_testing[activation] += activations_with_ports_names[activation]

        #If reset signal is not the activation (Since it needs to be eliminated because it doesn't generate any port stimulus).
        if activation in sequential_grouped_variables_by_testing:
            sequential_grouped_variables_by_testing[activation] = sequential_grouped_variables_by_testing[activation] + activations_with_ports_names[activation]

        #Eliminate all the repeated port names from each activation type
        if combinational_grouped_variables_by_testing:
            combinational_grouped_variables_by_testing[activation] = list(set(combinational_grouped_variables_by_testing[activation]))
        if sequential_grouped_variables_by_testing:
            sequential_grouped_variables_by_testing[activation] = list(set(sequential_grouped_variables_by_testing[activation]))

    return combinational_grouped_variables_by_testing, sequential_grouped_variables_by_testing

#print(group_activations_with_signal_names(dut_module=dut_module, test_module=test_module))
