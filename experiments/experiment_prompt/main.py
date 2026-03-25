from experiments.experiment_prompt.core.experiment_controller import ExperimentController
from config import arguments
from utils.file_handling import file_handling
from experiments import ollama_settings
from utils.utils import get_model_info

if __name__ == "__main__":

    MAX_VRAM = 48

    OLLAMA_SETTINGS = {
        "num_ctx": 8192,      # Context window size
        "num_predict": -1,    # Generate until stop token (no limit)
        "num_gpu": 80,        # Offload 80 layers to GPU (adjust based on your model)
        "num_thread": 32,     # Use 32 CPU threads (half of 64 cores)
        "use_mmap": True,     # Memory-map model file for faster loading
        "numa": True,         # Enable NUMA-aware memory allocation
        "temperature": 0.1,   # Low temperature for deterministic outputs
        "seed": 42,           # Fixed seed for reproducibility
        "top_k": 10           # Restrict sampling to top 10 tokens
    }

    # Initialize Argument Parser
    parser = arguments.parse_arguments()

    model_info = get_model_info(model_name=parser.model)
    model_vram_results = ollama_settings.calculate_ollama_vram(raw_text = model_info, context_length = OLLAMA_SETTINGS['num_ctx'])
    OLLAMA_SETTINGS['num_gpu'] = model_vram_results['Layers']

    if model_vram_results['Total Required VRAM (GB)'] * 0.9 <= MAX_VRAM:

        experiment_mode = parser.experiment

        # Generate output filename logic
        if parser.output:
            final_output_path = parser.output
        else:
            # Replicates your original dynamic naming logic
            final_output_path = f"sv_results_{parser.model.replace(':', '_')}_{experiment_mode}.csv"
        file_handling.initialize_csv_file(final_output_path)

        modules = file_handling.read_modules_file(parser.path)

        experiment_controller = ExperimentController(model_name=parser.model, output_filepath=final_output_path, experiment_mode=experiment_mode, ollama_settings=OLLAMA_SETTINGS)

        experiment_controller.run(modules=modules)

    else:
        print('MAXIMUM VRAM REACHED, MODEL WILL NOT BE LOADED IN GPU')
