from clock_reset_initialize import generate_reset_initial_info, generate_clock_initial_section
from generate_bindings import generate_dut_assert_sections
from module_info_extractor import get_module_name, get_port_signals, get_triggers, normalize_ports_with_range, extract_internal_variables_names
from stimuli_section_generator import generate_blocks

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



def generate_full_instantiate_section(full_type_signals: list, clk_initialization_section:str, reset_initialization_section:str, dut_assert_sections: dict):
    '''
    Generates the common signals, completion tracking signal and the binding section.
    :param full_type_signals:
    :param dut_assert_sections:
    :return:
    '''

    common_signals = [signal.replace("input ", "").replace("output ", "") for signal in full_type_signals]
    common_signals_section = '\n'.join([f'\t{signal};' for signal in common_signals])
    template = (f'\t\n//Common signals\n'
                f'{common_signals_section}'
                f'\n\tint blocks_done = 0;\n'
                f'\n'
                f'{clk_initialization_section}\n'
                f'{reset_initialization_section}\n'
                f"{dut_assert_sections['dut_section']}\n"
                f"{dut_assert_sections['assert_section']}")

    return template

def generate_end_simulation_trigger():
    '''
    Includes the finish of the simulation for when all the stimuli blocks are finished.
    :return:
    '''
    return (f'\t// ====================================================\n'
            f'\t// SIMULATION END TRIGGER\n'
            f'\t// ====================================================\n'
            f'\n'
            f'\tinitial begin: simulation_end_monitor_trigger\n'
            f'\t\t// Wait until both test suites are done\n'
            f'\t\twait(blocks_done == (TOTAL_TEST_BLOCKS));\n'
            f'\n'
            f'\t\t// Extra time for any final assertions to trigger\n'
            f'\t\t#(POST_COMPLETION_DELAY);\n'
            f'\n'
            f'\t\t$display("[%0t] Simulation complete - $finish called", $time);\n'
            f'\t\t$finish;\n'
            f'\tend\n\n')

def generate_timeout_protection():
    '''
    Includes an end trigger in case the simulation enters an infinite loop because of the DUT or assert design.
    :return:
    '''
    return (f'\t// ====================================================\n'
            f'\t// TIMEOUT PROTECTION\n'
            f'\t// ====================================================\n'
            f'\n'
            f'\tinitial begin: timeout_protection_trigger\n'
            f'\t\t#(TIMEOUT_LIMIT);\n'
            f'\t\t$display("❌ TIMEOUT ERROR at %0t", $time);\n'
            f'\t\t$display("   Timeout limit: %0d", TIMEOUT_LIMIT);\n'
            f'\t\t$finish;\n'
            f'\tend\n\n')


#######################################################################


def generate_clk_reset_initialization(clk_signal: str, rst_signal: str, rst_trigger:str)-> tuple:
    '''
    Generates the clock and reset initialization sections if there are clocks and|or reset sections
    :param clk_signal:
    :param rst_signal:
    :param rst_trigger:
    :param clk_half_period:
    :return:
    '''
    initial_reset_section = ''
    initial_clock_section = ''

    if rst_signal:
        initial_reset_section = generate_reset_initial_info(reset_trigger=rst_trigger, reset_signal=rst_signal)
    if clk_signal:
        initial_clock_section = generate_clock_initial_section(
            clock_signal=clk_signal
        )

    return initial_clock_section, initial_reset_section


def generate_testbench(timescale: str, dut_module: str, assert_module: str, CLK_HALF_PERIOD: int, RESET_DELAY: int, TIMEOUT_LIMIT: int, COMB_TOTAL_TESTS: int, SEQ_TOTAL_TESTS: int, POST_COMPLETION_DELAY: int):

    # Get the signals from the dut module ports list.
    signals = get_port_signals(module=dut_module)

    # Finds the triggers for clock and trigger if they exist.
    clk_trigger, rst_trigger = get_triggers(module=dut_module)

    clk_signal = clk_trigger.split(' ')[-1] if clk_trigger else ''
    rst_signal = rst_trigger.split(' ')[-1] if rst_trigger else ''

    dut_module_name = get_module_name(module=dut_module)

    assert_module_name = get_module_name(module=assert_module)

    # Adds the type of signal and input|output to those signals that don't have it.
    full_type_signals = normalize_ports_with_range(input_signals=signals)

    clk_initialization_section, reset_initialization_section = generate_clk_reset_initialization(clk_signal = clk_signal, rst_signal = rst_signal, rst_trigger = rst_trigger)

    internal_dut_variables_names = extract_internal_variables_names(dut_module=dut_module)

    dut_assert_sections = generate_dut_assert_sections(
        signals=full_type_signals,
        dut_module_name=dut_module_name,
        assert_module_name=assert_module_name,
        internal_dut_variables_names=internal_dut_variables_names)

    full_instantiate_section = generate_full_instantiate_section(full_type_signals=full_type_signals,
                                                                 clk_initialization_section=clk_initialization_section,
                                                                 reset_initialization_section=reset_initialization_section,
                                                                 dut_assert_sections=dut_assert_sections)

    stimulus_block_section, total_test_blocks = generate_blocks(full_type_signals = full_type_signals, dut_module =  dut_module, test_module = assert_module, clock_signal = clk_signal, reset_signal = rst_signal)

    testbench_header = generate_testbench_header(CLK_HALF_PERIOD = CLK_HALF_PERIOD,
        RESET_DELAY = RESET_DELAY,
        TIMEOUT_LIMIT = TIMEOUT_LIMIT,
        COMB_TOTAL_TESTS = COMB_TOTAL_TESTS,
        SEQ_TOTAL_TESTS = SEQ_TOTAL_TESTS,
        POST_COMPLETION_DELAY = POST_COMPLETION_DELAY,
        total_test_blocks = total_test_blocks)

    end_simulation_trigger = generate_end_simulation_trigger()

    timeout_protection = generate_timeout_protection()

    template = (f'{timescale}\n\n'
                f'{testbench_header}\n'
                f'{full_instantiate_section}\n'
                f'{stimulus_block_section}\n'
                f'{end_simulation_trigger}\n'
                f'{timeout_protection}\n'
                f'endmodule')

    return template