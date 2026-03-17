def generate_testbench_header(CLK_HALF_PERIOD: int,
                              RESET_DELAY: int,
                              TIMEOUT_LIMIT: int,
                              COMB_TOTAL_TESTS: int,
                              SEQ_TOTAL_TESTS: int,
                              POST_COMPLETION_DELAY: int,
                              total_test_blocks: int,

                              ):
    return (f'module tb #(\n'
            f'\t// Simulation control parameters\n'
            f'\tparameter int CLK_HALF_PERIOD = {CLK_HALF_PERIOD},        // Half clock period (for #5 clk = ~clk)\n'
            f'\tparameter int RESET_DELAY = {RESET_DELAY},           // Reset duration in time units\n'
            f'\tparameter int TIMEOUT_LIMIT = {TIMEOUT_LIMIT},      // Timeout limit in time units\n'
            f'\tparameter int COMB_TOTAL_TESTS = {COMB_TOTAL_TESTS},     // Number of combinational tests\n'
            f'\tparameter int SEQ_TOTAL_TESTS = {SEQ_TOTAL_TESTS},      // Number of sequential tests\n'
            f'\tparameter int POST_COMPLETION_DELAY = {POST_COMPLETION_DELAY}, // Delay after completion before $finish\n'
            f'\tparameter int TOTAL_TEST_BLOCKS = {total_test_blocks} //Total number of blocks (sequential and combinational) that need to be tested and wait for finish).\n'
            f')(\n'
            f'\t// No ports needed for top-level testbench\n'
            f');\n')
