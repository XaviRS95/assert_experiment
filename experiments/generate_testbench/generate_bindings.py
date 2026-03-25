from module_info_extractor import extract_ports_names, generate_instantiate_section, extract_internal_variables_names

def generate_dut_assert_sections(signals: list, dut_module_name: str, assert_module_name: str, internal_dut_variables_names: list) -> dict:
    '''
    Generates the DUT and assert binding section
    :param signals:
    :param dut_module_name:
    :param assert_module_name:
    :return:
    '''
    signals_names = extract_ports_names(signals_list = signals)

    dut_section = generate_instantiate_section(
        dut_module_name = dut_module_name,
        assert_module_name = assert_module_name,
        signals_list=signals_names,
        section_type='dut'
    )

    assert_section = generate_instantiate_section(
        dut_module_name=dut_module_name,
        assert_module_name=assert_module_name,
        signals_list=signals_names,
        section_type='assertions',
        internal_variables_names=internal_dut_variables_names
    )

    return {
        'dut_section': dut_section,
        'assert_section': assert_section
    }