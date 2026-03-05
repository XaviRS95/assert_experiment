from utils import utils
from prompts.tgts_experiments import seq_to_tgts_prompt
from experiments.experiment_tgts.processing.tgts_extractions import tgts_to_sequential_properties
from utils.regex_utils import sv_parsing
from experiments.experiment_tgts.tracking.token_tracker import TokenTracker


class SequentialAssertionGenerator:
    """Generates assertions for sequential blocks"""

    def __init__(self, model_name: str):
        self.model_name = model_name

    def generate_for_blocks(self, seq_blocks: list, parameters: str,
                            ports: str, inner_vars: str) -> dict:
        """Generate properties for all sequential blocks"""
        all_properties = []

        prompt_tkns = 0
        response_tkns = 0

        for block in seq_blocks:
            block_processing = self._process_single_block(
                block=block,
                parameters=parameters,
                ports=ports,
                inner_vars=inner_vars
            )

            all_properties.append(block_processing['properties'])

            prompt_tkns += block_processing['prompt_tkns']
            response_tkns += block_processing['response_tkns']



        return {
            'prompt_tkns': prompt_tkns,
            'response_tkns': response_tkns,
            'sequential_properties': all_properties
        }

    def _process_single_block(self, block: str, parameters: str,
                              ports: str, inner_vars: str) -> dict:
        """Process a single sequential block"""
        headerless_block = sv_parsing.extract_block_content(block=block)

        sensitivity_list = sv_parsing.extract_sensitivity_list(
            block=block
        )

        prompt = seq_to_tgts_prompt(
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

        properties = tgts_to_sequential_properties.sequential_properties_from_tgts(
            tgts_rules=model_response['tgts_rules'],
            sensitivity_list=sensitivity_list
        )

        return {'properties': properties,
                'prompt_tkns': model_response['prompt_tkns'],
                'response_tkns': model_response['response_tkns']}