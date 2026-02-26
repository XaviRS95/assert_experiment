def run_experiment_for_module(module_code: str, model_name: str) -> dict:
    """
    Orchestrates the entire experiment flow for a single module.
    Returns results dictionary with all metrics and generated code.
    """
    total_prompt_tkns = 0
    total_response_tkns = 0

    # Pre-processing
    clean_code = text_processing.commentless_code(code=module_code)

    # Extract all block types
    blocks = extract_all_blocks(clean_code)

    # Early exit if no relevant blocks
    if not (blocks['seq_blocks'] or blocks['comb_blocks']):
        return {
            'final_module': '',
            'compiler_output': 'NO_SEQ_OR_COMB_BLOCK_FOUND',
            'prompt_tkns': 0,
            'response_tkns': 0
        }

    # Extract module interface
    module_interface = extract_module_interface(clean_code, blocks)

    # Process combinational blocks
    comb_results = comb_processor.process_combinational_blocks(
        clean_comb_blocks=blocks['comb_blocks'],
        parameters=module_interface['parameters'],
        ports=module_interface['ports'],
        inner_vars=module_interface['inner_vars'],
        model_name=model_name
    )
    total_prompt_tkns += comb_results['prompt_tkns']
    total_response_tkns += comb_results['response_tkns']

    # Process sequential blocks
    seq_results = seq_processor.process_sequential_blocks(
        clean_seq_blocks=blocks['seq_blocks'],
        parameters=module_interface['parameters'],
        ports=module_interface['ports'],
        inner_vars=module_interface['inner_vars'],
        model_name=model_name
    )
    total_prompt_tkns += seq_results['prompt_tkns']
    total_response_tkns += seq_results['response_tkns']

    # Assemble final module
    final_module = module_assembler.assemble_assertion_module(
        module_name=module_interface['module_name'],
        parameters=module_interface['parameters'],
        ports=module_interface['ports'],
        inner_vars=module_interface['inner_vars'],
        func_blocks=blocks['func_blocks'],
        immediate_assertions=comb_results['immediate_assertions'],
        sequential_properties=seq_results['sequential_properties']
    )

    # Syntax check
    compiler_output = utils.check_code_syntax(code=final_module)

    return {
        'final_module': final_module,
        'compiler_output': compiler_output,
        'prompt_tkns': total_prompt_tkns,
        'response_tkns': total_response_tkns
    }


def extract_all_blocks(clean_code: str) -> dict:
    """Extract all block types from cleaned code"""
    from ..utils.regex_utils import sv_parsing

    return {
        'comb_blocks': sv_parsing.get_blocks(code=clean_code, pattern=r'always_comb'),
        'seq_blocks': sv_parsing.get_blocks(code=clean_code, pattern=r'always_(?:ff|latch)'),
        'func_blocks': sv_parsing.extract_functions(code=clean_code)
    }


def extract_module_interface(clean_code: str, blocks: dict) -> dict:
    """Extract module interface information"""
    from ..utils.regex_utils import sv_parsing

    header_and_vars = sv_parsing.extract_module_interface_and_decls(
        code=clean_code,
        comb_blocks=blocks['comb_blocks'],
        seq_blocks=blocks['seq_blocks'],
        func_blocks=blocks['func_blocks']
    )

    return {
        'module_name': header_and_vars['header']['module_name'],
        'parameters': header_and_vars['header']['parameters'],
        'ports': header_and_vars['header']['ports'],
        'inner_vars': header_and_vars['inner_vars']
    }