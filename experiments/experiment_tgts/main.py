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

    modules = ['''
    module ethernet_crc32_pipelined (
    input logic clk,
    input logic rst_n,
    input logic [7:0] data_in,
    input logic data_valid,
    input logic start_frame,
    input logic end_frame,
    output logic [31:0] crc_out,
    output logic crc_valid,
    output logic crc_error
);

//-------------------------------------------------------------------------
// State enumeration
//-------------------------------------------------------------------------
typedef enum logic [1:0] {
    IDLE,
    CALC,
    FINALIZE,
    CHECK
} state_t;

//-------------------------------------------------------------------------
// CRC32 Constants (Ethernet polynomial: 0x04C11DB7)
//-------------------------------------------------------------------------
parameter CRC32_POLY = 32'h04C11DB7;
parameter CRC32_INIT = 32'hFFFFFFFF;
parameter CRC32_RESIDUE = 32'hDEBB20E3;

//-------------------------------------------------------------------------
// Sequential logic: State and pipeline registers
//-------------------------------------------------------------------------
state_t state_reg, state_next;
logic [31:0] crc_reg, crc_next;
logic [31:0] crc_pipe1, crc_pipe2;
logic [7:0] data_pipe1, data_pipe2;
logic valid_pipe1, valid_pipe2;
logic start_pipe1, start_pipe2;
logic end_pipe1, end_pipe2;
logic [2:0] byte_count_reg, byte_count_next;

always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        state_reg <= IDLE;
        crc_reg <= CRC32_INIT;
        crc_pipe1 <= 32'b0;
        crc_pipe2 <= 32'b0;
        data_pipe1 <= 8'b0;
        data_pipe2 <= 8'b0;
        valid_pipe1 <= 1'b0;
        valid_pipe2 <= 1'b0;
        start_pipe1 <= 1'b0;
        start_pipe2 <= 1'b0;
        end_pipe1 <= 1'b0;
        end_pipe2 <= 1'b0;
        byte_count_reg <= 3'b0;
    end else begin
        state_reg <= state_next;
        crc_reg <= crc_next;
        byte_count_reg <= byte_count_next;

        // Pipeline stage 1
        crc_pipe1 <= crc_reg;
        data_pipe1 <= data_in;
        valid_pipe1 <= data_valid;
        start_pipe1 <= start_frame;
        end_pipe1 <= end_frame;

        // Pipeline stage 2
        crc_pipe2 <= crc_pipe1;
        data_pipe2 <= data_pipe1;
        valid_pipe2 <= valid_pipe1;
        start_pipe2 <= start_pipe1;
        end_pipe2 <= end_pipe1;
    end
end

//-------------------------------------------------------------------------
// CRC32 calculation function (combinational)
//-------------------------------------------------------------------------
function automatic [31:0] crc32_byte;
    input [31:0] crc;
    input [7:0] data;
    logic [31:0] new_crc;
    logic [31:0] poly;
begin
    new_crc = crc ^ {24'b0, data};
    poly = CRC32_POLY;

    for (int i = 0; i < 8; i++) begin
        if (new_crc[0])
            new_crc = (new_crc >> 1) ^ poly;
        else
            new_crc = (new_crc >> 1);
    end

    crc32_byte = new_crc;
end
endfunction

//-------------------------------------------------------------------------
// Pipeline stage 1 combinational logic
//-------------------------------------------------------------------------
logic [31:0] crc_stage1_out;
logic [31:0] crc_stage1_init;
logic stage1_valid;

always_comb begin
    // Stage 1 CRC calculation
    if (start_pipe1)
        crc_stage1_init = CRC32_INIT;
    else
        crc_stage1_init = crc_pipe1;

    if (valid_pipe1)
        crc_stage1_out = crc32_byte(crc_stage1_init, data_in);
    else
        crc_stage1_out = crc_stage1_init;

    stage1_valid = valid_pipe1;
end

//-------------------------------------------------------------------------
// Pipeline stage 2 combinational logic
//-------------------------------------------------------------------------
logic [31:0] crc_stage2_out;
logic [31:0] crc_stage2_final;
logic stage2_start, stage2_end;

always_comb begin
    // Stage 2 CRC calculation
    if (start_pipe2)
        crc_stage2_out = crc32_byte(CRC32_INIT, data_pipe2);
    else if (valid_pipe2)
        crc_stage2_out = crc32_byte(crc_pipe2, data_pipe2);
    else
        crc_stage2_out = crc_pipe2;

    // Final XOR
    crc_stage2_final = ~crc_stage2_out;

    stage2_start = start_pipe2;
    stage2_end = end_pipe2;
end

//-------------------------------------------------------------------------
// Main FSM combinational logic
//-------------------------------------------------------------------------
always_comb begin
    state_next = state_reg;
    crc_next = crc_reg;
    byte_count_next = byte_count_reg;
    crc_out = 32'b0;
    crc_valid = 1'b0;
    crc_error = 1'b0;

    case (state_reg)
        IDLE: begin
            if (start_frame) begin
                state_next = CALC;
                crc_next = CRC32_INIT;
                byte_count_next = 3'b0;
            end
        end

        CALC: begin
            // Update CRC with pipelined output
            crc_next = crc_stage2_out;

            if (valid_pipe2)
                byte_count_next = byte_count_reg + 1;

            if (end_pipe2) begin
                state_next = FINALIZE;
                crc_next = crc_stage2_final;
            end
        end

        FINALIZE: begin
            crc_out = crc_reg;
            crc_valid = 1'b1;
            state_next = CHECK;
        end

        CHECK: begin
            // Check against expected residue
            if (crc_reg == CRC32_RESIDUE)
                crc_error = 1'b0;
            else
                crc_error = 1'b1;

            if (!data_valid)
                state_next = IDLE;
        end
    endcase
end

endmodule
    ''']

    # Run experiment
    controller = ExperimentController(
        model_name=args.model,
        output_filepath=output_filepath
    )

    controller.run(modules)

if __name__ == "__main__":
    main()