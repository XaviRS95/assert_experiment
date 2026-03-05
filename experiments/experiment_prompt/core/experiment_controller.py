import time

from utils.tracking.results_writer import ResultsWriter
from utils.tracking.statistics import ExperimentStatistics
from utils.tracking.token_tracker import TokenTracker
from utils.utils import query_ollama, check_code_syntax

from prompts.prompt_experiments import experiment1_prompt, experiment2_prompt

class ExperimentController:
    """Controls the flow of experiment 3"""

    def __init__(self, model_name: str, output_filepath: str, experiment_mode: int):
        self.model_name = model_name
        self.output_filepath = output_filepath
        self.experiment_mode = experiment_mode
        self.stats = ExperimentStatistics()
        self.token_tracker = TokenTracker()

    def run(self, modules: list):
        """Run the experiment on all modules"""

        with ResultsWriter(self.output_filepath) as writer:
            for i, module_code in enumerate(modules):
                result = self._process_single_module(module_code, i, len(modules))
                self._write_result(writer, module_code, result)
                self._update_statistics(result)
                #Re-start the token tracker
                self.token_tracker = TokenTracker()

        self._print_summary()

    def _process_single_module(self, module_code: str, index: int, total: int):
        """Process a single module"""
        print(f'Module #{index + 1} out of {total} in Experiment #{self.experiment_mode} in model {self.model_name}')
        print(f"Original code: \n{module_code}\n")

        time1 = time.time()
        if self.experiment_mode == 1:
            prompt = experiment1_prompt(module=module_code)
        else:
            prompt = experiment2_prompt(module=module_code)

        model_response = query_ollama(prompt=prompt, model=self.model_name, code_call=True)

        elapsed_time = time.time() - time1

        if model_response['sv_code'] != 'NO_CODE':

            # Track tokens
            self.token_tracker.save_tokens(
                model_response['prompt_tkns'],
                model_response['response_tkns']
            )

            print(f'Generated testing module: \n{model_response["sv_code"]}\n')

            compiler_output = check_code_syntax(code=model_response['sv_code'])

            return self._create_result(module_code, model_response['sv_code'], compiler_output, elapsed_time)
        else:
            return self._create_result(module_code, '', 'NO_SV_MODULE_FOUND', elapsed_time)



    def _create_result(self, original_code: str, generated_code: str,
                       compiler_output: str, start_time: float) -> dict:
        """Create result dictionary"""
        elapsed = time.time() - start_time
        tokens = self.token_tracker.get_totals()

        return {
            'original_code': original_code,
            'generated_code': generated_code or '',
            'compiler_output': compiler_output,
            'elapsed_time': elapsed,
            'prompt_tkns': tokens['prompt_tkns'],
            'response_tkns': tokens['response_tkns']
        }

    def _write_result(self, writer: ResultsWriter, original_code: str, result: dict):
        """Write result to CSV"""
        writer.write_result(
            original_code,
            result['generated_code'],
            result['compiler_output'],
            result['elapsed_time'],
            result['prompt_tkns'],
            result['response_tkns']
        )

        print(f"Status: {result['compiler_output']} | Time: {result['elapsed_time']:.2f}s")
        print(f"Total Prompt Tokens: {result['prompt_tkns']}")
        print(f"Total Response Tokens: {result['response_tkns']}")

        if result['compiler_output'] == "OK":
            self.stats.increment_correct()

    def _update_statistics(self, result: dict):
        """Update experiment statistics"""
        self.stats.increment_total()

    def _print_summary(self):
        """Print experiment summary"""
        summary = self.stats.get_summary()
        print(f"\nExperiment Complete!")
        print(f"Correctly generated: {summary['correct']}/{summary['total']}")
        print(f"Success rate: {summary['success_rate']:.2f}%")