import re
from utils.regex_utils.module_assert_check import check_module_has_asserts

def extract_code(output: str)-> tuple:
    '''
    Auxiliar function to extract the systemverilog code from the LLM output.
    This is just a safeguard in case the model decides to putput something else than SystemVerilog code.
    '''
    sv_code = output
    is_valid = True

    correct_format_output_match = re.search(r"```systemverilog\s*([\s\S]*?)\s*```", sv_code)

    if not correct_format_output_match:
        is_valid = False
    else:
        sv_code = correct_format_output_match.group(1)
        if not check_module_has_asserts(module=sv_code):
            is_valid = False

    return sv_code, is_valid