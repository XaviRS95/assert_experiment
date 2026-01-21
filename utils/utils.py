import re, requests, csv, json

def read_code_files(csv_path: str) -> list:
    code_list = []

    with open(csv_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        next(reader, None)  # Skip header
        for row in reader:
            if row:  # skip empty rows
                code_list.append(row[0])

    return code_list

def generate_final_assertion_content(module_name:str, parameters: str, aux_vars: str, assertions: str) -> str:
    new_module = f""" 
    module {module_name}_assertions ({parameters}, input logic clk);
    
    {aux_vars}
    
    {assertions}
    
    endmodule;"""

    return new_module


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
    sv_code = extract_code(output=data["response"])
    return sv_code


def check_code_syntax(code: str):
    endpoint = 'http://localhost:8002/api/syntax_checker'
    payload = {
        'code': code
    }

    response = requests.post(url=endpoint, json=payload)
    result = json.loads(response.content.decode("utf-8"))
    return result['result']




