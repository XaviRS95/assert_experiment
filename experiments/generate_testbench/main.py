from module_generator import generate_testbench
import pandas as pd
from update_assert_module import process_module_complete
from config import arguments
import requests, time, glob, os

def try_testbench(dut_module: str, assert_module:str, testbench_module:str, host:str = 'http://localhost:8002')-> dict:
    '''

    :param dut_module:
    :param assert_module:
    :param testbench_module:
    :param host:
    :return:
    '''
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


# --- Assuming these helper functions exist in your environment ---
# from your_module import arguments, generate_testbench, try_testbench

def run_coverage_analysis(file_data):
    """
    Refactored version of your main() logic to process a specific DataFrame slice.
    """
    if file_data.empty:
        return 0.0

    TIMESCALE = '`timescale 1ns/1ns'
    CLK_HALF_PERIOD = 5
    RESET_DELAY = 30
    TIMEOUT_LIMIT = 20000
    COMB_TOTAL_TESTS = 100
    SEQ_TOTAL_TESTS = 100
    POST_COMPLETION_DELAY = 100

    average_coverage = 0

    for index, row in file_data.iterrows():
        # Using the logic from your provided main()
        dut_module = row['original_code']
        assert_module = row['generated_code']

        if 'obi_protocol_controller' in dut_module:
            pass

        if 'typedef' in assert_module:
            assert_module = process_module_complete(module_content=assert_module)

        testbench_module = generate_testbench(
            timescale=TIMESCALE,
            dut_module=dut_module,
            assert_module=assert_module,
            CLK_HALF_PERIOD=CLK_HALF_PERIOD,
            RESET_DELAY=RESET_DELAY,
            TIMEOUT_LIMIT=TIMEOUT_LIMIT,
            COMB_TOTAL_TESTS=COMB_TOTAL_TESTS,
            SEQ_TOTAL_TESTS=SEQ_TOTAL_TESTS,
            POST_COMPLETION_DELAY=POST_COMPLETION_DELAY
        )

        testbench_test_results = try_testbench(
            dut_module=dut_module,
            assert_module=assert_module,
            testbench_module=testbench_module
        )

        coverage = testbench_test_results.get('coverage_pct', 0)

        average_coverage += testbench_test_results.get('coverage_pct', 0)

    return average_coverage / len(file_data)


def process_directory(directory_path):
    # Search for all CSV files in the directory
    csv_files = glob.glob(os.path.join(directory_path, "*.csv"))
    print(f'Found files: {csv_files}')
    for filepath in csv_files:
        llm_name = os.path.basename(filepath).replace(".csv", "")
        print(f"\n{'=' * 60}\nPROCESSING LLM: {llm_name}\n{'=' * 60}")

        try:
            data = pd.read_csv(filepath)
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            continue

        # Define the subsections
        subsections = {
            "combinational_basic": data.iloc[0:80],
            "sequential_basic": data.iloc[80:160],
            "fsm": data.iloc[160:190],
            "industry": data.iloc[-10:]
        }

        for sub_name, df_slice in subsections.items():
            # Filter: only rows where iverilog_output is "OK"
            filtered_df = df_slice[df_slice['iverilog_output'] == "OK"].copy()

            if filtered_df.empty:
                print(f"[{sub_name}] No 'OK' results found. Skipping.")
                continue

            print(f"\n--- Subsection: {sub_name} (Rows: {len(filtered_df)}) ---")

            # Execute the core logic
            avg_pct = run_coverage_analysis(filtered_df)

            print(f"RESULT: {llm_name} | {sub_name} | Avg Coverage: {avg_pct:.2f}%")



# Update this path to your directory containing the CSVs
TARGET_DIR = "../../all_results/results_7/experiment3"
process_directory(TARGET_DIR)