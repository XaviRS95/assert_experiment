from experiments.experiment_tgts.config.arguments import parse_arguments, get_output_filename
from experiments.experiment_tgts.config.file_handling import initialize_csv_file
from experiments.experiment_tgts.core.experiment_controller import ExperimentController
from utils.file_handling import file_handling
from experiments import ollama_settings
from utils.utils import get_model_info
def main():
    """Main entry point for experiment 3"""

    MAX_VRAM = 48

    OLLAMA_SETTINGS = {
    }

    # Parse arguments
    args = parse_arguments()
    output_filepath = get_output_filename(args)

    model_info = get_model_info(model_name=args.model)
    # model_vram_results = ollama_settings.calculate_ollama_vram(raw_text = model_info, context_length = OLLAMA_SETTINGS['num_ctx'])
    # OLLAMA_SETTINGS['num_gpu'] = model_vram_results['Layers']

    if True:

        # Initialize output file
        initialize_csv_file(output_filepath)

        # Read modules
        modules = file_handling.read_modules_file(args.path)

        # Run experiment
        controller = ExperimentController(
            model_name=args.model,
            output_filepath=output_filepath,
            ollama_settings = OLLAMA_SETTINGS
        )

        controller.run(modules)

if __name__ == "__main__":
    main()