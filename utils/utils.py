import requests, csv, json, os
from utils.regex_utils.llm_utils import extract_code
from utils.regex_utils.tgts_parsing import extract_tgts_rules
from pathlib import Path

def read_modules_file(filepath: str) -> list:
    """
    Reads SystemVerilog modules from a CSV file.

    Args:
        filepath: Path to the CSV file containing a 'modules' column

    Returns:
        List of module strings (excluding the header row)
    """
    modules = []

    final_filepath = f'{Path(__file__).parent.parent.parent.absolute()}/datasets/{filepath}'

    if not os.path.exists(final_filepath):
        raise FileNotFoundError(f"CSV file not found: {final_filepath}")

    with open(final_filepath, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)  # Uses first row as headers

        for row in reader:
            if 'modules' in row and row['modules'].strip():
                modules.append(row['modules'].strip())

    print(f"Loaded {len(modules)} modules from {final_filepath}")
    return modules

def generate_final_assertion_content(module_name:str, parameters: str, aux_vars: str, assertions: str) -> str:

    header = f""" module {module_name}_assertions ({parameters});"""

    new_module = f"""{header}\n\n{aux_vars}\n\n{assertions}\n\nendmodule;"""

    return new_module


def query_ollama(
    prompt: str,
    model: str,
    code_call: bool, #This parameter is to identify if what's needed to be extracted from the response is SystemVerilog code or TGTS rules.
    host: str = "http://localhost:11434"
) -> dict:
    url = f"{host}/api/generate"

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False  # IMPORTANT: disables streaming
    }

    response = requests.post(url, json=payload)
    response.raise_for_status()

    data = response.json()
    if code_call:

        sv_code, is_valid = extract_code(output=data["response"])

        return {
            'sv_code' :  sv_code,
            'is_valid' : is_valid,
            'prompt_tkns' : data['prompt_eval_count'],
            'response_tkns' : data['eval_count']
        }
    else:
        return {
            'tgts_rules' : extract_tgts_rules(model_response=data['response']),
            'prompt_tkns': data['prompt_eval_count'],
            'response_tkns': data['eval_count']
        }


def check_code_syntax(code: str):
    endpoint = 'http://localhost:8003/api/syntax_checker'
    payload = {
        'code': code
    }
    if code:
        response = requests.post(url=endpoint, json=payload)
        result = json.loads(response.content.decode("utf-8"))
        return result['result']
    else:
        return 'CODE_BLOCK_NOT_FOUND'