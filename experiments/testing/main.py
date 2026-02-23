from module_info_extractor import *
from module_generator import *

code_module= """
module seq_case71(
    input logic clk, reset,
    output logic [1:0] count
);
    always_ff @(posedge clk or negedge reset) begin
        if(!reset)
            count <= 2'b00;
        else
            case(count)
                2'b00: count <= 2'b01;
                2'b01: count <= 2'b10;
                2'b10: count <= 2'b11;
                2'b11: count <= 2'b00;
                default: count <= 2'b00;
            endcase
    end
endmodule
"""

test_module="""
module seq_case71_asserts  (
input logic clk, 
reset,
input logic [1:0] count);

	property lkcknhahejcmkjgookebmjjmmacghmjf;
	    @(posedge clk) disable iff(!reset) ((count == 2'b00)) |=> (count == 2'b01);
	endproperty
	assert property (lkcknhahejcmkjgookebmjjmmacghmjf);

	property ehiilmflnhejkhboaliecmkhhimflbhe;
	    @(posedge clk) disable iff(!reset) ((count == 2'b01)) |=> (count == 2'b10);
	endproperty
	assert property (ehiilmflnhejkhboaliecmkhhimflbhe);

	property kjhbapemmdidknbppgcieolbkbeoaaka;
	    @(posedge clk) disable iff(!reset) ((count == 2'b10)) |=> (count == 2'b11);
	endproperty
	assert property (kjhbapemmdidknbppgcieolbkbeoaaka);

	property bkclmchdnjaikhkiaofnmkgchakeandi;
	    @(posedge clk) disable iff(!reset) ((count == 2'b11)) |=> (count == 2'b00);
	endproperty
	assert property (bkclmchdnjaikhkiaofnmkgchakeandi);

	property lclfbpjcjadikkpebdlopjjjdilcbgoi;
	    @(posedge clk) disable iff(!reset) ((count != 2'b00 && count != 2'b01 && count != 2'b10 && count != 2'b11)) |=> (count == 2'b00);
	endproperty
	assert property (lclfbpjcjadikkpebdlopjjjdilcbgoi);

endmodule
"""

NUM_EXPERIMENTS = 100
CLOCK_PERIOD_NS = 5
INITIAL_RESET_NS = 20

dut_module_name = get_module_name(module=code_module)

assert_module_name = get_module_name(module=test_module)

signals = get_port_signals(module=code_module)

clk_trigger, rst_trigger = get_triggers(module=code_module)

clk_signal = clk_trigger.split(' ')[-1] if clk_trigger else ''
rst_signal = rst_trigger.split(' ')[-1] if rst_trigger else ''

#Adds the type of signal and input|output to those signals that don't have it.
full_type_signals = normalize_ports_with_range(input_signals=signals)

#Extracts only the input signals, leaving the output signals apart.

clock_reset_initial_section = generate_clock_reset_initial_section(
    clock_signal = clk_signal,
    reset_signal = rst_signal,
    clock_period = CLOCK_PERIOD_NS,
    initial_reset_time = INITIAL_RESET_NS
)

dut_assert_sections = genetate_dut_assert_sections(
    signals=full_type_signals,
    dut_module_name=dut_module_name,
    assert_module_name=assert_module_name)

initial_stimuli_variables = generate_signal_stimulus(signals = full_type_signals,
                                                     clock_signal = clk_signal,
                                                     reset_signal = rst_signal)

initial_stimuli_section = generate_initial_stimulus(num_of_tests = NUM_EXPERIMENTS,
                                                    signal_stimulus = initial_stimuli_variables,
                                                    clock_activation = clk_trigger,
                                                    reset_activation = rst_trigger)

full_instantiate_section = generate_full_instantiate_section(clean_signals = full_type_signals,
                                                             dut_section = dut_assert_sections['dut_section'],
                                                             assert_section = dut_assert_sections['assert_section'],
                                                             clock_signal = clk_signal,
                                                             reset_signal = rst_signal)

final_module = generate_final_module(clock_reset_initial_section=clock_reset_initial_section,
                                     instantiate_section=full_instantiate_section,
                                     initial_stimuli_section=initial_stimuli_section)

print(final_module)