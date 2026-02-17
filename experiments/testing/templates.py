def generate_testbench(module_name:str, dut_signals: str, udt_section: str, check_section:str, initial_stimulus):
    TEMPLATE = ("//module top;"
                "   logic clk = 0;",
                "   logic rst_n = 0;",
                "   always #5 clk = ~clk;",
                "   initial #20 rst_n = 1;",
                "",
                f"{generate_assert_section(module_name=module_name)}",
                "",
                f"{}",
                "",
                "",
                "",
                "",
                "",
                "",
                f"{initial_stimulus}",
                "endmodule")

    return TEMPLATE

def generate_udt_section(module_name:str, signal_list: list):

    signals = ''

    for i in range(len(signal_list)):
        signals+=f'\t.{signal_list}({signal_list}){"," if i < len(signal_list) - 1 else ""}\n'

    dut_module = (f'{module_name} dut ('
                  f'{signals}'
                  f');\n')

    return dut_module


def generate_assert_section(module_name: str, signal_list: list):
    signals = ''

    for i in range(len(signal_list)):
        signals += f'\t.{signal_list}({signal_list}){"," if i < len(signal_list) - 1 else ""}\n'

    dut_module = (f'{module_name} assert ('
                  f'{signals}'
                  f');\n')

    return dut_module

def generate_initial_stimulus(num_of_tests:int, signal_stimulus: str, clock_activation:str='', reset_activation:str=''):
    TEMPLATE = (f'\tinitial begin',
                f'\t\t{reset_activation}',
                f'\t\tfor(int i=0; i<{num_of_tests};i++) begin',
                f'\t\t\t{clock_activation}',
                f'{signal_stimulus}',
                f'\t\tend',
                f'\t\t$display("Test complete!");',
                f'\t\t$assertreport;',
                f'\t\t$finish;',
                f'\tend')

    return TEMPLATE