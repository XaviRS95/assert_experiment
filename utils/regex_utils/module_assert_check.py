import re

def check_module_has_asserts(module: str)-> bool:
    '''
    Checks if the provided systemverilog module has at least 1 reference to an assert in the experiment 1 & 2.
    :param module:
    :return:
    '''
    is_valid = True

    has_asserts_in_code = re.findall(r'assert\s*\(\s*.*?\s*==\s*.*?\)\s*else\s*\$error\s*\(\s*""[^""]*""\s*\)\s*;', module)
    has_properties_in_code = re.findall(r'property\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*;', module)
    if not has_asserts_in_code and not has_properties_in_code:
        is_valid = False

    return is_valid


def check_module_has_asserts_properties(module: str)-> bool:
    '''
    Checks if the provided systemverilog module has at least 1 reference to a property or an assert, indicating that the module has asserts in experiment 3
    :param module:
    :return:
    '''
    is_valid = True

    has_testing_in_code = re.findall(r'\b(assert property)\b', module)
    if not has_testing_in_code:
        is_valid = False

    return is_valid