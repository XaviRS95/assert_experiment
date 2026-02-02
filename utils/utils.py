import re, requests, csv, json, uuid
from .regex import extract_code, extract_tgts_rules

def read_code_files(csv_path: str) -> list:
    code_list = []

    with open(csv_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        next(reader, None)  # Skip header
        for row in reader:
            if row:  # skip empty rows
                code_list.append(row[0])

    return code_list[23:]

def generate_final_assertion_content(module_name:str, parameters: str, aux_vars: str, assertions: str) -> str:

    #if f'module {module_name}' in

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
        return {
            'sv_code' :  extract_code(output=data["response"]),
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
    endpoint = 'http://localhost:8002/api/syntax_checker'
    payload = {
        'code': code
    }

    response = requests.post(url=endpoint, json=payload)
    result = json.loads(response.content.decode("utf-8"))
    return result['result']