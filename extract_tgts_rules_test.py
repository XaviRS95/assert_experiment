import re
import json

raw_text = """
RULE tl_o_d_valid_0

WHEN true

THEN tl_o_d_valid == 1'b0


RULE tl_o_d_error_0

WHEN true

THEN tl_o_d_error == 1'b0


RULE tl_o_d_valid_1

WHEN tl_i_a_valid

THEN tl_o_d_valid == 1'b1


RULE tl_o_d_error_1

WHEN tl_i_a_valid && (tl_i_a_opcode != 3'b000 && tl_i_a_opcode != 3'b001 && tl_i_a_opcode != 3'b010)

THEN tl_o_d_error == 1'b1


RULE tl_o_d_error_2

WHEN tl_i_a_valid && tl_i_a_opcode == 3'b000 && (tl_i_a_size != 3'b000 && tl_i_a_size != 3'b001 && tl_i_a_size != 3'b010)

THEN tl_o_d_error == 1'b1


RULE tl_o_d_error_3

WHEN tl_i_a_valid && tl_i_a_opcode == 3'b001 && tl_i_a_param == 3'b000 && (tl_i_a_size != 3'b001 && tl_i_a_size != 3'b010)

THEN tl_o_d_error == 1'b1


RULE tl_o_d_error_4

WHEN tl_i_a_valid && tl_i_a_opcode == 3'b010 && tl_i_a_param != 3'b001

THEN tl_o_d_error == 1'b1 
"""


def extract_tgts_rules(text):
    # Regex breakdown:
    # RULE + name
    # WHEN + everything until the THEN keyword (non-greedy)
    # THEN + the full assignment logic
    pattern = r"RULE\s+(?P<name>\w+)\s+WHEN\s+(?P<clauses>[\s\S]+?)\s+THEN\s+(?P<check>.+)"

    matches = []

    # re.MULTILINE is used to handle the start/end of the string correctly
    for match in re.finditer(pattern, text):
        # .groupdict() maps the (?P<name>) syntax directly to keys
        rule_dict = match.groupdict()

        # Clean up whitespace/newlines from the captured clauses
        rule_dict['clauses'] = rule_dict['clauses'].strip()
        rule_dict['check'] = rule_dict['check'].strip()

        matches.append(rule_dict)

    return matches


def immediate_asserts_from_tgts(rules_list: list):
    sva_lines = []

    sva_lines.append("// Automatically generated SystemVerilog Assertions from TGTS")

    for rule in rules_list:
        # 1. Clean up the name for the property label
        assert_label = f"assert_label_{rule['name']}"

        if rule['clauses'] != 'true':

            assert_body = f'{rule["clauses"]} && {rule["check"]}'

            #Immediate assertions
            sva_block = (
                f'{assert_label}: assert({assert_body}) '
                f'else $error("Error in immediate assert {assert_label}");'
            )

            #Concurrent construction block
            # sva_block = (
            #     f"// Rule: {prop_name}\n"
            #     f"assert {rule['name']}: assert property (\n"
            #     f"  {antecedent} |-> {consequent}\n"
            #     f") else $error(\"TGTS Violation: {rule['name']} failed\");\n"
            # )

            sva_lines.append(sva_block)

    return "\n".join(sva_lines)

# Execution
rules_list = extract_tgts_rules(raw_text)
properties_list = immediate_asserts_from_tgts(rules_list=rules_list)

print(properties_list)