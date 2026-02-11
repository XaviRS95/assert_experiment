import csv
import os
import time
import argparse
from utils import regex, utils
from prompts.prompts_experiment1 import experiment1_simple_call as generate_prompt

def experiment1(model_name: str, modules_path: str, output_filepath: str):
    ok_number = 0

    if os.path.exists(output_filepath):
        os.remove(output_filepath)

    # Use the parameter output_filepath here instead of the global constant
    with open(output_filepath, "w", newline="", encoding="utf-8") as results_file:
        writer = csv.writer(results_file)
        writer.writerow(["original_code", "generated_code", "iverilog_output", "time(s)", "prompt_tkns", "output_tkns"])

        codes = utils.read_modules_file(modules_path)

        for i in range(len(codes)):
            print(f'Module #{i + 1} out of {len(codes)} in model {model_name}')
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
            print(f"Original code: \n{codes[i]}")
            print('')
            print(f'Generated properties: \n{model_response["sv_code"]}')
            print('')
            print(compiler_output, f"{time2 - time1:.2f}s")
            if compiler_output == "OK":
                ok_number += 1

            print(f"Progress: {ok_number}/{len(codes)} ({ok_number / len(codes):.2%})")
            print("########################################")

if __name__ == "__main__":
    # Initialize Argument Parser
    parser = argparse.ArgumentParser(description="Run SystemVerilog Experiment 1 using Ollama models.")

    # Define Command Line Arguments
    parser.add_argument(
        "--model",
        type=str,
        default="deepseek-coder-v2:16b",
        help="The name of the model in Ollama (e.g., codellama, llama3)"
    )
    parser.add_argument(
        "--path",
        type=str,
        default="sv_cases.csv",
        help="Path to the input CSV containing code modules"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Optional custom output filename. If omitted, one is generated automatically."
    )

    args = parser.parse_args()

    # Generate output filename logic
    if args.output:
        final_output_path = args.output
    else:
        # Replicates your original dynamic naming logic
        final_output_path = f"sv_results_{args.model.replace(':', '_')}_1.csv"

    # Execute the experiment
    experiment1(
        model_name=args.model,
        modules_path=args.path,
        output_filepath=final_output_path
    )