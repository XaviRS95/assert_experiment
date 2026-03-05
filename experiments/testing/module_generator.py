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
    """Generate stimulus assignments for input signals only"""

    input_signals = [signal.replace("input ", "") for signal in signals if 'output ' not in signal]

    template = ''

    for signal in input_signals:
        # Skip outputs
        if (not clock_signal or clock_signal not in signal) and (not reset_signal or reset_signal not in signal):

            sig_type, sig_name, array_info = parse_signal_declaration(signal)

            if sig_name:

                template += f"\t\t\t{sig_name} = "

                # Handle different types
                if sig_type in ['bit', 'logic'] and not array_info:
                    template += "$urandom_range(0, 1);\n"

                elif array_info:
                    msb, lsb = int(array_info[0]), int(array_info[1])
                    width = abs(msb - lsb) + 1
                    max_val = 2 ** width - 1
                    template += f"$urandom_range(0, {max_val});\n"

                elif sig_type == 'byte':
                    template += "$urandom_range(-128, 127);\n"

                elif sig_type == 'int':
                    template += "$urandom_range(-2**31, 2**31-1);\n"

                elif sig_type == 'shortint':
                    template += "$urandom_range(-32768, 32767);\n"

                elif sig_type == 'longint':
                    template += "$urandom_range(-2**63, 2**63-1);\n"

                else:
                    template += "$urandom();\n"

    return template

def parse_signal_declaration(signal_line):
    """Parse a signal declaration line and return (type, name, width_info)"""
    # Remove 'input' or 'output' keyword
    clean_line = signal_line.replace('input', '').replace('output', '').strip().rstrip(';')

    # Split into parts
    parts = clean_line.split()

    if len(parts) == 1:
        # Just a name with implicit type
        return 'logic', parts[0], None
    elif len(parts) >= 2:
        sig_type = parts[0]
        sig_name = parts[-1]

        # Check if it's a packed array (contains [])

        array_match = re.search(r'\[(\d*):(\d)\]', clean_line)
        if array_match:
            return sig_type, sig_name, array_match.groups()
        else:
            return sig_type, sig_name, None

    return None, None, None



def generate_initial_stimulus(num_of_tests:int, signal_stimulus: str, clock_activation:str=''):

    clock_activation = "@(" + clock_activation + ");" if clock_activation else ''

    TEMPLATE = (f'\tinitial begin',
                f'\t\tfor(int i=0; i<{num_of_tests};i++) begin',
                f'\t\t\t{clock_activation}',
                f'{signal_stimulus}',
                f'\t\t\t#5ns;\n'
                f'\t\tend',
                f'\t\t$display("Test complete!");',
                f'\t\t$finish;',
                f'\tend')

    return '\n'.join(TEMPLATE)

def extract_variable_names(signals_list: list):
    signals_names = []

    for signal in signals_list:
        signals_names.append(signal.split(' ')[-1])

    return signals_names

def generate_final_module(timescale: str, clock_reset_initial_section: str, instantiate_section: str, initial_stimuli_section: str):
    TEMPLATE = (f'`{timescale}'
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