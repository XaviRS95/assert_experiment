from module_info_extractor import *
from module_generator import *
import pandas as pd
from config import arguments
import requests

def filter_dataset(filepath: str):
    file_data = pd.read_csv(filepath)
    file_data = file_data[file_data['iverilog_output'] == 'OK']
    return file_data[['original_code','generated_code']]

def try_testbench(dut_module: str, assert_module:str, testbench_module:str, host:str = 'http://localhost:8002')-> str:
    url = f"{host}/api/testbench_testing"

    payload = {
        "dut": dut_module,
        "asserts": assert_module,
        "testbench": testbench_module
    }

    response = requests.post(url, json=payload)
    response.raise_for_status()

    data = response.json()

    print(data)

    return ''


def main():

    NUM_EXPERIMENTS = 100
    CLOCK_PERIOD_NS = 5
    INITIAL_RESET_NS = 20
    TIMESCALE = 'timescale 1ns/1ns'

    args = arguments.parse_arguments()

    file_data = filter_dataset(filepath=args.path)

    for _, row in file_data.iterrows():

        print(row['original_code'],'\n')

        print(row['generated_code'],'\n')

        dut_module_name = get_module_name(module=row['original_code'])

        assert_module_name = get_module_name(module=row['generated_code'])

        signals = get_port_signals(module=row['original_code'])

        clk_trigger, rst_trigger = get_triggers(module=row['original_code'])

        clk_signal = clk_trigger.split(' ')[-1] if clk_trigger else ''
        rst_signal = rst_trigger.split(' ')[-1] if rst_trigger else ''

        # Adds the type of signal and input|output to those signals that don't have it.
        full_type_signals = normalize_ports_with_range(input_signals=signals)

        # Extracts only the input signals, leaving the output signals apart.

        initial_reset_info = generate_reset_initial_info(reset_trigger=rst_trigger,
                                                         reset_signal=rst_signal,
                                                         initial_reset_time=INITIAL_RESET_NS)

        clock_reset_initial_section = generate_clock_reset_initial_section(
            initial_reset_info=initial_reset_info,
            clock_signal=clk_signal,
            reset_signal=rst_signal,
            clock_period=CLOCK_PERIOD_NS
        )

        dut_assert_sections = genetate_dut_assert_sections(
            signals=full_type_signals,
            dut_module_name=dut_module_name,
            assert_module_name=assert_module_name)

        full_instantiate_section = generate_full_instantiate_section(clean_signals=full_type_signals,
                                                                     dut_section=dut_assert_sections['dut_section'],
                                                                     assert_section=dut_assert_sections['assert_section'],
                                                                     clock_signal=clk_signal,
                                                                     reset_signal=rst_signal)

        initial_stimuli_variables = generate_signal_stimulus(signals=full_type_signals,
                                                             clock_signal=clk_signal,
                                                             reset_signal=rst_signal)

        initial_stimuli_section = generate_initial_stimulus(num_of_tests=NUM_EXPERIMENTS,
                                                            signal_stimulus=initial_stimuli_variables,
                                                            clock_activation=clk_trigger)

        final_module = generate_final_module(timescale=TIMESCALE,
                                             clock_reset_initial_section=clock_reset_initial_section,
                                             instantiate_section=full_instantiate_section,
                                             initial_stimuli_section=initial_stimuli_section)

        is_testbench_correct = try_testbench(dut_module = row['original_code'],
                                             assert_module = row['generated_code'],
                                             testbench_module= final_module)

        print(final_module)

        print('---------------------------------------------------------------------------------------------')


if __name__ == "__main__":
    main()