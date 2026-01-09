import csv, os, requests, subprocess, time
import prompts, utils

def read_code_files(csv_path: str) -> list:
    code_list = []

    with open(csv_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        next(reader, None)  # Skip header
        for row in reader:
            if row:  # skip empty rows
                code_list.append(row[0])

    return code_list

def query_ollama(
    prompt: str,
    model: str,
    host: str = "http://localhost:11434"
) -> str:
    url = f"{host}/api/generate"

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False  # IMPORTANT: disables streaming
    }

    response = requests.post(url, json=payload)
    response.raise_for_status()

    data = response.json()
    sv_code = utils.extract_code(output=data["response"])
    return sv_code


def check_systemverilog_syntax(sv_code: str) -> str:
    filename = "sv_file.sv"

    try:
        # Write SystemVerilog code to auxiliary file
        with open(filename, "w", encoding="utf-8") as f:
            f.write(sv_code)
        # Run Icarus Verilog syntax check
        result = subprocess.run(
            ["verible-verilog-syntax", filename],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            return "OK"
        else:
            print(result.stdout)
            return result.stdout
    except Exception as e:
        print(e)
        return 'Error in Verible check'
    finally:
        # Clean up auxiliary file
        if os.path.exists(filename):
            os.remove(filename)


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

        codes = read_code_files('sv_cases.csv')
        for code in codes:
            print("########################################")
            time1 = time.time()
            prompt = prompts.experiment2_simple_call(code=code)
            module_name, parameters = utils.extract_module_ports(code=code)
            generated_asserts = query_ollama(prompt=prompt, model=MODEL)
            time2 = time.time()
            final_assertion_content = utils.generate_final_assertion_content(module_name = module_name, parameters = parameters, assertions = generated_asserts)
            compiler_output = check_systemverilog_syntax(sv_code=final_assertion_content)
            writer.writerow([
                code,
                final_assertion_content,
                compiler_output,
                time2 - time1
            ])
            print(compiler_output, time2 - time1)
            if compiler_output == "OK":
                ok_number += 1

            print(f"{ok_number}/{len(codes)}", ok_number / len(codes))

        results_file.close()