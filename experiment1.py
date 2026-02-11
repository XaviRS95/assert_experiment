import csv, os, time
from utils import regex, utils
from prompts.prompts_experiment1 import experiment1_simple_call as generate_prompt


def experiment1(model_name: str, modules_path: str, output_filepath: str):
    ok_number = 0

    if os.path.exists(output_filepath):
        os.remove(output_filepath)

    with open(OUTPUT_CSV_FILENAME, "w", newline="", encoding="utf-8") as results_file:
        writer = csv.writer(results_file)
        writer.writerow(["original_code", "generated_code", "iverilog_output", "time(s)", "prompt_tkns", "output_tkns"])

        codes = utils.read_modules_file(modules_path)

        for i in range(len(codes)):
            print("########################################")
            time1 = time.time()

            prompt = generate_prompt(code=codes[i])
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
            print(f'Module #{i+1} out of {len(codes)}')
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

    MODEL = "deepseek-coder-v2:16b"
    MODULES_PATH = "sv_cases.csv"
    OUTPUT_CSV_FILENAME = f"sv_results_1_{MODEL.replace(':', '_')}.csv"

    experiment1(model_name=MODEL, modules_path=MODULES_PATH, output_filepath=OUTPUT_CSV_FILENAME)