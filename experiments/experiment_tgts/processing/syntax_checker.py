from utils import utils
from utils.regex_utils.module_assert_check import check_module_has_asserts_properties
class SyntaxChecker:
    """Handles syntax checking of generated code"""

    @staticmethod
    def check(code: str) -> str:
        """Check syntax of generated code"""
        if not code:
            return "NO_CODE_GENERATED"
        else:
            if not check_module_has_asserts_properties(module=code):
                return 'MODULE_WITHOUT_ASSERTS'
            else:
                return utils.check_code_syntax(code=code)

    @staticmethod
    def validate_blocks_exist(has_blocks: bool) -> str:
        """Validate if module has blocks to process"""
        if not has_blocks:
            return "NO_SEQ_OR_COMB_BLOCK_FOUND"
        return None