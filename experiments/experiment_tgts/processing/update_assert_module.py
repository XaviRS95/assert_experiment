import re

import re


def extract_internal_variables(module_content, typedef_names):
    typedef_names_list = list(typedef_names.keys())
    types = r'\b(?:bit|byte|shortint|int|longint|reg|logic|integer|' + '|'.join(typedef_names) + r')\b'
    pattern = r'(?:^|\n)\s*(' + types + r')\s+(?:signed\s+)?(?:unsigned\s+)?([^;]+);'

    matches = re.findall(pattern, module_content, flags=re.DOTALL)

    variables = []
    for data_type, vars_line in matches:
        if data_type in typedef_names_list:
            data_type = typedef_names[data_type]
        parts = re.split(r',\s*', vars_line)
        for part in parts:
            part = part.strip()
            if '=' in part:
                part = part.split('=')[0].strip()

            var_name = re.sub(r'\[\s*[^\]]*\s*\]', '', part).strip()

            if var_name and not var_name.startswith('//'):
                variables.append(f"{data_type} {var_name}")

    return variables


def extract_typedef_name(module_content):
    typedef_names = {}
    pattern = r'typedef\s+(?:enum\s+)?([\w\s\[\]:]+)\s*\{[\s\S]*?\}\s*(\w+);'
    matches = re.findall(pattern, module_content, flags=re.DOTALL)
    for match in matches:
        typedef_names[match[1]] = match[0]
    return typedef_names


def obtain_internal_variables(module_content):
    pattern1 = r'[a-z]{32}:\s*assert property\s*\(.*?\)\s*else\s*\$error\(".*"\)\s*;?\s*\n?'
    pattern2 = r'property\s+([a-z]{32})\s*;.*?endproperty\s+assert\s+property\s*\(\s*\1\s*\)\s*;'
    pattern3 = r'function\s+\S+\s+(\w+)\s*\([^)]*\)\s*;.*?endfunction'
    pattern4 = r'^\s*module\s+\w+\s*(?:#\s*\([^)]*\)\s*)?(?:\([^)]*\)\s*)?;'

    module_content = re.sub(pattern1, '', module_content, flags=re.MULTILINE | re.DOTALL)
    module_content = re.sub(pattern2, '', module_content, flags=re.MULTILINE | re.DOTALL)
    module_content = re.sub(pattern3, '', module_content, flags=re.MULTILINE | re.DOTALL)
    module_content = re.sub(pattern4, '', module_content, flags=re.MULTILINE | re.DOTALL)
    module_content = module_content.strip()

    typedef_names = extract_typedef_name(module_content)
    internal_variables = extract_internal_variables(module_content=module_content, typedef_names=typedef_names)

    return internal_variables

def extract_ports_and_merge(module_content, internal_variables):
    port_pattern = r'module\s+\w+\s*(?:#\s*\([^)]*\)\s*)?\s*\(\s*(.*?)\s*\)\s*;'

    match = re.search(port_pattern, module_content, flags=re.DOTALL)
    if not match:
        return []

    ports_section = match.group(1)

    port_pattern_detail = r'(input|output|inout)\s+([^,;]+)'
    ports = re.findall(port_pattern_detail, ports_section)

    port_list = []
    for direction, port_decl in ports:
        port_decl = port_decl.strip()
        port_list.append(f"{direction} {port_decl}")

    for var in internal_variables:
        port_list.append(f"input {var}")

    port_arguments = ',\n'.join(port_list)
    return port_arguments


def update_module_header(module_content, port_arguments):
    header_pattern = r'(module\s+\w+\s*(?:#\s*\([^)]*\)\s*)?)\s*\(\s*.*?\s*\)\s*;'
    new_header = f'\\1(\n{port_arguments}\n);'
    updated_content = re.sub(header_pattern, new_header, module_content, flags=re.DOTALL)
    return updated_content


def remove_original_internal_variables(module_content, internal_variables):
    for var in internal_variables:
        data_type, var_name = var.split(' ', 1)

        pattern = r'^\s*' + re.escape(data_type) + r'\s+(?:.*?\b' + re.escape(
            var_name) + r'\b\s*(?:\[[^\]]*\]\s*)?(?:,\s*[^;]*)?\s*;)'
        module_content = re.sub(pattern, '', module_content, flags=re.MULTILINE)

    return module_content

def remove_typedef_variables(module):
    get_names_pattern = 'typedef\s+[\s\S]*?}\s*(\w+);'
    matches = re.findall(get_names_pattern, module)
    for match in matches:
        find_variables_pattern = f'^\s*{match}\s+[^;]+;'
        module = re.sub(find_variables_pattern, '', module, flags=re.MULTILINE)

    return module

def process_module_complete(module_content):
    internal_vars = obtain_internal_variables(module_content)
    port_args = extract_ports_and_merge(module_content, internal_vars)

    updated_module = update_module_header(module_content, port_args)
    updated_module = remove_original_internal_variables(updated_module, internal_vars)
    updated_module = remove_typedef_variables(updated_module)

    lines = updated_module.split('\n')
    cleaned_lines = [line for line in lines if line.strip()]

    return '\n'.join(cleaned_lines)