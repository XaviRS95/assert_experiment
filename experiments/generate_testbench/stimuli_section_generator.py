from module_info_extractor import separate_grouped_activations_in_seq_or_comb, group_clock_activations
import re

def generate_activation_with_full_type_list(full_type_signals: list, separated_activations: dict, reset_signal: str)-> dict:
    '''
    Obtains for each activation the full type of all the port variables inside of it.
    This is used to later generate the stimuli for each one of them.
    :param full_type_signals: full_type_signals = normalize_ports_with_range(input_signals=signals)
    :param separated_activations: Either the combinational or sequential separated activation.
    :return:
    '''
    new_separated_activations = dict.fromkeys(separated_activations.keys(), [])

    for activation, ports_names in separated_activations.items():
        if (not reset_signal or reset_signal not in activation):
            for signal in ports_names:
                for full_type_signal in full_type_signals:
                    space_separated_signal = full_type_signal.split(' ')
                    if signal == space_separated_signal[-1]:
                        new_separated_activations[activation].append(full_type_signal)

    return new_separated_activations



def generate_signal_stimulus(signals: list, clock_signal: str, reset_signal:str) -> str:
    '''
    Generate stimulus assignments for input signals only with enhanced type support
    :param signals: Full type signals that include inpyt|output and the datatype
    :param clock_signal:
    :param reset_signal:
    :return:
    '''

    # Extended list of SystemVerilog data types
    SV_TYPES = {
        # 2-state types
        'bit': '2-state',
        'byte': '2-state',
        'shortint': '2-state',
        'int': '2-state',
        'longint': '2-state',

        # 4-state types
        'logic': '4-state',
        'reg': '4-state',
        'integer': '4-state',
        'time': '4-state',

        # Net types
        'wire': 'net',
        'wand': 'net',
        'wor': 'net',
        'tri': 'net',
        'triand': 'net',
        'trior': 'net',
        'trireg': 'net',
        'tri0': 'net',
        'tri1': 'net',
        'uwire': 'net',

        # Real types
        'real': 'real',
        'shortreal': 'real',
        'realtime': 'real',

        # Signed/unsigned variants
        'signed_int': 'signed',
        'unsigned_int': 'unsigned',
        'signed_bit': 'signed',
        'unsigned_bit': 'unsigned',
        'signed_logic': 'signed',
        'unsigned_logic': 'unsigned',
    }

    input_signals = []
    for signal in signals:
        if 'input ' in signal and 'output ' not in signal:
            # Remove 'input' keyword and clean up
            cleaned = signal.replace('input ', '').strip().rstrip(',')
            input_signals.append(cleaned)

    template = ''

    for signal in input_signals:
        # Skip clock and reset signals
        if clock_signal and clock_signal in signal:
            continue
        if reset_signal and reset_signal in signal:
            continue

        sig_type, sig_name, array_info = parse_signal_declaration(signal)

        if sig_name:
            template += f"\t\t\t{sig_name} = "

            # Handle different types
            if sig_type in SV_TYPES:
                type_category = SV_TYPES[sig_type]

                # Handle array types (packed arrays)
                if array_info:
                    msb, lsb = int(array_info[0]), int(array_info[1])
                    width = abs(msb - lsb) + 1
                    max_val = (2 ** width) - 1

                    if type_category in ['2-state', '4-state', 'net', 'signed', 'unsigned']:
                        template += f"$urandom_range(0, {max_val});\n"

                # Handle non-array types
                else:
                    if sig_type == 'bit':
                        template += "$urandom_range(0, 1);\n"

                    elif sig_type == 'byte':
                        template += "$urandom_range(-128, 127);\n"

                    elif sig_type == 'shortint':
                        template += "$urandom_range(-32768, 32767);\n"

                    elif sig_type == 'int' or sig_type == 'signed_int' or sig_type == 'unsigned_int':
                        template += "$urandom_range(-2147483648, 2147483647);\n"

                    elif sig_type == 'longint' or sig_type == 'signed_longint' or sig_type == 'unsigned_longint':
                        template += "$urandom_range(-9223372036854775808, 9223372036854775807);\n"

                    elif sig_type in ['logic', 'reg', 'wire', 'wand', 'wor', 'tri', 'triand', 'trior', 'trireg', 'tri0',
                                      'tri1', 'uwire']:
                        template += "$urandom_range(0, 1);\n"

                    elif sig_type == 'integer':
                        template += "$urandom_range(-2147483648, 2147483647);\n"

                    elif sig_type == 'time':
                        template += "$urandom_range(0, 2**64-1);\n"

                    elif sig_type in ['real', 'shortreal', 'realtime']:
                        template += "$urandom() / (2**31-1);  // random real\n"

                    else:
                        template += "$urandom();\n"
            else:
                # For unrecognized types (like user-defined structs, enums, interfaces)
                # You might want to handle these specially
                template += "$urandom();  // Unknown type: {sig_type}\n"

    return template

def parse_signal_declaration(signal):
    '''
    Enhanced parser for SystemVerilog signal declarations
    :param signal:
    :return:
    '''

    # Remove leading/trailing whitespace
    signal = signal.strip()

    # Patterns for different declarations
    patterns = {
        # Basic types with optional packed dimensions: logic [7:0] sig_name
        'basic': r'^(?P<type>[\w]+)(?:\s+)(?P<name>\w+)$',

        # Packed array: logic [7:0] sig_name
        'packed': r'^(?P<type>\w+)\s+\[\s*(?P<msb>-?\d+)\s*:\s*(?P<lsb>-?\d+)\s*\]\s+(?P<name>\w+)$',

        # Unpacked array: logic sig_name [0:7]
        'unpacked': r'^(?P<type>\w+)\s+(?P<name>\w+)\s*\[\s*(?P<msb>-?\d+)\s*:\s*(?P<lsb>-?\d+)\s*\]$',

        # Multi-dimensional: logic [7:0] sig_name [0:3]
        'multidim': r'^(?P<type>\w+)\s+\[\s*(?P<pmsb>-?\d+)\s*:\s*(?P<plsb>-?\d+)\s*\]\s+(?P<name>\w+)\s*\[\s*(?P<umsb>-?\d+)\s*:\s*(?P<ulsb>-?\d+)\s*\]$',

        # Signed/unsigned: signed int sig_name
        'signed': r'^(?P<signed>signed|unsigned)\s+(?P<type>\w+)(?:\s+)(?P<name>\w+)$',

        # Signed with packed: signed [7:0] sig_name
        'signed_packed': r'^(?P<signed>signed|unsigned)\s+\[\s*(?P<msb>-?\d+)\s*:\s*(?P<lsb>-?\d+)\s*\]\s+(?P<name>\w+)$',

        # Struct/enum/interface (simplified)
        'complex': r'^(?P<type>\w+)\s+(?P<name>\w+)$',
    }

    for pattern_name, pattern in patterns.items():
        match = re.match(pattern, signal)
        if match:
            groups = match.groupdict()

            if pattern_name == 'packed':
                return groups['type'], groups['name'], (groups['msb'], groups['lsb'])
            elif pattern_name == 'unpacked':
                return groups['type'], groups['name'], (groups['msb'], groups['lsb'])
            elif pattern_name == 'multidim':
                # For multi-dimensional, return packed info
                return groups['type'], groups['name'], (groups['pmsb'], groups['plsb'])
            elif pattern_name == 'signed':
                return f"{groups['signed']}_{groups['type']}", groups['name'], None
            elif pattern_name == 'signed_packed':
                return f"{groups['signed']}_{groups['type'] if 'type' in groups else 'logic'}", groups['name'], (
                groups['msb'], groups['lsb'])
            else:  # basic or complex
                return groups['type'], groups['name'], None

    # If no pattern matches
    return None, None, None


def generate_combinational_block(full_type_signals: list, combinational_triggers: list, clock_signal: str, reset_signal: str) -> str:
    '''

    :param combinational_triggers:
    :return:
    '''

    combinational_block = ''

    if combinational_triggers:

        prepared_signals = []
        for signal in combinational_triggers:
            for full_type_signal in full_type_signals:
                if signal == full_type_signal.split(' ')[-1]:
                    prepared_signals.append(full_type_signal)

        stimulus = generate_signal_stimulus(signals=prepared_signals, reset_signal=reset_signal, clock_signal=clock_signal)

        sequential_template = (f'\tinitial begin\n'
                               f'\t\t// Wait for reset to complete\n'
                               f'\t\t#(RESET_DELAY + 5);\n'
                               f'\t\tfor(int i=0; i<COMB_TOTAL_TESTS; i++) begin\n'
                               f'{stimulus}'
                               f'\t\t\t#5;\n'
                               f'\t\tend\n'
                               f'\t\t#1;\n'
                               f'\t\tblocks_done++;\n'
                               f'\tend\n')

        combinational_block = sequential_template

    return combinational_block


def generate_sequential_blocks(full_type_signals: list, activations_with_ports: dict, clock_signal: str, reset_signal: str)-> list:
    '''

    :param activations_with_ports:
    :return:
    '''
    sequential_blocks = []

    activation_with_full_type_list = generate_activation_with_full_type_list(full_type_signals = full_type_signals, separated_activations=activations_with_ports, reset_signal=reset_signal)

    for key, value in activations_with_ports.items():

        stimulus = generate_signal_stimulus(signals=activation_with_full_type_list[key], reset_signal=reset_signal,
                                            clock_signal=clock_signal)
        if stimulus:
            sequential_template = (f'\tinitial begin\n'
                                   f'\t\t// Wait for reset to complete\n'
                                   f'\t\t#(RESET_DELAY + 5);\n'
                                   f'\t\tfor(int i=0; i<SEQ_TOTAL_TESTS; i++) begin\n'
                                   f'\t\t\t@({key});\n'
                                   f'{stimulus}'
                                   f'\t\tend\n'
                                   f'\t\tblocks_done = blocks_done + 1;\n'
                                   f'\tend\n')
            sequential_blocks.append(sequential_template)

    return sequential_blocks



def generate_blocks(full_type_signals: list, dut_module: str, test_module: str, clock_signal: str, reset_signal: str)-> tuple:
    '''
    Main function to generate the combinational and sequential stimuli blocks
    :param dut_module:
    :param test_module:
    :return:
    '''
    combinational_activations, clock_activations = separate_grouped_activations_in_seq_or_comb(dut_module = dut_module, test_module = test_module, reset_signal=reset_signal, clock_signal=clock_signal)
    if combinational_activations:
        combinational_block = generate_combinational_block(full_type_signals = full_type_signals, combinational_triggers=combinational_activations, clock_signal=clock_signal, reset_signal=reset_signal)
    else:
        combinational_block = ''
    if clock_signal:
        sequential_blocks =  generate_sequential_blocks(full_type_signals = full_type_signals, activations_with_ports=clock_activations, clock_signal=clock_signal, reset_signal=reset_signal)
    else:
        sequential_blocks = []

    total_blocks = (1 if combinational_block else 0) + len(sequential_blocks)

    combinational_block = '// No combinational blocks detected' if not combinational_block else combinational_block
    sequential_blocks = '// No sequential blocks detected' if not sequential_blocks else "\n\n".join(sequential_blocks)

    stimulus_blocks_section = (f'// ====================================================\n'
                               f'// TEST BLOCKS STIMULATIONS\n'
                               f'// ====================================================\n'
                               f'\n'
                               f'// COMBINATIONAL TESTS\n'
                               f'{combinational_block}\n'
                               f'\n'
                               f'// SEQUENTIAL TESTS\n'
                               f'{sequential_blocks}\n')

    return stimulus_blocks_section, total_blocks