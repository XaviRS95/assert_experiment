from .block_extractor import BlockExtractor
from utils.regex_utils import sv_parsing


class ModuleProcessor:
    """Processes a module to extract its structure"""

    def __init__(self, code: str):
        self.code = code
        self.block_extractor = BlockExtractor(code)

    def process(self):
        """Process module and return its components"""
        blocks = self.block_extractor.extract_all_blocks()

        # If no blocks to process, return early
        if not (blocks['comb'] or blocks['seq']):
            return {'has_blocks': False}

        header_and_vars = sv_parsing.extract_module_interface_and_decls(
            code=self.block_extractor.clean_code,
            comb_blocks=blocks['comb'],
            seq_blocks=blocks['seq'],
            func_blocks=blocks['functions']
        )


        return {
            'has_blocks': True,
            'clean_code': self.block_extractor.clean_code,
            'comb_blocks': blocks['comb'],
            'seq_blocks': blocks['seq'],
            'func_blocks': blocks['functions'],
            'module_name': header_and_vars['header']['module_name'],
            'parameters': header_and_vars['header']['parameters'],
            'ports': header_and_vars['header']['ports'],
            'inner_vars': header_and_vars['inner_vars']
        }