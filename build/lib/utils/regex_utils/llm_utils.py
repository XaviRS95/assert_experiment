import re

def extract_code(output: str)-> str:
    '''
    Auxiliar function to extract the systemverilog code from the LLM output.
    This is just a safeguard in case the model decides to putput something else than SystemVerilog code.
    '''
    match = re.search(r"```systemverilog\s*([\s\S]*?)\s*```", output)
    sv_code = match.group(1) if match else ""
    return sv_code
