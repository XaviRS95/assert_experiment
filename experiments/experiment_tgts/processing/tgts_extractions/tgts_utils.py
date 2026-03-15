import re
from utils.regex_utils.text_processing import get_alpha_uuid

def constains_delays(text: str)-> bool:
    delay_pattern = r"\[\s*t\s*(?:\+\s*\d+)?\s*\]"
    return True if re.search(delay_pattern, text) else False

def extract_delay_pattern(checks: str) -> tuple:
    """Extract variable name and delay value from [t+delay] pattern"""
    match = re.search(r'(\w+)\s*\[\s*t\s*\+\s*(\d+)\s*\]', checks)
    if match:
        var_name = match.group(1)
        delay_val = int(match.group(2))
        return var_name, delay_val
    return None, None


def process_delay_expression(checks: str) -> str:
    # 1. Find the "Anchor" (the t+n part on the LHS)
    # Matches: var_name [ t + 1 ]
    anchor_match = re.search(r'(\w+)\s*\[\s*t\s*\+\s*(\d+)\s*\]', checks)

    if not anchor_match:
        return checks

    var_name = anchor_match.group(1)
    anchor_delay = int(anchor_match.group(2))

    # 2. Split the expression into LHS and RHS
    # Using a split that handles various operators
    parts = re.split(r'(==|>=|<=|>|<|!=)', checks)
    if len(parts) < 3:
        return checks

    lhs = parts[0]
    operator = parts[1]
    rhs = "".join(parts[2:])

    # 3. Process LHS: Remove the [t+n]
    new_lhs = re.sub(rf'{var_name}\s*\[\s*t\s*\+\s*{anchor_delay}\s*\]', var_name, lhs).strip()

    # 4. Process RHS: Convert [t] or [t+m] to $past
    # Look for the variable with any bracketed t expression
    def replace_with_past(match):
        inner_t = match.group(2)  # This is "t" or "t + 0" or "t + 1"

        # Determine the offset
        if inner_t.strip() == 't':
            offset = anchor_delay
        else:
            # Extract number from 't + m'
            offset_match = re.search(r'\d+', inner_t)
            m = int(offset_match.group(0)) if offset_match else 0
            offset = anchor_delay - m

        if offset > 0:
            return f"$past({var_name}, {offset})" if offset > 1 else f"$past({var_name})"
        return var_name

    # Regex to find var[t...] on the RHS
    rhs_pattern = rf'\b({var_name})\s*\[\s*(t(?:\s*\+\s*\d+)?)\s*\]'
    new_rhs = re.sub(rhs_pattern, replace_with_past, rhs).strip()

    return f"{new_lhs} {operator} {new_rhs}"


def remove_reset_signal(clause: str, reset_signal: str) -> str:
    # 1. Define the core reset pattern
    val_pattern = r"(\d+'b[01xXzZ]|\d+)"
    comparison_ops = r"(?:==|!=|<=|>=|<|>)"
    reset_core = rf"(?:!\s*)?\b{reset_signal}\b(?:\s*{comparison_ops}\s*{val_pattern})?"

    # 2. Split the clause by && or || while keeping the operators
    # This creates a list like ['((rst == 0)', '&&', '(val > 0))']
    parts = re.split(r'(&&|\|\|)', clause)

    # 3. Filter out parts that contain the reset signal
    # We also need to keep track of where operators are to avoid "&& &&"
    new_parts = []
    for part in parts:
        if not re.search(reset_core, part):
            new_parts.append(part)

    # 4. Join and Clean Up
    # After filtering, we might have dangling operators at the start/end
    # or double operators like "&& &&"
    temp_result = "".join(new_parts).strip()

    # Remove leading/trailing/double operators
    temp_result = re.sub(r'^\s*(&&|\|\|)\s*', '', temp_result)
    temp_result = re.sub(r'\s*(&&|\|\|)\s*$', '', temp_result)
    temp_result = re.sub(r'(&&|\|\|)\s*(&&|\|\|)', r'\1', temp_result)

    # 5. Fix Parentheses Balance (The "Healer")
    def heal_balance(text):
        # Left-to-Right: Remove orphaned ')'
        balance = 0
        pass1 = ""
        for char in text:
            if char == '(':
                balance += 1
                pass1 += char
            elif char == ')':
                if balance > 0:
                    balance -= 1
                    pass1 += char
            else:
                pass1 += char

        # Right-to-Left: Remove orphaned '('
        balance = 0
        pass2 = ""
        for char in reversed(pass1):
            if char == ')':
                balance += 1
                pass2 += char
            elif char == '(':
                if balance > 0:
                    balance -= 1
                    pass2 += char
            else:
                pass2 += char
        return pass2[::-1]

    result = heal_balance(temp_result).strip()

    # Final check: if it's just empty parentheses or nothing, it's a reset block
    if not result or result in ["()", "(( ))"]:
        return "ASYNC_RST_CHECK"

    return result

def generate_async_reset_assert(reset_sensitivity_activation:str, final_check: str) -> str:
    """Generate async reset assertion block"""
    id = get_alpha_uuid()
    async_reset = (f'property {id};\n'
                   f'\t@({reset_sensitivity_activation}) {final_check};\n'
                   f'endproperty\n'
                   f'assert property ({id}) else $error("Error in asynchronous reset {id}");\n')
    return async_reset

def generate_sequential_property(sensitivity_list: dict, disable_iff: str,
                                 clauses: str, final_check: str) -> str:
    """Generate sequential property with assertion"""
    property_label = get_alpha_uuid()
    return (f"property {property_label};\n"
            f"    @({sensitivity_list['clk']}) {disable_iff} ({clauses}) |=> ({final_check});\n"
            f"endproperty\n"
            f"assert property ({property_label});\n")


def clean_logical_operators(text: str) -> str:
    """Replace textual logical operators with SystemVerilog equivalents"""
    if not text:
        return text

    replacements = [
        (' AND ', ' && '),
        (' and ', ' && '),
        (' OR ', ' || '),
        (' or ', ' || '),
        (' NOT ', ' !'),
        (' not ', ' !'),
    ]

    for old, new in replacements:
        text = text.replace(old, new)

    return text


def remove_clock_cycle_notation(text: str) -> str:
    """Remove [t], [t+1], etc. notations"""
    if not text:
        return text

    patterns = ['[t]', '[ t ]', '[t+1]', '[t + 1]']
    for pattern in patterns:
        text = text.replace(pattern, '')

    return text


def filter_valid_tgts_rules(tgts_rules: list) -> list:
    """Filter out malformed TGTS rules with true/TRUE clauses or checks"""
    return [rule for rule in tgts_rules
            if rule.get('clauses', '').lower() not in ['true']
            and rule.get('check', '').lower() not in ['true']]


def extract_reset_info(sensitivity_list: dict) -> dict:
    """Extract reset signal information from sensitivity list"""
    reset_info = {
        'disable_iff': '',
        'reset_signal_name': '',
        'reset_signal_activation': ''
    }

    if 'rst' in sensitivity_list and sensitivity_list['rst']:
        reset_parts = sensitivity_list['rst'].split(' ')
        if len(reset_parts) >= 2:
            reset_signal_trigger = reset_parts[0]
            reset_info['reset_signal_name'] = reset_parts[1]
            reset_info[
                'reset_signal_activation'] = f'{"!" if reset_signal_trigger == "negedge" else ""}{reset_parts[1]}'
            reset_info['disable_iff'] = f'disable iff({reset_info["reset_signal_activation"]})'

    return reset_info


