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
        "num_ctx": 8192,      # Context window size
        "num_predict": -1,    # Generate until stop token (no limit)
        "num_gpu": 80,        # Offload 80 layers to GPU (adjust based on your model)
        "num_thread": 8,     # Use 32 CPU threads (half of 64 cores)
        "use_mmap": True,     # Memory-map model file for faster loading
        "numa": True,         # Enable NUMA-aware memory allocation
        "temperature": 0.1,   # Low temperature for deterministic outputs
        "seed": 42,           # Fixed seed for reproducibility
        "top_k": 10           # Restrict sampling to top 10 tokens
    }

    # Parse arguments
    args = parse_arguments()
    output_filepath = get_output_filename(args)

    model_info = get_model_info(model_name=args.model)
    model_vram_results = ollama_settings.calculate_ollama_vram(raw_text = model_info, context_length = OLLAMA_SETTINGS['num_ctx'])
    OLLAMA_SETTINGS['num_gpu'] = model_vram_results['Layers']

    if model_vram_results['Total Required VRAM (GB)']*0.9 <= MAX_VRAM:

        # Initialize output file
        initialize_csv_file(output_filepath)

        # Read modules
        modules = file_handling.read_modules_file(args.path)

        module = '''
        
module mipi_csi2_receiver (
    input logic clk,
    input logic rst_n,

    // MIPI D-PHY interface
    input logic [3:0] data_lane_p [0:3],      // 4 data lanes
    input logic [3:0] data_lane_n [0:3],
    input logic clk_lane_p,
    input logic clk_lane_n,
    input logic lp_mode,                       // Low power mode indicator

    // Protocol decoding
    output logic [15:0] pixel_data [0:3][0:255], // 4 lanes of pixel data
    output logic [7:0] line_length,
    output logic [15:0] frame_width,
    output logic [15:0] frame_height,
    output logic [15:0] frame_height,
    output logic [3:0] data_type,               // RAW8, RAW10, RGB565, YUV422, etc.
    output logic [1:0] virtual_channel,
    output logic frame_start,
    output logic frame_end,
    output logic line_valid,
    output logic data_valid,

    // Error detection
    output logic ecc_error,
    output logic crc_error,
    output logic sync_error,

    // Statistics
    output logic [31:0] frame_count,
    output logic [31:0] line_count,
    output logic [31:0] byte_count
);

typedef enum logic [4:0] {
    IDLE,
    LP_STATE,
    HS_START,
    SYNC_PATTERN,
    ECC_CHECK,
    PH_HEADER,
    PH_DATA_TYPE,
    PH_WORD_COUNT,
    PH_ECC,
    PAYLOAD_DATA,
    CRC_CHECK,
    LINE_END,
    FRAME_START,
    FRAME_END,
    ERROR_RECOVERY,
    WAIT_HS_TRAIL,
    LP_11_STATE
} state_t;

state_t state, next_state;
logic [31:0] word_count;
logic [15:0] pixel_count [0:3];
logic [7:0] lane_data [0:3];
logic [3:0] lane_align;
logic [5:0] ecc_calc;
logic [5:0] ecc_recv;
logic [15:0] crc_calc;
logic [15:0] crc_recv;
logic [31:0] packet_data [0:255];
logic [2:0] lane_index;
logic sync_detected;
logic [7:0] sync_pattern;

// CSI-2 sync codes
parameter SYNC_CODE = 8'hB8;
parameter BLANKING_CODE = 8'h00;

always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        state <= IDLE;
        word_count <= 32'b0;
        lane_index <= 3'b0;
        pixel_count[0] <= 16'b0;
        pixel_count[1] <= 16'b0;
        pixel_count[2] <= 16'b0;
        pixel_count[3] <= 16'b0;
        frame_count <= 32'b0;
        line_count <= 32'b0;
        byte_count <= 32'b0;
        crc_calc <= 16'hFFFF;

        for (int i = 0; i < 4; i++)
            for (int j = 0; j < 256; j++)
                pixel_data[i][j] <= 16'b0;
    end else begin
        state <= next_state;

        case (state)
            HS_START: begin
                // Deserialize lane data
                for (int i = 0; i < 4; i++) begin
                    lane_data[i] <= {data_lane_p[i], data_lane_n[i]};
                end
            end

            SYNC_PATTERN: begin
                sync_pattern <= lane_data[0];
                sync_detected <= (lane_data[0] == SYNC_CODE);
            end

            PH_HEADER: begin
                packet_data[word_count] <= {lane_data[3], lane_data[2],
                                           lane_data[1], lane_data[0]};
                word_count <= word_count + 1;
            end

            PH_DATA_TYPE: begin
                data_type <= lane_data[0][3:0];
                virtual_channel <= lane_data[0][5:4];
            end

            PH_WORD_COUNT: begin
                word_count <= {lane_data[1], lane_data[0]};
            end

            PH_ECC: begin
                // Calculate ECC (simplified Hamming code)
                ecc_calc <= 6'b0;
                for (int i = 0; i < 24; i++) begin
                    // ECC calculation logic
                end
                ecc_recv <= lane_data[0][5:0];

                if (ecc_calc != ecc_recv)
                    ecc_error <= 1'b1;
            end

            PAYLOAD_DATA: begin
                if (word_count > 0) begin
                    // Distribute data across lanes
                    for (int lane = 0; lane < 4; lane++) begin
                        case (data_type)
                            4'b0010: begin  // RAW10
                                pixel_data[lane][pixel_count[lane]] <=
                                    {lane_data[lane][7:0], 2'b0};
                                pixel_count[lane] <= pixel_count[lane] + 1;
                            end

                            4'b0111: begin  // RGB565
                                pixel_data[lane][pixel_count[lane]] <=
                                    {lane_data[lane*2 +: 16]};
                                pixel_count[lane] <= pixel_count[lane] + 1;
                                lane_index <= lane_index + 1;
                            end

                            4'b1010: begin  // YUV422 8-bit
                                pixel_data[lane][pixel_count[lane]] <=
                                    {lane_data[lane][7:0], lane_data[lane][7:0]};
                                pixel_count[lane] <= pixel_count[lane] + 1;
                            end
                        endcase
                    end

                    word_count <= word_count - 1;
                    byte_count <= byte_count + 4;

                    // Update CRC
                    crc_calc <= crc_calc ^ {lane_data[3], lane_data[2],
                                           lane_data[1], lane_data[0]};
                end
            end

            CRC_CHECK: begin
                crc_recv <= {lane_data[1], lane_data[0]};
                if (crc_calc != crc_recv)
                    crc_error <= 1'b1;
            end

            LINE_END: begin
                line_valid <= 1'b1;
                line_length <= pixel_count[0][7:0];
                line_count <= line_count + 1;

                for (int i = 0; i < 4; i++)
                    pixel_count[i] <= 16'b0;
            end

            FRAME_START: begin
                frame_start <= 1'b1;
                frame_count <= frame_count + 1;
                line_count <= 32'b0;
            end

            FRAME_END: begin
                frame_end <= 1'b1;
                frame_height <= line_count[15:0];
            end
        endcase
    end
end

always_comb begin
    next_state = state;
    data_valid = (state == PAYLOAD_DATA);

    case (state)
        IDLE: begin
            if (!lp_mode) begin
                next_state = LP_STATE;
            end
        end

        LP_STATE: begin
            if (clk_lane_p && !clk_lane_n)  // Clock rising
                next_state = HS_START;
        end

        HS_START: begin
            next_state = SYNC_PATTERN;
        end

        SYNC_PATTERN: begin
            if (sync_detected) begin
                next_state = PH_HEADER;
            end else if (lane_data[0] == BLANKING_CODE) begin
                next_state = LINE_END;
            end else begin
                sync_error <= 1'b1;
                next_state = ERROR_RECOVERY;
            end
        end

        PH_HEADER: begin
            next_state = PH_DATA_TYPE;
        end

        PH_DATA_TYPE: begin
            next_state = PH_WORD_COUNT;
        end

        PH_WORD_COUNT: begin
            next_state = PH_ECC;
        end

        PH_ECC: begin
            if (ecc_error)
                next_state = ERROR_RECOVERY;
            else begin
                case (data_type)
                    4'b0000: next_state = FRAME_START;  // Frame start code
                    4'b0001: next_state = FRAME_END;    // Frame end code
                    4'b0010, 4'b0111, 4'b1010: next_state = PAYLOAD_DATA;
                    default: next_state = WAIT_HS_TRAIL;
                endcase
            end
        end

        PAYLOAD_DATA: begin
            if (word_count == 0)
                next_state = CRC_CHECK;
        end

        CRC_CHECK: begin
            next_state = WAIT_HS_TRAIL;
        end

        LINE_END: begin
            next_state = WAIT_HS_TRAIL;
        end

        FRAME_START: begin
            frame_start <= 1'b0;
            next_state = WAIT_HS_TRAIL;
        end

        FRAME_END: begin
            frame_end <= 1'b0;
            next_state = WAIT_HS_TRAIL;
        end

        WAIT_HS_TRAIL: begin
            if (lp_mode)
                next_state = LP_11_STATE;
        end

        LP_11_STATE: begin
            if (!lp_mode)
                next_state = HS_START;
            else
                next_state = IDLE;
        end

        ERROR_RECOVERY: begin
            if (lp_mode)
                next_state = IDLE;
        end
    endcase
end

endmodule
        
        '''

        modules = [module]


        # Run experiment
        controller = ExperimentController(
            model_name=args.model,
            output_filepath=output_filepath,
            ollama_settings = OLLAMA_SETTINGS
        )

        controller.run(modules)
    else:
        print('MAXIMUM VRAM REACHED, MODEL WILL NOT BE LOADED IN GPU')

if __name__ == "__main__":
    main()