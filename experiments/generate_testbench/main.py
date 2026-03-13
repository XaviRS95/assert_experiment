from module_info_extractor import *
from module_generator import *
import pandas as pd
from config import arguments
import requests

def filter_dataset(filepath: str):
    file_data = pd.read_csv(filepath)
    file_data = file_data[file_data['iverilog_output'] == 'OK']
    return file_data[['original_code','generated_code']]

def try_testbench(dut_module: str, assert_module:str, testbench_module:str, host:str = 'http://localhost:8002')-> dict:
    url = f"{host}/api/testbench_testing"

    payload = {
        "dut": dut_module,
        "asserts": assert_module,
        "testbench": testbench_module
    }

    response = requests.post(url, json=payload)
    response.raise_for_status()

    data = response.json()

    return data


def main():

    NUM_EXPERIMENTS = 100
    CLOCK_PERIOD_NS = 5
    INITIAL_RESET_NS = 20
    TIMESCALE = 'timescale 1ns/1ns'

    average_errors = 0
    average_coverage = 0

    args = arguments.parse_arguments()

    file_data = filter_dataset(filepath=args.path)

    for index, row in file_data.iterrows():

        print('INDEX',index)

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

        print(final_module)

        testbench_test_results = try_testbench(dut_module = row['original_code'],
                                             assert_module = row['generated_code'],
                                             testbench_module= final_module)


        print(f'Number of errors: {testbench_test_results["total_errors"]}')
        print(f'Total coverage: {testbench_test_results["coverage_pct"]}')
        print(f'Testing data:')
        [print(row) for row in testbench_test_results["testing_data"]]

        average_errors += 1 if testbench_test_results["total_errors"] > 0 else 0
        average_coverage += testbench_test_results["coverage_pct"]

        print(f"Current average errors: {average_errors / len(file_data)}")
        print(f"Current average coverage: {average_coverage / len(file_data)}")

        print('---------------------------------------------------------------------------------------------')

    print(f"Final average errors: {average_errors / len(file_data)}")
    print(f"Final average coverage: {average_coverage / len(file_data)}")



if __name__ == "__main__":
    main()