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

def extract_sensitivity_list_variables(dut_module: str)-> list:

    block_pattern = r'(always_ff|always_latch)\s*@\s*\((.*?)\)'
    raw_lists = re.findall(block_pattern, dut_module, re.DOTALL)

    all_elements = []

    for _, list_content in raw_lists:
        # 2. Split by 'or' OR ',' (with optional surrounding whitespace)
        # The '|' in the regex acts as the "OR" operator
        elements = re.split(r'\s+or\s+|\s*,\s*', list_content.strip())
        all_elements.extend(elements)

    final_sensitivity_list = list(set(all_elements))
    # Return unique elements, cleaned of any trailing/leading whitespace
    return final_sensitivity_list

def extract_property_details(test_module: str)-> list:
    # 1. Regex to find property blocks
    # Captures: Name, Activation, and the Body of the property
    prop_pattern = r'property\s+\w+;.*?@\((.*?)\)(.*?)endproperty'
    matches = re.finditer(prop_pattern, test_module, re.DOTALL)

    # SystemVerilog keywords/built-ins to ignore when extracting variables
    reserved = {'posedge', 'negedge', 'disable', 'iff', 'past', 'input', 'logic'}

    results = []

    for match in matches:
        activation = match.group(2).strip()
        body = match.group(3).strip()

        # 2. Extract variable names from the body
        # Matches words starting with a letter, ignoring numbers and special chars
        # We look for words like 'value', 'en', 'rst'
        all_words = re.findall(r'\b[a-zA-Z_]\w*\b', body)

        # Filter out keywords and the $ from $past
        variables = set()
        for word in all_words:
            if word.lower() not in reserved:
                variables.add(word)

        results.append({
            "activation": activation,
            "variables": sorted(list(variables))
        })

    return results

def group_sequential_tests(dut_module:str, test_module: str) -> dict:

    sensitivity_list_variables = extract_sensitivity_list_variables(dut_module=dut_module)

    property_details = extract_property_details(test_module=test_module)

    grouped_variables_by_testing = dict.fromkeys(sensitivity_list_variables, [])

    for property in property_details:
        if property['activation'] in grouped_variables_by_testing:
            grouped_variables_by_testing[property['activation']].append(property['variables'])

    return grouped_variables_by_testing


print(group_sequential_tests(dut_module=dut_module, test_module=test_module))



def get_sensitivity_list(test_module: str)-> tuple:
    PATTERN = r'@\((.*?)\)'
    combinational_sensitivity_list = []
    sequential_sensitivity_list = []

    # Find all matches
    matches = re.findall(PATTERN, test_module)

    for event in matches:
        if 'posedge' in event or 'negedge' in event:
            sequential_sensitivity_list.append(event.strip())
        else:
            combinational_sensitivity_list.append(event.strip())

    return combinational_sensitivity_list, sequential_sensitivity_list


def generate_sequential_blocks(variables_per_sensitivity: dict, )-> list:

    sequential_blocks = []

    #get variable memory stimulations.
    #stimulus = get_stimulus(variables_per_sensitivity.keys())
    stimulus = ''


    for key, value in variables_per_sensitivity.items():
        sequential_template = (f'\tinitial begin'
                               f'\t\t// Wait for reset to complete'
                               f'\t\t#(RESET_DELAY + 5);'
                               f'\t\tfor(int i=0; i<SEQ_TOTAL_TESTS; i++) begin'
                               f'\t\t\t@({key});'
                               f'{stimulus}'
                               f'\t\tend'
                               f'\t\tblocks_done = blocks_done + 1;'
                               f'\tend'
                               f''
                               f''
                               f'')


def generate_blocks():
    pass




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
