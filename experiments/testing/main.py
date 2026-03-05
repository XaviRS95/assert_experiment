from module_info_extractor import *
from module_generator import *

code_module= """
module multi_proto_arbiter (
    input  logic tl_valid_i,
    input  logic axi_awvalid_i,
    input  logic axi_arvalid_i,
    input  logic obi_req_i,
    input  logic [2:0] tl_opcode_i,
    input  logic [1:0] obi_resp_i,
    output logic grant_o,
    output logic deny_o,
    output logic error_o
);

    always_comb begin
        grant_o = 1'b0;
        deny_o  = 1'b0;
        error_o = 1'b0;

        unique case (1'b1)
            tl_valid_i: begin
                unique case (tl_opcode_i)
                    3'b000: grant_o = 1'b1; // Get
                    3'b001, 3'b010: grant_o = 1'b1; // Put
                    default: deny_o = 1'b1;
                endcase
            end

            axi_awvalid_i || axi_arvalid_i: begin
                grant_o = 1'b1;
            end

            obi_req_i: begin
                unique case (obi_resp_i)
                    2'b00: grant_o = 1'b1;
                    2'b10: deny_o = 1'b1;
                    default: error_o = 1'b1;
                endcase
            end

            default: error_o = 1'b1;
        endcase
    end
endmodule
"""

test_module="""
module multi_proto_arbiter_asserts  (input logic tl_valid_i,
input logic axi_awvalid_i,
input logic axi_arvalid_i,
input logic obi_req_i,
input logic [2:0] tl_opcode_i,
input logic [1:0] obi_resp_i,
input logic grant_o,
input logic deny_o,
input logic error_o);

    

    

    always_comb begin
    efbpnigdecknkcpbolcgjbpgmcpfdkjb: assert( (tl_valid_i && tl_opcode_i == 3'b000) ? (grant_o == 1'b1) : 1 )  else $error(""Error in immediate assert efbpnigdecknkcpbolcgjbpgmcpfdkjb"");

ekfjgkhlnjkgkabmbflcoljlnmehmiba: assert( (tl_valid_i && (tl_opcode_i == 3'b001 || tl_opcode_i == 3'b010)) ? (grant_o == 1'b1) : 1 )  else $error(""Error in immediate assert ekfjgkhlnjkgkabmbflcoljlnmehmiba"");

pkfbmbfjanbnkfepobfkfijkdcbfbkha: assert( (tl_valid_i && !(tl_opcode_i == 3'b000 || tl_opcode_i == 3'b001 || tl_opcode_i == 3'b010)) ? (deny_o == 1'b1) : 1 )  else $error(""Error in immediate assert pkfbmbfjanbnkfepobfkfijkdcbfbkha"");

anegpnkdgnjjkchfapbhiapeeploooka: assert( (axi_awvalid_i || axi_arvalid_i) ? (grant_o == 1'b1) : 1 )  else $error(""Error in immediate assert anegpnkdgnjjkchfapbhiapeeploooka"");

aefnnkdkmpdfkglbpfimeocnkfkjaokl: assert( (obi_req_i && obi_resp_i == 2'b00) ? (grant_o == 1'b1) : 1 )  else $error(""Error in immediate assert aefnnkdkmpdfkglbpfimeocnkfkjaokl"");

aihckfbhmldikbgmpmelikkiomejdelk: assert( (obi_req_i && obi_resp_i == 2'b10) ? (deny_o == 1'b1) : 1 )  else $error(""Error in immediate assert aihckfbhmldikbgmpmelikkiomejdelk"");

inmnglnhgbnnkbodbpnanfjlngmljood: assert( (obi_req_i && !(obi_resp_i == 2'b00 || obi_resp_i == 2'b10)) ? (error_o == 1'b1) : 1 )  else $error(""Error in immediate assert inmnglnhgbnnkbodbpnanfjlngmljood"");

jgkclgglkjilkhoabpbpohnfehhgmfge: assert( (!tl_valid_i && !axi_awvalid_i && !axi_arvalid_i && !obi_req_i) ? (error_o == 1'b1) : 1 )  else $error(""Error in immediate assert jgkclgglkjilkhoabpbpohnfehhgmfge"");

    end

    

    endmodule
"""

NUM_EXPERIMENTS = 100
CLOCK_PERIOD_NS = 5
INITIAL_RESET_NS = 20
TIMESCALE = 'timescale 1ns/1ns'

dut_module_name = get_module_name(module=code_module)

assert_module_name = get_module_name(module=test_module)

signals = get_port_signals(module=code_module)

clk_trigger, rst_trigger = get_triggers(module=code_module)

clk_signal = clk_trigger.split(' ')[-1] if clk_trigger else ''
rst_signal = rst_trigger.split(' ')[-1] if rst_trigger else ''

#Adds the type of signal and input|output to those signals that don't have it.
full_type_signals = normalize_ports_with_range(input_signals=signals)

#Extracts only the input signals, leaving the output signals apart.

initial_reset_info = generate_reset_initial_info(reset_trigger = rst_trigger,
                                                 reset_signal = rst_signal,
                                                 initial_reset_time = INITIAL_RESET_NS)

clock_reset_initial_section = generate_clock_reset_initial_section(
    initial_reset_info=initial_reset_info,
    clock_signal = clk_signal,
    reset_signal = rst_signal,
    clock_period = CLOCK_PERIOD_NS
)

dut_assert_sections = genetate_dut_assert_sections(
    signals=full_type_signals,
    dut_module_name=dut_module_name,
    assert_module_name=assert_module_name)


full_instantiate_section = generate_full_instantiate_section(clean_signals = full_type_signals,
                                                             dut_section = dut_assert_sections['dut_section'],
                                                             assert_section = dut_assert_sections['assert_section'],
                                                             clock_signal = clk_signal,
                                                             reset_signal = rst_signal)


initial_stimuli_variables = generate_signal_stimulus(signals = full_type_signals,
                                                     clock_signal = clk_signal,
                                                     reset_signal = rst_signal)

initial_stimuli_section = generate_initial_stimulus(num_of_tests = NUM_EXPERIMENTS,
                                                    signal_stimulus = initial_stimuli_variables,
                                                    clock_activation = clk_trigger)


final_module = generate_final_module(timescale=TIMESCALE,
                                     clock_reset_initial_section=clock_reset_initial_section,
                                     instantiate_section=full_instantiate_section,
                                     initial_stimuli_section=initial_stimuli_section)

print(final_module)