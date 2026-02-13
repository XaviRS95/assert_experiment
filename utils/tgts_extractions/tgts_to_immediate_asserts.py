from ..regex_utils.text_processing import get_alpha_uuid
from .tgts_utils import clean_logical_operators, filter_valid_tgts_rules

def immediate_asserts_from_tgts(tgts_rules: list) -> str:
    """
    Generates immediate assertions from TGTS rules.

    Format: label: assert( (clauses) ? (check) : 1 ) else $error(...);
    """
    sva_lines = []

    # Process only valid rules
    valid_rules = filter_valid_tgts_rules(tgts_rules)

    for rule in valid_rules:
        # Generate unique label
        assert_label = get_alpha_uuid()

        # Clean up clauses and check expressions
        clauses = clean_logical_operators(rule['clauses'])
        check = clean_logical_operators(rule['check'])

        # Build the immediate assertion
        error_message = f'$error("Error in immediate assert {assert_label}")'
        sva_block = (
            f"{assert_label}: assert( ({clauses}) ? ({check}) : 1 )"
            f"  else {error_message};\n"
        )

        sva_lines.append(sva_block)

    return "\n".join(sva_lines)