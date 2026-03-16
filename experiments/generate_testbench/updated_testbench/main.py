TIMESCALE = '`timescale 1ns/1ns'
CLK_HALF_PERIOD = 5
RESET_DELAY = 30
TIMEOUT_LIMIT = 20000
COMB_TOTAL_TESTS = 100
SEQ_TOTAL_TESTS = 100
POST_COMPLETION_DELAY = 100
total_test_blocks = 3


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


def generate_testbench(dut_module: str, assert_module: str, TIMESCALE: str, CLK_HALF_PERIOD: int, RESET_DELAY: int, TIMEOUT_LIMIT: int, COMB_TOTAL_TESTS: int, SEQ_TOTAL_TESTS: int, POST_COMPLETION_DELAY: int):




