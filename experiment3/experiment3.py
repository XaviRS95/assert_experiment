from prompts.prompts_experiment3 import comb_to_tgts
from utils import utils, regex
from prompts import prompts_experiment3


def experiment3(model_name:str, file_path:str):

    sv_modules = utils.read_code_files(csv_path=file_path)

    for sv_code in sv_modules:
        clean_code = regex.commentless_code(code=sv_code)
        clean_comb_blocks = regex.get_blocks(code=clean_code, pattern=r'always_comb')
        clean_seq_blocks = regex.get_blocks(code=clean_code, pattern=r'always_(?:ff|latch)')
        clean_func_blocks = regex.extract_functions(code=clean_code)
        header_and_vars = regex.extract_header_and_vars(code=clean_code, comb_blocks=clean_comb_blocks,
                                                  seq_blocks=clean_seq_blocks, func_blocks=clean_func_blocks)

        module_name = header_and_vars['header']['module_name']
        parameters = header_and_vars['header']['parameters']
        ports = header_and_vars['header']['ports']
        inner_vars = header_and_vars['inner_and_vars']

        for block in clean_comb_blocks:
            comb_to_tgts_prompt = comb_to_tgts(parameters=parameters, ports=ports, inner_vars=inner_vars, block=block)
            tgts_rules = utils.query_ollama(prompt=comb_to_tgts_prompt, model=model_name, code_call=False)


