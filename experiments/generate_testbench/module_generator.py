import re


def generate_reset_initial_info(reset_trigger:str, reset_signal: str, initial_reset_time: int)-> str:

    TEMPLATE = '\n'

    if reset_signal and reset_trigger:
        reset_info = {
            'reset_assert_value': "0",
            'reset_deassert_value': "1",
            'reset_wait_edge': "posedge reset",  # Wait for low→high
        }

        if "posedge" in reset_trigger:
            reset_info['reset_assert_value'] = "1"
            reset_info['reset_deassert_value'] = "0"
            reset_info['reset_wait_edge'] = "negedge reset"  # Wait for high→low

        TEMPLATE = (f'\tinitial begin\n'
                    f'\t\t{reset_signal} = {reset_info["reset_assert_value"]};\n'
                    f'\t\t#{initial_reset_time};\n'
                    f'\t\t{reset_signal} = {reset_info["reset_deassert_value"]};\n'
                    f'\tend\n')

    return TEMPLATE

def generate_clock_reset_initial_section(initial_reset_info: str, clock_signal:str= '', reset_signal:str= '', clock_period:int=0):
    template = ''

    #Generates the section of clock_signal if there is a clock in the module.
    if clock_signal:
        template += f'\tlogic {clock_signal} = 0;\n'
        if clock_period > 0:
            template += f'\talways #{clock_period} {clock_signal} = ~{clock_signal};\n'

    #Generates the reset section for if there is a reset section.
    if reset_signal:
        template += f'\tlogic {reset_signal};\n'

    if initial_reset_info:
        template += f'{initial_reset_info}\n'


    return template

def declare_dut_signals(signals: str)-> str:
    clean_signals = signals.replace('input ', '').replace('output ', '')
    return clean_signals

def generate_instantiate_section(module_name: str, signals_list: list, section_type: str):

    dut_module = f'\t{module_name} {section_type} (\n'

    signals = ''

    for i in range(len(signals_list)):
        signals += f'\t\t.{signals_list[i]}({signals_list[i]}){"," if i < len(signals_list) - 1 else ""}\n'

    dut_module += signals

    dut_module +=  f'\t);\n'

    return dut_module

def generate_signal_stimulus(signals: list, clock_signal: str, reset_signal:str) -> str:
    """Generate stimulus assignments for input signals only with enhanced type support"""

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
    """Enhanced parser for SystemVerilog signal declarations"""
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



def generate_initial_stimulus(num_of_tests:int, signal_stimulus: str, clock_activation:str=''):

    clock_activation = "@(" + clock_activation + ");" if clock_activation else ''

    TEMPLATE = (f'\tinitial begin',
                f'\t\tfor(int i=0; i<{num_of_tests};i++) begin',
                f'\t\t\t{clock_activation}',
                f'{signal_stimulus}',
                f'\t\t\t#1ps;\n'
                f'\t\t\t#5ns;\n'
                f'\t\tend',
                f'\t\t#10ns;',
                f'\t\t$display("Test complete!");',
                f'\tend')

    return '\n'.join(TEMPLATE)

def extract_variable_names(signals_list: list):
    signals_names = []

    for signal in signals_list:
        signals_names.append(signal.split(' ')[-1])

    return signals_names

def generate_final_module(timescale: str, clock_reset_initial_section: str, instantiate_section: str, initial_stimuli_section: str):
    TEMPLATE = (f'`{timescale}\n\n'
                f'module tb;\n\n'
                f'{clock_reset_initial_section}'
                f'{instantiate_section}'
                f'{initial_stimuli_section}'
                f'\nendmodule')

    return ''.join(TEMPLATE)

def generate_full_instantiate_section(clean_signals: list, dut_section: str, assert_section: str, clock_signal:str = '', reset_signal: str = ''):

    clean_signals = [signal.replace("input ", "").replace("output ", "") for signal in clean_signals]

    #Eliminate clock and reset signal from the list if they exist
    if clock_signal:
        clean_signals = [signal for signal in clean_signals if clock_signal not in signal]

    if reset_signal:
        clean_signals = [signal for signal in clean_signals if reset_signal not in signal]

    clean_signals = '\n'.join([f'\t{signal};' for signal in clean_signals])

    return clean_signals + '\n\n' + dut_section + '\n' + assert_section

def genetate_dut_assert_sections(signals: list, dut_module_name: str, assert_module_name: str) -> dict:

    signals_names = extract_variable_names(signals_list = signals)

    dut_section = generate_instantiate_section(
        module_name=dut_module_name,
        signals_list=signals_names,
        section_type='dut'
    )

    assert_section = generate_instantiate_section(
        module_name=assert_module_name,
        signals_list=signals_names,
        section_type='assertions'
    )

    return {
        'dut_section': dut_section,
        'assert_section': assert_section
    }