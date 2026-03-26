from utils import utils
from prompts.tgts_experiments import comb_to_tgts_prompt
from experiments.experiment_tgts.processing.tgts_extractions import tgts_to_immediate_asserts
from experiments.experiment_tgts.tracking.token_tracker import TokenTracker
from utils.regex_utils import sv_parsing

class CombinationalAssertionGenerator:
    """Generates assertions for combinational blocks"""

    def __init__(self, model_name: str, ollama_settings: dict):
        self.model_name = model_name
        self.ollama_settings = ollama_settings

    def generate_for_blocks(self, comb_blocks: list, parameters: str,
                            ports: str, inner_vars: str, ) -> dict:
        """Generate assertions for all combinational blocks"""
        all_assertions = []

        prompt_tkns = 0
        response_tkns = 0

        for block in comb_blocks:
            block_processing = self._process_single_block(
                block, parameters, ports, inner_vars
            )

            all_assertions.append(block_processing['immediate_asserts'])

            prompt_tkns += block_processing['prompt_tkns']
            response_tkns += block_processing['response_tkns']


        return {
            'prompt_tkns': prompt_tkns,
            'response_tkns': response_tkns,
            'immediate_assertions': all_assertions
        }

    def _process_single_block(self, block: str, parameters: str,
                              ports: str, inner_vars: str) -> dict:
        """Process a single combinational block"""



        headerless_block = sv_parsing.extract_block_content(block=block)

        input_ports_list = sv_parsing.extract_input_variable_names(variables=ports)
        inner_vars_list = sv_parsing.extract_internal_variable_names(variables=inner_vars)

        variables = {
            'input_ports_list': input_ports_list,
            'inner_vars_list': inner_vars_list
        }

        prompt = comb_to_tgts_prompt(
            parameters=parameters,
            ports=ports,
            inner_vars=inner_vars,
            block=headerless_block
        )

        model_response = utils.query_ollama(
            prompt=prompt,
            model=self.model_name,
            code_call=False,
            ollama_settings=self.ollama_settings
        )

        immediate_asserts = tgts_to_immediate_asserts.concurrent_asserts_from_tgts(
            tgts_rules=model_response['tgts_rules'],
            variables= variables
        )

        return {'immediate_asserts': immediate_asserts,
                'prompt_tkns': model_response['prompt_tkns'],
                'response_tkns': model_response['response_tkns']}