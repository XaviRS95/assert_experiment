from utils import utils
from prompts.prompts_experiment3 import comb_to_tgts_prompt
from utils.tgts_extractions import tgts_to_immediate_asserts
from experiments.experiment3.tracking.token_tracker import TokenTracker
from utils.regex_utils import sv_parsing

class CombinationalAssertionGenerator:
    """Generates assertions for combinational blocks"""

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.token_tracker = TokenTracker()

    def generate_for_blocks(self, comb_blocks: list, parameters: str,
                            ports: str, inner_vars: str) -> dict:
        """Generate assertions for all combinational blocks"""
        all_assertions = []

        for block in comb_blocks:
            block_assertions = self._process_single_block(
                block, parameters, ports, inner_vars
            )
            all_assertions.append(block_assertions)

        token_totals = self.token_tracker.get_totals()

        return {
            'prompt_tkns': token_totals['prompt_tkns'],
            'response_tkns': token_totals['response_tkns'],
            'immediate_assertions': all_assertions
        }

    def _process_single_block(self, block: str, parameters: str,
                              ports: str, inner_vars: str) -> str:
        """Process a single combinational block"""

        headerless_block = sv_parsing.extract_block_content(block=block)

        prompt = comb_to_tgts_prompt(
            parameters=parameters,
            ports=ports,
            inner_vars=inner_vars,
            block=headerless_block
        )

        model_response = utils.query_ollama(
            prompt=prompt,
            model=self.model_name,
            code_call=False
        )

        self.token_tracker.add_tokens(
            model_response.get('prompt_tkns', 0),
            model_response.get('response_tkns', 0)
        )

        immediate_asserts = tgts_to_immediate_asserts.immediate_asserts_from_tgts(
            tgts_rules=model_response['tgts_rules']
        )

        return immediate_asserts