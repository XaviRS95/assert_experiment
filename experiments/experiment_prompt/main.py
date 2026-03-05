from experiments.experiment_prompt.core.experiment_controller import ExperimentController
from config import arguments
from utils.file_handling import file_handling

if __name__ == "__main__":
    # Initialize Argument Parser
    parser = arguments.parse_arguments()

    experiment_mode = parser.experiment

    # Generate output filename logic
    if parser.output:
        final_output_path = parser.output
    else:
        # Replicates your original dynamic naming logic
        final_output_path = f"sv_results_{parser.model.replace(':', '_')}_{experiment_mode}.csv"
    file_handling.initialize_csv_file(final_output_path)

    modules = file_handling.read_modules_file(parser.path)

    experiment_controller = ExperimentController(model_name=parser.model, output_filepath=final_output_path, experiment_mode=experiment_mode)

    experiment_controller.run(modules=modules)