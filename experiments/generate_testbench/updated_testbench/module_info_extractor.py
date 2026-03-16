import re

from experiments.experiment_tgts.processing.tgts_extractions.tgts_to_sequential_properties import \
    sequential_properties_from_tgts

dut_module = '''
module case_range_1(input logic clk, rst, en, output logic [3:0] value);
always_ff @(posedge clk or posedge rst) begin
  if (rst) value <= 0;
  else begin
    case(value) inside
      [0:3]: if (en) value <= value + 1;
      [4:7]: if (en) value <= value - 1;
      [8:11]: value <= 4'b0101;
      [12:15]: value <= 0;
    endcase
  end
end
endmodule
'''

test_module = '''
module case_range_1_asserts  (input logic clk, rst, en, input logic [3:0] value);

property kpgfghmoemeckgaoakkmbhjooinkbmkg;
	@(posedge rst) value == 4'b0000;
endproperty
assert property (kpgfghmoemeckgaoakkmbhjooinkbmkg);

property lnhdgpokgdhgkbfabaocidmdmkogjfce;
    @(posedge clk) disable iff(rst) ((value >= 4'd0) && (value <= 4'd3) && (en == 1'b1)) |=> (value == ($past(value) + 1));
endproperty
assert property (lnhdgpokgdhgkbfabaocidmdmkogjfce);

property mifjoipicmkjkcnebgbnhkjofhijnlbm;
    @(posedge clk) disable iff(rst) ((value >= 4'd4) && (value <= 4'd7) && (en == 1'b1)) |=> (value == ($past(value) - 1));
endproperty
assert property (mifjoipicmkjkcnebgbnhkjofhijnlbm);

property doakfoclahnikohmpcpgecihpbmgkjnm;
    @(posedge clk) disable iff(rst) ((value >= 4'd8) && (value <= 4'd11)) |=> (value == 4'b0101);
endproperty
assert property (doakfoclahnikohmpcpgecihpbmgkjnm);

property pkampmbdkjhnkofcbkaeomhcbfcbkllm;
    @(posedge clk) disable iff(rst) ((value >= 4'd12) && (value <= 4'd15)) |=> (value == 4'b0000);
endproperty
assert property (pkampmbdkjhnkofcbkaeomhcbfcbkllm);

endmodule
'''

def extract_sequential_sensitivity_list_variables(dut_module: str)-> list:
    '''
    Identifies the signals used in the sensitivity list of all sequential blocks from the original module.
    :param dut_module:
    :return:
    '''
    block_pattern = r'(always_ff|always_latch)\s*@\s*\((.*?)\)'
    raw_lists = re.findall(block_pattern, dut_module, re.DOTALL)

    all_elements = []

    for _, list_content in raw_lists:
        # 2. Split by 'or' OR ',' (with optional surrounding whitespace)
        # The '|' in the regex acts as the "OR" operator
        elements = re.split(r'\s+or\s+|\s*,\s*', list_content.strip())
        all_elements.extend(elements)

    sequential_sensitivity_list = list(set(all_elements))
    # Return unique elements, cleaned of any trailing/leading whitespace
    return sequential_sensitivity_list

def get_combinational_sensitivity_lists(test_module: str, sequential_sensitivity_list: list)-> tuple:
    '''
    Extracts the sensitivity list from all testing that are combinational (do not rely on clock nor reset activations)
    :param test_module:
    :param sequential_sensitivity_list:
    :return:
    '''
    PATTERN = r'@\((.*?)\)'
    combinational_sensitivity_list = []

    # Find all matches
    matches = re.findall(PATTERN, test_module)

    for event in matches:
        if event not in sequential_sensitivity_list:
            combinational_sensitivity_list.append(event.strip())

    return combinational_sensitivity_list, sequential_sensitivity_list

def group_activations_with_ports_names(test_module: str)-> list:
    '''
    Extracts the sensitivity list that activates each port from all the tests.
    This is crucial to later understand what ports stimulate under what sensitivity lists,
    to build each stimulating testing block.
    :param test_module:
    :return:
    '''
    prop_pattern = r'property\s+\w+;.*?@\((.*?)\)(.*?)endproperty'
    matches = re.finditer(prop_pattern, test_module, re.DOTALL)

    results = []

    for match in matches:
        activation = match.group(1).strip()
        body = match.group(2).strip()

        variables = set()

        #TODO EXTRACT THE PORTS NAMES FROM THE LEFT HAND SIDE AND THE RIGHT HAND SIDE.

        results.append({
            "activation": activation,
            "variables": sorted(list(variables))
        })

    return results

def group_activations_with_signal_names(dut_module:str, test_module: str) -> tuple:
    '''
    Groups the ports with their activation variables.
    :param dut_module:
    :param test_module:
    :return:
    '''

    #All the sequential blocks activation combinations are stored.
    sequential_sensitivity_list_variables = extract_sequential_sensitivity_list_variables(dut_module=dut_module)

    # All the combinations of the combinational blocks activation are stored.
    combinational_sensitivity_lists_variables = get_combinational_sensitivity_lists(test_module = test_module, sequential_sensitivity_list=sequential_sensitivity_list_variables)

    #Groups all the activations with the ports that are involved in that block.
    activations_with_ports_names = group_activations_with_ports_names(test_module=test_module)

    combinational_grouped_variables_by_testing = dict.fromkeys(combinational_sensitivity_lists_variables, [])
    sequential_grouped_variables_by_testing = dict.fromkeys(sequential_sensitivity_list_variables, [])

    for activation in activations_with_ports_names:
        #Check if it's an activation condition previously recognized
        if activation['activation'] in sequential_grouped_variables_by_testing:
            sequential_grouped_variables_by_testing[activation['activation']] += activation['variables']
        elif activation['activation'] in combinational_grouped_variables_by_testing:
            combinational_grouped_variables_by_testing[activation['activation']] = list(set(combinational_grouped_variables_by_testing[activation['activation']]))

    return combinational_grouped_variables_by_testing, sequential_grouped_variables_by_testing

#print(group_activations_with_signal_names(dut_module=dut_module, test_module=test_module))


def generate_combinational_blocks(activations_with_ports: dict) -> list:
    '''

    :param activations_with_ports:
    :return:
    '''
    combinational_blocks = []

    # get variable memory stimulations.
    # stimulus = get_stimulus(variables_per_sensitivity.keys())
    stimulus = ''

    for key, value in activations_with_ports.items():
        sequential_template = (f'\tinitial begin\n'
                               f'\t\t// Wait for reset to complete\n'
                               f'\t\t#(RESET_DELAY + 5);\n'
                               f'\t\tfor(int i=0; i<COMB_TOTAL_TESTS; i++) begin\n'
                               f'\t\t\t@({key});\n'
                               f'{stimulus}'
                               f'\t\tend\n'
                               f'\t\tblocks_done = blocks_done + 1;\n'
                               f'\tend\n')

        combinational_blocks.append(sequential_template)

    return combinational_blocks


def generate_sequential_blocks(activations_with_ports: dict)-> list:
    '''

    :param activations_with_ports:
    :return:
    '''
    sequential_blocks = []

    #get variable memory stimulations.
    #stimulus = get_stimulus(variables_per_sensitivity.keys())
    stimulus = ''


    for key, value in activations_with_ports.items():
        sequential_template = (f'\tinitial begin\n'
                               f'\t\t// Wait for reset to complete\n'
                               f'\t\t#(RESET_DELAY + 5);\n'
                               f'\t\tfor(int i=0; i<SEQ_TOTAL_TESTS; i++) begin\n'
                               f'\t\t\t@({key});\n'
                               f'{stimulus}'
                               f'\t\tend\n'
                               f'\t\tblocks_done = blocks_done + 1;\n'
                               f'\tend\n')

        sequential_blocks.append(sequential_template)

    return sequential_blocks



def generate_blocks():
    combinational_activations, sequential_activations = group_activations_with_signal_names(dut_module = dut_module, test_module = test_module)
    combinational_blocks = "\n\n".join(generate_combinational_blocks(activations_with_ports=combinational_activations))
    sequential_blocks = "\n\n".join(generate_sequential_blocks(activations_with_ports=sequential_activations))

    stimulus_blocks_section = (f'// ====================================================\n'
                               f'// TEST BLOCKS STIMULATIONS\n'
                               f'// ====================================================\n'
                               f'\n'
                               f'// COMBINATIONAL TESTS\n'
                               f'{combinational_blocks}\n'
                               f'\n'
                               f'// SEQUENTIAL TESTS\n'
                               f'{sequential_blocks}\n')

    return stimulus_blocks_section



TIMESCALE = '`timescale 1ns/1ns'
CLK_HALF_PERIOD = 5
RESET_DELAY = 30
TIMEOUT_LIMIT = 20000
COMB_TOTAL_TESTS = 100
SEQ_TOTAL_TESTS = 100
POST_COMPLETION_DELAY = 100
total_test_blocks = 3

#TODO RECUERDA QUE EL RESET NO NECESITA ALWAYS BEGIN, DIRECTAMENTE LO ACTIVAS CADA X Y SOLUCIONADO.

new_testbench_template = f'''
{TIMESCALE}

module tb_coordinated #(
    // Simulation control parameters
    parameter int CLK_HALF_PERIOD = {CLK_HALF_PERIOD},        // Half clock period (for #5 clk = ~clk)
    parameter int RESET_DELAY = {RESET_DELAY},           // Reset duration in time units
    parameter int TIMEOUT_LIMIT = {TIMEOUT_LIMIT},      // Timeout limit in time units
    parameter int COMB_TOTAL_TESTS = {COMB_TOTAL_TESTS},     // Number of combinational tests
    parameter int SEQ_TOTAL_TESTS = {SEQ_TOTAL_TESTS},      // Number of sequential tests
    parameter int POST_COMPLETION_DELAY = {POST_COMPLETION_DELAY}, // Delay after completion before $finish
    parameter int TOTAL_TEST_BLOCKS = {total_test_blocks} //Total number of blocks (sequential and combinational) that need to be tested and wait for finish).
)(
    // No ports needed for top-level testbench
);
    
    // Common signals
    logic clk;
    logic reset;
    logic state_out;
    
    // Completion tracking
    int blocks_done = 0;
    
    // Clock generation - using parameter
    initial begin: clock_gen
        clk = 0;
        forever #(CLK_HALF_PERIOD) clk = ~clk;
    end
    
    // Reset sequence - using parameter
    initial begin: reset_seq
        reset = 1;
        #(RESET_DELAY) reset = 0;
    end
    
    // ====================================================
    // DUT INSTANTIATION
    // ====================================================

    fsm51 dut (
        .clk(clk),
        .reset(reset),
        .state_out(state_out)
    );
    
    // ====================================================
    // ASSERT MODULE BINDING
    // ====================================================
    
    bind fsm51 assert_module assert_inst (
        .clk(clk),
        .reset(reset),
        .state_out(state_out)
    );
    
    // ====================================================
    // TEST BLOCKS STIMULATIONS
    // ====================================================
    
    // COMBINATIONAL TESTS
    initial begin: comb_tests
        // Wait for reset to complete
        #(RESET_DELAY + 5);
        
        for(int i=0; i<COMB_TOTAL_TESTS; i++) begin
            @(*); // Wait for any variable change
            #1;   // Small delay for settling
            // STIMULATE VARIABLES HERE
        end
        
        blocks_done = blocks_done + 1;
    end
    
    // SEQUENTIAL TESTS
    initial begin: seq_tests
        // Wait for reset to complete
        #(RESET_DELAY + 5);
        
        for(int i=0; i<SEQ_TOTAL_TESTS; i++) begin
            @(posedge clk);
                // STIMULATE VARIABLES HERE
        end
        
        blocks_done = blocks_done + 1;
    end
    
    // ====================================================
    // SIMULATION END TRIGGER
    // ====================================================
    
    initial begin: monitor
        // Wait until both test suites are done
        wait(blocks_done == (TOTAL_TEST_BLOCKS));
        
        // Extra time for any final assertions to trigger
        #(POST_COMPLETION_DELAY);
        
        $display("[%0t] Simulation complete - $finish called", $time);
        $finish;
    end
    
    // ====================================================
    // TIMEOUT PROTECTION
    // ====================================================
    initial begin: timeout
        #(TIMEOUT_LIMIT);
        $display("❌ TIMEOUT ERROR at %0t", $time);
        $display("   Timeout limit: %0d", TIMEOUT_LIMIT);
        $finish;
    end
      
endmodule
'''
