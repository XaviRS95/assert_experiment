

def generate_clock_initial_section(clock_signal:str):
    '''
    Generates the clock instantiation section if it exists.
    :param clock_signal:
    :return:
    '''
    template = (f'\t//Clock generation section:\n'
                f'\tinitial begin: clock_gen\n'
                f'\t\t{clock_signal} = 0;\n'
                f'\t\tforever #(CLK_HALF_PERIOD) {clock_signal} = ~{clock_signal};\n'
                f'\tend\n')

    return template

def generate_reset_initial_info(reset_trigger:str, reset_signal: str)-> str:
    '''
    Generates the Reset sequence generation
    :param reset_trigger:
    :param reset_signal:
    :return:
    '''
    reset_info = {
        'reset_assert_value': "0",
        'reset_deassert_value': "1",
    }

    if "posedge" in reset_trigger:
        reset_info['reset_assert_value'] = "1"
        reset_info['reset_deassert_value'] = "0"

    TEMPLATE = (f'\t//Reset sequence:\n'
                f'\tinitial begin\n'
                f'\t\t{reset_signal} = {reset_info["reset_assert_value"]};\n'
                f'\t\t#(RESET DELAY) {reset_signal} = {reset_info["reset_deassert_value"]} ;\n'
                f'\tend\n')

    return TEMPLATE