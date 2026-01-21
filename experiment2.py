import csv, os, time
from utils import regex, utils
from prompts.prompts_experiment2 import experiment2_simple_call as generate_prompt


if __name__ == "__main__":
    #prompt = "Explain transformers in simple terms."
    #result = query_ollama(prompt)
    #print(result)
    MODEL = "deepseek-coder-v2:16b"
    OUTPUT_CSV_FILENAME = f"sv_results_2_{MODEL}.csv"
    ok_number = 0

    if os.path.exists(OUTPUT_CSV_FILENAME):
        os.remove(OUTPUT_CSV_FILENAME)

    with open(OUTPUT_CSV_FILENAME, "w", newline="", encoding="utf-8") as results_file:
        writer = csv.writer(results_file)
        writer.writerow(["original_code", "generated_code", "iverilog_output"])

        codes = utils.read_code_files('sv_cases.csv')
        for code in codes:
            print("########################################")
            time1 = time.time()

            prompt = generate_prompt(code=code)
            module_name, parameters = regex.extract_module_ports(code=code)
            aux_vars = regex.extract_func_var_assign(code=code)
            generated_module = utils.query_ollama(prompt=prompt, model=MODEL)
            #final_assertion_content = utils.generate_final_assertion_content(module_name = module_name, parameters = parameters, aux_vars= aux_vars, assertions = generated_asserts)
            compiler_output = utils.check_code_syntax(code=generated_module)

            time2 = time.time()
            writer.writerow([
                code,
                generated_module,
                compiler_output,
                time2 - time1
            ])
            print(f"Original code: \n{code}")
            print('')
            print(f'Generated properties: \n{generated_module}')
            print('')
            print(compiler_output, time2 - time1)
            if compiler_output == "OK":
                ok_number += 1

            print(f"{ok_number}/{len(codes)}", ok_number / len(codes))

        results_file.close()