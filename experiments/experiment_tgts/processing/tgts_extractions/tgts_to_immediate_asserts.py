from utils.regex_utils.text_processing import get_alpha_uuid
from .tgts_utils import clean_logical_operators, filter_valid_tgts_rules, generate_concurrent_sensitivity_list

def immediate_asserts_from_tgts(tgts_rules: list) -> str:
    """
    Generates immediate assertions from TGTS rules.

    Format: label: assert( (clauses) ? (check) : 1 ) else $error(...);
    """
    sva_lines = []

    # Process only valid rules
    valid_rules = filter_valid_tgts_rules(tgts_rules)

    raw_asserts = []

    for rule in valid_rules:

        # Clean up clauses and check expressions
        clauses = clean_logical_operators(rule['clauses'])
        check = clean_logical_operators(rule['check'])

        raw_assert = f'assert( ({clauses}) ? ({check}) : 1 )'

        #This removes repeated immediate assertions that the LLM outputted:
        if raw_assert not in raw_asserts:
            raw_asserts.append(raw_assert)

    for raw_assert in raw_asserts:

        # Generate unique label
        assert_label = get_alpha_uuid()

        # Build the immediate assertion
        error_message = f'$error("Error in immediate assert {assert_label}")'
        sva_block = (
            f"{assert_label}: {raw_assert}"
            f"  else {error_message};\n"
        )

        sva_lines.append(sva_block)

    return "\n".join(sva_lines)


def concurrent_asserts_from_tgts(tgts_rules: list, input_ports_list:list) -> str:
    """
    Generates immediate assertions from TGTS rules.

    Format: label: assert( (clauses) ? (check) : 1 ) else $error(...);
    """
    sva_lines = []

    # Process only valid rules
    valid_rules = filter_valid_tgts_rules(tgts_rules)

    raw_asserts = []

    for rule in valid_rules:

        # Clean up clauses and check expressions
        clauses = clean_logical_operators(rule['clauses'])
        check = clean_logical_operators(rule['check'])

        concurrent_sensitivity_list = generate_concurrent_sensitivity_list(clauses=clauses, checks=check, input_ports_list=input_ports_list)

        sensitivity_list = f'@({concurrent_sensitivity_list})'

        raw_assert = f'{sensitivity_list} {clauses} |-> {check}'

        #This removes repeated immediate assertions that the LLM outputted:
        if raw_assert not in raw_asserts:
            raw_asserts.append(raw_assert)

    for raw_assert in raw_asserts:

        # Generate unique label
        assert_label = get_alpha_uuid()

        # Build the immediate assertion
        error_message = f'$error("Error in immediate assert {assert_label}")'

        sva_block = f'{assert_label}: assert property ({raw_assert}) else {error_message};'

        sva_lines.append(sva_block)

    return "\n".join(sva_lines)