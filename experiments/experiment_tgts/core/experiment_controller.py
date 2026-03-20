import time
from ..processing.module_processor import ModuleProcessor
from ..processing.syntax_checker import SyntaxChecker
from ..core.assertion_generators.comb_assertions import CombinationalAssertionGenerator
from ..core.assertion_generators.seq_assertions import SequentialAssertionGenerator
from ..core.module_assembly.final_assembler import FinalAssembler
from ..tracking.token_tracker import TokenTracker
from ..tracking.statistics import ExperimentStatistics
from ..tracking.results_writer import ResultsWriter
from utils.regex_utils.module_assert_check import check_module_has_asserts_properties

class ExperimentController:
    """Controls the flow of experiment 3"""

    def __init__(self, model_name: str, output_filepath: str):
        self.model_name = model_name
        self.output_filepath = output_filepath
        self.comb_generator = CombinationalAssertionGenerator(model_name)
        self.seq_generator = SequentialAssertionGenerator(model_name)
        self.assembler = FinalAssembler()
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
        print(f'Module #{index + 1} out of {total} in Experiment #3 in model {self.model_name}')
        print(f"Original code: \n{module_code}\n")

        time1 = time.time()

        # Process module structure
        processor = ModuleProcessor(module_code)
        module_info = processor.process()

        # Check if module has blocks to process
        no_blocks_result = SyntaxChecker.validate_blocks_exist(module_info.get('has_blocks', False))
        if no_blocks_result:
            return self._create_result(module_code, None, no_blocks_result, elapsed_time=time.time() - time1)

        # Generate assertions
        comb_results = self.comb_generator.generate_for_blocks(
            module_info['comb_blocks'],
            module_info['parameters'],
            module_info['ports'],
            module_info['inner_vars']
        )

        seq_results = self.seq_generator.generate_for_blocks(
            module_info['seq_blocks'],
            module_info['parameters'],
            module_info['ports'],
            module_info['inner_vars']
        )

        # Track tokens
        self.token_tracker.add_tokens(
            comb_results['prompt_tkns'] + seq_results['prompt_tkns'],
            comb_results['response_tkns'] + seq_results['response_tkns']
        )

        # Assemble final module
        final_module = self.assembler.assemble(module_info, comb_results, seq_results)
        print(f'Generated testing module: \n{final_module}\n')

        elapsed_time = time.time() - time1

        compiler_output = SyntaxChecker.check(final_module)

        return self._create_result(module_code, final_module, compiler_output, elapsed_time=elapsed_time)

    def _create_result(self, original_code: str, generated_code: str,
                       compiler_output: str, elapsed_time: float) -> dict:
        """Create result dictionary"""
        tokens = self.token_tracker.get_totals()

        return {
            'original_code': original_code,
            'generated_code': generated_code or '',
            'compiler_output': compiler_output,
            'elapsed_time': elapsed_time,
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