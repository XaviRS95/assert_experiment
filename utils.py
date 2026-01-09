import re

def extract_code(output: str)-> str:
    match = re.search(r"```systemverilog\s*([\s\S]*?)\s*```", output)
    sv_code = match.group(1) if match else ""
    return sv_code

def extract_module_ports(code: str):
    # Regex to capture module name and parameters
    pattern = r"module\s+(\w+)\s*\((.*?)\)\s*;"

    match = re.search(pattern, code, re.DOTALL)
    if match:
        module_name = match.group(1)
        parameters = match.group(2).strip()
        return module_name, parameters
    else:
        return "", ""

def generate_final_assertion_content(module_name:str, parameters: str, assertions: str) -> str:
    new_module = f""" module {module_name}_assertions ({parameters});
    {assertions}
    endmodule;"""

    return new_module