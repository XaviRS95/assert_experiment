import csv
import os
import time
import argparse
from prompts.prompts_experiment3 import comb_to_tgts, seq_to_tgts
from utils import utils, regex


def experiment3(model_name: str, modules_path: str, output_filepath: str):
    ok_number = 0

    if os.path.exists(output_filepath):
        os.remove(output_filepath)

    with open(output_filepath, "w", newline="", encoding="utf-8") as results_file:
        writer = csv.writer(results_file)
        writer.writerow(["original_code", "generated_code", "iverilog_output", "time(s)", "prompt_tkns", "output_tkns"])

        codes = utils.read_code_files(modules_path)

        for i in range(len(codes)):
            print(f'Module #{i + 1} out of {len(codes)} in model {model_name}')
            used_prompt_tokens = 0
            generated_response_tokens = 0

            print(f"Original code: \n{codes[i]}")
            print('')

            time1 = time.time()
            clean_code = regex.commentless_code(code=codes[i])
            clean_comb_blocks = regex.get_blocks(code=clean_code, pattern=r'always_comb')
            clean_seq_blocks = regex.get_blocks(code=clean_code, pattern=r'always_(?:ff|latch)')
            clean_func_blocks = regex.extract_functions(code=clean_code)
            header_and_vars = regex.extract_header_and_vars(
                code=clean_code,
                comb_blocks=clean_comb_blocks,
                seq_blocks=clean_seq_blocks,
                func_blocks=clean_func_blocks
            )

            module_name = header_and_vars['header']['module_name']
            parameters = header_and_vars['header']['parameters']
            ports = header_and_vars['header']['ports']
            inner_vars = header_and_vars['inner_vars']

            assertions = []
            sequential_properties = []

            # Combinational blocks processing
            for block in clean_comb_blocks:
                comb_to_tgts_prompt = comb_to_tgts(parameters=parameters, ports=ports, inner_vars=inner_vars,
                                                   block=block)
                model_response = utils.query_ollama(prompt=comb_to_tgts_prompt, model=model_name, code_call=False)

                used_prompt_tokens += model_response.get('prompt_tkns', 0)
                generated_response_tokens += model_response.get('response_tkns', 0)

                immediate_asserts = regex.immediate_asserts_from_tgts(tgts_rules=model_response['tgts_rules'])
                assertions.append(immediate_asserts)

            # Sequential blocks processing
            for block in clean_seq_blocks:
                seq_to_tgts_prompt = seq_to_tgts(parameters=parameters, ports=ports, inner_vars=inner_vars, block=block)
                model_response = utils.query_ollama(prompt=seq_to_tgts_prompt, model=model_name, code_call=False)

                used_prompt_tokens += model_response.get('prompt_tkns', 0)
                generated_response_tokens += model_response.get('response_tkns', 0)

                clock_trigger = regex.extract_sequential_clock_trigger(block=block)
                sequential_properties.append(regex.sequential_properties_from_tgts(
                    tgts_rules=model_response['tgts_rules'],
                    clock_trigger=clock_trigger
                ))

            # Assembly
            final_module_parameters = f'# ({parameters})' if parameters else ''
            final_module_ports = ports.replace('output logic', 'input logic')
            final_module_assertions = '\n\n'.join(assertions)
            final_module_assertion_block = (
                f"always_comb begin\n    {final_module_assertions}\n    end") if final_module_assertions else ''
            final_module_properties = '\n'.join(sequential_properties)

            final_module = f"""module {module_name}_asserts {final_module_parameters} ({final_module_ports});

    {inner_vars}

    {clean_func_blocks if clean_func_blocks else ''}

    {final_module_assertion_block}

    {final_module_properties}

    endmodule"""

            compiler_output = utils.check_code_syntax(code=final_module)
            time2 = time.time()

            writer.writerow([
                codes[i],
                final_module,
                compiler_output,
                time2 - time1,
                used_prompt_tokens,
                generated_response_tokens
            ])

            print(f'Generated testing module: \n{final_module}')
            print('')
            print(f"Status: {compiler_output} | Time: {time2 - time1:.2f}s")
            print(f"Total Prompt Tokens: {used_prompt_tokens}")
            print(f"Total Response Tokens: {generated_response_tokens}")

            if compiler_output == "OK":
                ok_number += 1

            print(f"Overall Progress: {ok_number}/{len(codes)} ({ok_number / len(codes):.2%})")
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
        final_csv_path = f"sv_results_3_{args.model.replace(':', '_')}.csv"

    experiment3(
        model_name=args.model,
        modules_path=args.path,
        output_filepath=final_csv_path
    )