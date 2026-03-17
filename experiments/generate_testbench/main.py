from module_generator import generate_testbench

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

        TIMESCALE = '`timescale 1ns/1ns'
        CLK_HALF_PERIOD = 5
        RESET_DELAY = 30
        TIMEOUT_LIMIT = 20000
        COMB_TOTAL_TESTS = 100
        SEQ_TOTAL_TESTS = 100
        POST_COMPLETION_DELAY = 100

        average_errors = 0
        average_coverage = 0

        args = arguments.parse_arguments()

        file_data = filter_dataset(filepath=args.path)

        for index, row in file_data.iterrows():

                print('INDEX', index)

                dut_module = row['original_code']
                assert_module = row['generated_code']

                testbench_module = generate_testbench(
                        timescale=TIMESCALE,
                        dut_module=dut_module,
                        assert_module=assert_module,
                        CLK_HALF_PERIOD = CLK_HALF_PERIOD,
                        RESET_DELAY = RESET_DELAY,
                        TIMEOUT_LIMIT = TIMEOUT_LIMIT,
                        COMB_TOTAL_TESTS = COMB_TOTAL_TESTS,
                        SEQ_TOTAL_TESTS = SEQ_TOTAL_TESTS,
                        POST_COMPLETION_DELAY = POST_COMPLETION_DELAY)

                testbench_test_results = try_testbench(dut_module=row['original_code'],
                                                       assert_module=row['generated_code'],
                                                       testbench_module=testbench_module)

                print(testbench_module)

                print(f'Number of errors: {testbench_test_results["total_errors"]}')
                print(f'Total coverage: {testbench_test_results["coverage_pct"]}')
                print(f'Testing data:')
                [print(row) for row in testbench_test_results["testing_data"]]

                average_errors += 1 if testbench_test_results["total_errors"] > 0 else 0
                average_coverage += testbench_test_results["coverage_pct"]

                print(f"Current average errors: {average_errors / len(file_data)}")
                print(f"Current average coverage: {average_coverage / len(file_data)}")

                print('---------------------------------------------------------------------------------------------')

if __name__ == "__main__":
    main()