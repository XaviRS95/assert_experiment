import csv, os, time
from utils import regex, utils
from prompts.prompts_experiment2 import *

def experiment2_full_ai(model_name: str, modules_path: str, output_filepath: str):
    ok_number = 0

    if os.path.exists(output_filepath):
        os.remove(output_filepath)

    with open(output_filepath, "w", newline="", encoding="utf-8") as results_file:
        writer = csv.writer(results_file)
        writer.writerow(["original_code", "generated_code", "iverilog_output", "time(s)", "prompt_tkns", "output_tkns"])

        codes = utils.read_code_files(modules_path)

        for i in range(len(codes)):
            print("########################################")
            time1 = time.time()

            prompt = experiment2_simple_call(code=codes[i])
            model_response = utils.query_ollama(prompt=prompt, model=model_name, code_call=True)
            compiler_output = utils.check_code_syntax(code=model_response['sv_code'])

            time2 = time.time()
            writer.writerow([
                codes[i],
                model_response['sv_code'],
                compiler_output,
                time2 - time1,
                model_response['prompt_tkns'],
                model_response['response_tkns']
            ])
            print(f'Module #{i + 1} out of {len(codes)}')
            print(f"Original code: \n{codes[i]}")
            print('')
            print(f'Generated properties: \n{model_response["sv_code"]}')
            print('')
            print(compiler_output, time2 - time1)
            print(f"Prompt consumed # of tokens: {model_response['prompt_tkns']}")
            print(f'Response-generated # of tokens: {model_response["response_tkns"]}')
            if compiler_output == "OK":
                ok_number += 1

            print(f"{ok_number}/{len(codes)}", ok_number / len(codes))

        results_file.close()


def experiment2_regex_aided(model_name: str, modules_path: str, output_filepath: str):
    ok_number = 0

    if os.path.exists(output_filepath):
        os.remove(output_filepath)

    with open(output_filepath, "w", newline="", encoding="utf-8") as results_file:
        writer = csv.writer(results_file)
        writer.writerow(["original_code", "generated_code", "iverilog_output", "time(s)", "prompt_tkns", "output_tkns"])

        codes = utils.read_code_files(modules_path)

        for i in range(len(codes)):
            print("########################################")
            time1 = time.time()

            clean_code = regex.commentless_code(code=codes[i])
            clean_comb_blocks = regex.get_blocks(code=clean_code, pattern=r'always_comb')
            clean_seq_blocks = regex.get_blocks(code=clean_code, pattern=r'always_(?:ff|latch)')
            modules = '\n'.join(clean_seq_blocks + clean_comb_blocks)

            prompt = experiment2_only_properties_call(code=modules)

            model_response = utils.query_ollama(prompt=prompt, model=model_name, code_call=True)

            #To properly evaluate the sysntatic correctness of the asserts, the original module is reassembled

            clean_func_blocks = regex.extract_functions(code=clean_code)
            header_and_vars = regex.extract_header_and_vars(code=clean_code, comb_blocks=clean_comb_blocks,
                                                            seq_blocks=clean_seq_blocks, func_blocks=clean_func_blocks)

            module_name = header_and_vars['header']['module_name']
            parameters = f"#({header_and_vars['header']['parameters']})" if header_and_vars['header']['parameters'] else ''
            ports = header_and_vars['header']['ports'].replace('output logic', 'input logic') #For testing modules, the output of the original module is an input.
            inner_vars = header_and_vars['inner_vars']

            final_module = f"""
            module {module_name}_testing {parameters} ({ports});
            
            {inner_vars}
            
            {clean_func_blocks if clean_func_blocks else ''}
            
            {model_response['sv_code']}
            
            endmodule
            """

            compiler_output = utils.check_code_syntax(code=final_module)

            time2 = time.time()
            writer.writerow([
                codes[i],
                model_response['sv_code'],
                compiler_output,
                time2 - time1,
                model_response['prompt_tkns'],
                model_response['response_tkns']
            ])
            print(f'Module #{i + 1} out of {len(codes)}')
            print(f"Original code: \n{codes[i]}")
            print('')
            print(f'Generated properties: \n{model_response["sv_code"]}')
            print('')
            print(compiler_output, time2 - time1)
            print(f"Prompt consumed # of tokens: {model_response['prompt_tkns']}")
            print(f'Response-generated # of tokens: {model_response["response_tkns"]}')
            if compiler_output == "OK":
                ok_number += 1

            print(f"{ok_number}/{len(codes)}", ok_number / len(codes))

        results_file.close()


if __name__ == "__main__":

    EXPERIMENT_MODE = 'REGEX_AIDED'
    MODEL = "deepseek-coder-v2:16b"
    MODULES_PATH = "sv_cases.csv"
    OUTPUT_CSV_FILENAME = f"sv_results_2_{EXPERIMENT_MODE}_{MODEL.replace(':', '_')}.csv"
    if EXPERIMENT_MODE == 'FULL_AI':
        experiment2_full_ai(model_name=MODEL, modules_path=MODULES_PATH, output_filepath=OUTPUT_CSV_FILENAME)
    else:
        experiment2_regex_aided(model_name=MODEL, modules_path=MODULES_PATH, output_filepath=OUTPUT_CSV_FILENAME)