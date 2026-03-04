import csv
import os
import time
import argparse
from utils import utils
from prompts.prompts_experiment2 import *


def experiment2(model_name: str, modules_path: str, output_filepath: str):
    ok_number = 0

    if os.path.exists(output_filepath):
        os.remove(output_filepath)

    with open(output_filepath, "w", newline="", encoding="utf-8") as results_file:
        writer = csv.writer(results_file)
        writer.writerow(["original_code", "generated_code", "iverilog_output", "time(s)", "prompt_tkns", "output_tkns"])

        codes = utils.read_modules_file(modules_path)

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
            print(f"Original code: \n{codes[i]}\n")
            print(f'Generated properties: \n{model_response["sv_code"]}\n')
            print(compiler_output, time2 - time1)
            print(f"Prompt consumed # of tokens: {model_response['prompt_tkns']}")
            print(f'Response-generated # of tokens: {model_response["response_tkns"]}')
            if compiler_output == "OK":
                ok_number += 1

            print(f"{ok_number}/{len(codes)}", ok_number / len(codes))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run SystemVerilog Experiment 2.")

    parser.add_argument(
        "--model",
        type=str,
        default="deepseek-coder-v2:16b",
        help="Ollama model name"
    )
    parser.add_argument(
        "--path",
        type=str,
        default="sv_cases.csv",
        help="Path to input CSV"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Custom output filename (optional)"
    )

    args = parser.parse_args()

    # Determine filename
    if args.output:
        output_filename = args.output
    else:
        output_filename = f"sv_results_{args.model.replace(':', '_')}_2.csv"

    # Execution routing
    experiment2(
            model_name=args.model,
            modules_path=args.path,
            output_filepath=output_filename
        )