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

