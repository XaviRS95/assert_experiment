from experiments.experiment_tgts.config.arguments import parse_arguments, get_output_filename
from experiments.experiment_tgts.config.file_handling import initialize_csv_file
from experiments.experiment_tgts.core.experiment_controller import ExperimentController
from utils.file_handling import file_handling

def main():
    """Main entry point for experiment 3"""

    # Parse arguments
    args = parse_arguments()
    output_filepath = get_output_filename(args)

    # Initialize output file
    initialize_csv_file(output_filepath)

    # Read modules
    modules = file_handling.read_modules_file(args.path)

    # Run experiment
    controller = ExperimentController(
        model_name=args.model,
        output_filepath=output_filepath
    )

    controller.run(modules)

if __name__ == "__main__":
    main()