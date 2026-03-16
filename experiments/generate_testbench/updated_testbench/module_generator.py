from clock_reset_initialize import generate_reset_initial_info, generate_clock_initial_section
from generate_bindings import generate_dut_assert_sections
from module_info_extractor import get_module_name, get_port_signals, get_triggers, normalize_ports_with_range




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

def generate_full_instantiate_section(full_type_signals: list, dut_assert_sections: dict):
    '''
    Generates the common signals, completion tracking signal and the binding section.
    :param full_type_signals:
    :param dut_assert_sections:
    :return:
    '''
    section = '\t\n//Common signals\n'
    common_signals = [signal.replace("input ", "").replace("output ", "") for signal in full_type_signals]
    section += '\n'.join([f'\t{signal};' for signal in common_signals])
    section +='\tint blocks_done = 0;\n\n'

    return section + '\n\n' + dut_assert_sections['dut_section'] + '\n' + dut_assert_sections['assert_section']

def generate_end_simulation_trigger():
    '''
    Includes the finish of the simulation for when all the stimuli blocks are finished.
    :return:
    '''
    return (f'\t// ====================================================\n'
            f'\t// SIMULATION END TRIGGER\n'
            f'\t// ====================================================\n'
            f'\n'
            f'\tinitial begin: monitor\n'
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
            f'\tinitial begin: timeout\n'
            f'\t\t#(TIMEOUT_LIMIT);\n'
            f'\t\t$display("❌ TIMEOUT ERROR at %0t", $time);\n'
            f'\t\t$display("   Timeout limit: %0d", TIMEOUT_LIMIT);\n'
            f'\t\t$finish;\n'
            f'\tend\n\n')

dut_module = row['original_code']

assert_module = row['generated_code']

dut_module_name = get_module_name(module=dut_module)

assert_module_name = get_module_name(module=assert_module)

# Get the signals from the dut module ports list.
signals = get_port_signals(module=dut_module)

#Finds the triggers for clock and trigger if they exist.
clk_trigger, rst_trigger = get_triggers(module=dut_module)

clk_signal = clk_trigger.split(' ')[-1] if clk_trigger else ''
rst_signal = rst_trigger.split(' ')[-1] if rst_trigger else ''


# Adds the type of signal and input|output to those signals that don't have it.
full_type_signals = normalize_ports_with_range(input_signals=signals)

#######################################################################

initial_reset_section = ''
initial_clock_section = ''

if rst_signal:
    initial_reset_section = generate_reset_initial_info(reset_trigger=rst_trigger, reset_signal=rst_signal)
if clk_signal:
    initial_clock_section = generate_clock_initial_section(
                clock_signal=clk_signal,
                clock_period=CLK_HALF_PERIOD
    )

dut_assert_sections = generate_dut_assert_sections(
    signals=full_type_signals,
    dut_module_name=dut_module_name,
    assert_module_name=assert_module_name)


#It needs to be obtained at the end because total_test_blocks has to be calculated. For that, it's necessary to count how many blocks there are.
testbench_header = generate_testbench_header(CLK_HALF_PERIOD = CLK_HALF_PERIOD,
RESET_DELAY = RESET_DELAY,
TIMEOUT_LIMIT = TIMEOUT_LIMIT,
COMB_TOTAL_TESTS = COMB_TOTAL_TESTS,
SEQ_TOTAL_TESTS = SEQ_TOTAL_TESTS,
POST_COMPLETION_DELAY = POST_COMPLETION_DELAY,
total_test_blocks = total_test_blocks)



full_instantiate_section = generate_full_instantiate_section(full_type_signals=full_type_signals, dut_assert_sections=dut_assert_sections)


#TESTBENCH HEADER = testbench_header
#COMMON SIGNALS + BIND = generate_full_instantiate_section