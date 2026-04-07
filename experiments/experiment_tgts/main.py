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

        module ='''module case_simple_example (
    input  logic       addr,      // 1-bit address
    input  logic       sub_op,    // 1-bit sub-operation
    input  logic [1:0] mode,      // 2-bit mode for casex
    input  logic       data,
    output logic       result
);

    always_comb begin
        case (addr)
            1'b0: begin
                // Nested case statement
                case (sub_op)
                    1'b0:   result = data;
                    1'b1:   result = ~data;
                endcase
            end
            
            1'b1: begin
                // casex with don't-care and range value (comma-separated)
                casex (mode)
                    2'b0x,           // Range: matches 2'b00 or 2'b01
                    2'b1x: begin     // Range: matches 2'b10 or 2'b11
                        result = data & sub_op;
                    end
                    default: result = 1'b0;
                endcase
            end
        endcase
    end

endmodule'''

        modules = [module]

        # Run experiment
        controller = ExperimentController(
            model_name=args.model,
            output_filepath=output_filepath,
            ollama_settings = OLLAMA_SETTINGS
        )

        controller.run(modules)

if __name__ == "__main__":
    main()