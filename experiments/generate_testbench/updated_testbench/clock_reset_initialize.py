

def generate_clock_initial_section(clock_signal:str, clock_period:int=0):

    template = f'\tlogic {clock_signal} = 0;\n'
    if clock_period > 0:
        template += f'\talways #{clock_period} {clock_signal} = ~{clock_signal};\n'

    return template

def generate_reset_initial_info(reset_trigger:str, reset_signal: str)-> str:

    TEMPLATE = '\tlogic {reset_signal};\n\n'

    if reset_signal and reset_trigger:
        reset_info = {
            'reset_assert_value': "0",
            'reset_deassert_value': "1",
        }

        if "posedge" in reset_trigger:
            reset_info['reset_assert_value'] = "1"
            reset_info['reset_deassert_value'] = "0"

        TEMPLATE = (f'\tinitial begin\n'
                    f'\t\t{reset_signal} = {reset_info["reset_assert_value"]};\n'
                    f'\t\t#(RESET DELAY) {reset_signal} = {reset_info["reset_deassert_value"]} ;\n'
                    f'\tend\n')

    return TEMPLATE