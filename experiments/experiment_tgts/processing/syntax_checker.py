from utils import utils

class SyntaxChecker:
    """Handles syntax checking of generated code"""

    @staticmethod
    def check(code: str) -> str:
        """Check syntax of generated code"""
        if not code:
            return "NO_CODE_GENERATED"
        return utils.check_code_syntax(code=code)

    @staticmethod
    def validate_blocks_exist(has_blocks: bool) -> str:
        """Validate if module has blocks to process"""
        if not has_blocks:
            return "NO_SEQ_OR_COMB_BLOCK_FOUND"
        return None