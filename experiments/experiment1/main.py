import csv, os, time, argparse
from utils import utils
from prompts.prompts_experiment1 import experiment1_simple_call as generate_prompt
from config import arguments
from utils.file_handling import file_handling


def experiment1(model_name: str, modules_path: str, output_filepath: str):
    ok_number = 0

    if os.path.exists(output_filepath):
        os.remove(output_filepath)

    # Use the parameter output_filepath here instead of the global constant
    with open(output_filepath, "w", newline="", encoding="utf-8") as results_file:
        writer = csv.writer(results_file)

        modules = utils.read_modules_file(modules_path)

        for i in range(len(modules)):
            print(f'Module #{i + 1} out of {len(modules)} in model {model_name}')
            time1 = time.time()

            prompt = generate_prompt(code=modules[i])
            model_response = utils.query_ollama(prompt=prompt, model=model_name, code_call=True)
            compiler_output = utils.check_code_syntax(code=model_response['sv_code'])

            time2 = time.time()
            writer.writerow([
                modules[i],
                model_response['sv_code'],
                compiler_output,
                time2 - time1,
                model_response['prompt_tkns'],
                model_response['response_tkns']
            ])
            print(f"Original code: \n{modules[i]}")
            print('')
            print(f'Generated properties: \n{model_response["sv_code"]}')
            print('')
            print(compiler_output, f"{time2 - time1:.2f}s")
            if compiler_output == "OK":
                ok_number += 1

            print(f"Progress: {ok_number}/{len(modules)} ({ok_number / len(modules):.2%})")
            print("########################################")

if __name__ == "__main__":
    # Initialize Argument Parser
    parser = arguments.parse_arguments()

    # Generate output filename logic
    if parser.output:
        final_output_path = parser.output
    else:
        # Replicates your original dynamic naming logic
        final_output_path = f"sv_results_{parser.model.replace(':', '_')}_1.csv"

    file_handling.initialize_csv_file(final_output_path)

    # Execute the experiment
    experiment1(
        model_name=parser.model,
        modules_path=parser.path,
        output_filepath=final_output_path
    )