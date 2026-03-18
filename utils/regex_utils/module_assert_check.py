import re

def check_module_has_asserts(module: str)-> bool:
    '''
    Checks if the provided systemverilog module has at least 1 reference to a property or an assert, indicating that the module has asserts
    :param module:
    :return:
    '''
    is_valid = True

    has_testing_in_code = re.findall(r'\b(assert|property)\b', module)
    if not has_testing_in_code:
        is_valid = False

    return is_valid