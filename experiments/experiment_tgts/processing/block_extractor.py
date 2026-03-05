from utils.regex_utils import sv_parsing, text_processing

class BlockExtractor:
    """Extracts different types of blocks from SystemVerilog code"""

    def __init__(self, code: str):
        self.raw_code = code
        self.clean_code = text_processing.commentless_code(code=code)

    def extract_all_blocks(self):
        """Extract all block types from code"""
        return {
            'comb': self.extract_comb_blocks(),
            'seq': self.extract_seq_blocks(),
            'functions': self.extract_functions()
        }

    def extract_comb_blocks(self):
        """Extract combinational always blocks"""
        return sv_parsing.get_blocks(code=self.clean_code, pattern=r'always_comb')

    def extract_seq_blocks(self):
        """Extract sequential always blocks"""
        return sv_parsing.get_blocks(code=self.clean_code, pattern=r'always_(?:ff|latch)')

    def extract_functions(self):
        """Extract function blocks"""
        return sv_parsing.extract_functions(code=self.clean_code)