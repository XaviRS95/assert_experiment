import csv
import os
import time
import argparse
from prompts.prompts_experiment3 import comb_to_tgts_prompt, seq_to_tgts_prompt
from utils import utils, regex

def generate_comb_asserts(
        clean_comb_blocks,
        parameters,
        ports,
        inner_vars,
        model_name,
)->dict:

    prompt_tkns = 0,  # Total number of tokens in the prompts to process all sequential blocks
    response_tkns = 0  # Total number of tokes in the responses to generate all TGTS rules

    immediate_assertions = [] #Auxiliar list to store all final assertions

    for block in clean_comb_blocks:

        prompt = comb_to_tgts_prompt(parameters=parameters, ports=ports, inner_vars=inner_vars,
                                                  block=block)

        model_response = utils.query_ollama(prompt=prompt, model=model_name, code_call=False)

        prompt_tkns += model_response.get('prompt_tkns', 0)
        response_tkns += model_response.get('response_tkns', 0)

        immediate_asserts = regex.immediate_asserts_from_tgts(tgts_rules=model_response['tgts_rules'])
        immediate_assertions.append(immediate_asserts)

    return {
        'prompt_tkns': prompt_tkns,
        'response_tkns': response_tkns,
        'immediate_assertions': immediate_assertions
    }


def generate_seq_properties(
        clean_seq_blocks,
        parameters,
        ports,
        inner_vars,
        model_name,
) -> dict:

    prompt_tkns = 0,  # Total number of tokens in the prompts to process all sequential blocks
    response_tkns = 0  # Total number of tokes in the responses to generate all TGTS rules

    sequential_properties = [] #Auxiliar list to store all final properties

    for block in clean_seq_blocks:

        prompt = seq_to_tgts_prompt(parameters=parameters, ports=ports, inner_vars=inner_vars,
                                                block=block)

        model_response = utils.query_ollama(prompt=prompt, model=model_name, code_call=False)

        prompt_tkns += model_response.get('prompt_tkns', 0)
        response_tkns += model_response.get('response_tkns', 0)

        #Extracts the clock and possible reset sensitivity list
        sensitivity_list = regex.extract_sensitivity_list(block=block)

        #Generates the sequential properties from the TGTS rules previously generated
        block_sequential_properties = regex.sequential_properties_from_tgts(
            tgts_rules=model_response['tgts_rules'],
            clock_trigger=sensitivity_list
        )

        sequential_properties.append(block_sequential_properties)

    return {
        'prompt_tkns': prompt_tkns,
        'response_tkns': response_tkns,
        'sequential_properties': sequential_properties
    }

def experiment3(model_name: str, modules_path: str, output_filepath: str):


    if os.path.exists(output_filepath):
        os.remove(output_filepath)

    with open(output_filepath, "w", newline="", encoding="utf-8") as results_file:
        writer = csv.writer(results_file)
        writer.writerow(["original_code", "generated_code", "iverilog_output", "time(s)", "prompt_tkns", "output_tkns"])

        correctly_generated_numbers = 0 #Auxiliar variable to keep track of how many modules have been generated syntactically correct during execution time.

        modules = utils.read_modules_file(modules_path)

        for i in range(len(modules)):
            print(f'Module #{i + 1} out of {len(modules)} in model {model_name}')

            used_prompt_tokens = 0
            generated_response_tokens = 0

            print(f"Original code: \n{modules[i]}\n")

            time1 = time.time()


            clean_code = regex.commentless_code(code=modules[i]) #Remove comments from the code

            #Extracts all the combinational blocks from the module
            clean_comb_blocks = regex.get_blocks(code=clean_code, pattern=r'always_comb')

            #Extracts all the sequential blocks from the module
            clean_seq_blocks = regex.get_blocks(code=clean_code, pattern=r'always_(?:ff|latch)')

            #To avoid going through modules with no combinational nor sequential blocks:
            if clean_seq_blocks or clean_comb_blocks:

                clean_func_blocks = regex.extract_functions(code=clean_code)


                header_and_vars = regex.extract_module_interface_and_decls(
                    code=clean_code,
                    comb_blocks=clean_comb_blocks,
                    seq_blocks=clean_seq_blocks,
                    func_blocks=clean_func_blocks
                )

                module_name = header_and_vars['header']['module_name']
                parameters = header_and_vars['header']['parameters']
                ports = header_and_vars['header']['ports']
                inner_vars = header_and_vars['inner_vars']

                immediate_assertions = generate_comb_asserts(
                    clean_comb_blocks = clean_comb_blocks,
                    parameters = parameters,
                    ports = ports,
                    inner_vars = inner_vars,
                    model_name = model_name)

                sequential_properties = generate_seq_properties(
                    clean_seq_blocks=clean_seq_blocks,
                    parameters=parameters,
                    ports=ports,
                    inner_vars=inner_vars,
                    model_name=model_name)

                # Final assembly of the module:

                final_module_parameters = f'# ({parameters})' if parameters else ''
                final_module_ports = ports.replace('output logic', 'input logic')

                #Formatting immediate assertions to be included in the module:
                final_module_assertions = '\n\n'.join(immediate_assertions)
                final_module_assertion_block = (
                    f"always_comb begin\n    {final_module_assertions}\n    end") if final_module_assertions else ''

                #Formatting sequential properties to be included in the module:
                final_module_properties = '\n'.join(sequential_properties)

                #Template to generate the final SystemVerilog module:
                final_module = f"""module {module_name}_asserts {final_module_parameters} ({final_module_ports});

                    {inner_vars}

                    {clean_func_blocks if clean_func_blocks else ''}

                    {final_module_assertion_block}

                    {final_module_properties}

                    endmodule"""

                print(f'Generated testing module: \n{final_module}\n')

                #Syntax checker output:
                compiler_output = utils.check_code_syntax(code=final_module)

            else:
                compiler_output = 'NO_SEQ_OR_COMB_BLOCK_FOUND'

            time2 = time.time()

            writer.writerow([
                modules[i],
                final_module,
                compiler_output,
                time2 - time1,
                used_prompt_tokens,
                generated_response_tokens
            ])

            print(f"Status: {compiler_output} | Time: {time2 - time1:.2f}s")
            print(f"Total Prompt Tokens: {used_prompt_tokens}")
            print(f"Total Response Tokens: {generated_response_tokens}")

            if compiler_output == "OK":
                correctly_generated_numbers += 1

            print(f"Overall Progress: {correctly_generated_numbers}/{len(modules)} ({correctly_generated_numbers / len(modules):.2%})")
            print("########################################")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run SystemVerilog Experiment 3 (TGTS Generation).")

    parser.add_argument(
        "--model",
        type=str,
        default="deepseek-coder-v2:16b",
        help="Model name in Ollama"
    )
    parser.add_argument(
        "--path",
        type=str,
        default="sv_cases.csv",
        help="Path to the source CSV"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Explicit output filename"
    )

    args = parser.parse_args()

    # Generate filename if not provided
    if args.output:
        final_csv_path = args.output
    else:
        final_csv_path = f"sv_results_{args.model.replace(':', '_')}_3.csv"

    experiment3(
        model_name=args.model,
        modules_path=args.path,
        output_filepath=final_csv_path
    )