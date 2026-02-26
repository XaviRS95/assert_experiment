from ..tgts_extractions.tgts_utils import (extract_reset_info,
                                           filter_valid_tgts_rules,
                                           clean_logical_operators,
                                           constains_delays,
                                           remove_clock_cycle_notation,
                                           process_delay_expression,
                                           remove_reset_signal,
                                           generate_async_reset_assert,
                                           generate_sequential_property)

def sequential_properties_from_tgts(tgts_rules: list, sensitivity_list: dict) -> str:
    """
    Generates sequential SVA properties from TGTS rules.
    """
    seq_tests = []

    # Extract reset information
    reset_info = extract_reset_info(sensitivity_list)

    # Process only valid rules
    valid_rules = filter_valid_tgts_rules(tgts_rules)

    for rule in valid_rules:
        # Clean up clauses
        clauses = clean_logical_operators(rule['clauses'])
        if constains_delays(text=clauses):
            clauses = remove_clock_cycle_notation(clauses)


        # Process check expression
        checks = clean_logical_operators(rule['check'])
        final_check = checks
        if constains_delays(text=checks):
            final_check = process_delay_expression(checks)
            final_check = remove_clock_cycle_notation(final_check)

        # Remove reset signal if present
        if reset_info['reset_signal_name']:
            clauses = remove_reset_signal(
                clause=clauses,
                reset_signal=reset_info['reset_signal_name']
            )

        # Generate appropriate assertion
        if (clauses == "ASYNC_RST_CHECK" and
                reset_info['reset_signal_activation']):
            assertion = generate_async_reset_assert(
                reset_info['reset_signal_activation'],
                final_check
            )
        else:
            assertion = generate_sequential_property(
                sensitivity_list,
                reset_info['disable_iff'],
                clauses,
                final_check
            )

        seq_tests.append(assertion)

    return "\n".join(seq_tests)