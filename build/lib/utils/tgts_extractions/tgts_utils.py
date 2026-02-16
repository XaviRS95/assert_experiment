import re
from ..regex_utils.text_processing import get_alpha_uuid

def extract_delay_pattern(checks: str) -> tuple:
    """Extract variable name and delay value from [t+delay] pattern"""
    match = re.search(r'(\w+)\s*\[\s*t\s*\+\s*(\d+)\s*\]', checks)
    if match:
        var_name = match.group(1)
        delay_val = int(match.group(2))
        return var_name, delay_val
    return None, None


def process_delay_expression(checks: str) -> str:
    """Convert [t+delay] notation to SVA ##delay syntax"""
    var_name, delay_val = extract_delay_pattern(checks)
    if not var_name:
        return checks

    # Get the part after the index
    val_part = checks.split(']')[-1]

    # Apply $past logic if variable appears in val_part
    if var_name in val_part:
        val_part = re.sub(rf'\b{var_name}\b', f'$past({var_name})', val_part)

    # Determine SVA delay syntax
    if delay_val == 1:
        check_sva = var_name
    else:
        check_sva = f"##{delay_val - 1} {var_name}"

    return f"{check_sva}{val_part}"


def remove_reset_signal(clause: str, reset_signal: str) -> str:
    """Remove reset signal references from a clause"""
    if not clause or not reset_signal:
        return clause

    sig = re.escape(reset_signal)

    # Pattern to match reset signal with optional comparisons
    val_pattern = r"(\d+'b[01xXzZ]|\d+)"
    comparison = rf"(?:\s*(?:==|!=)\s*{val_pattern})?"
    reset_core = rf"(?:!\s*)?\(?\b{sig}\b{comparison}\)?"

    # Remove reset with trailing/leading operators
    trailing_op = rf"{reset_core}\s*(?:&&|\|\|)\s*"
    leading_op = rf"\s*(?:&&|\|\|)\s*{reset_core}"

    new_clause = re.sub(trailing_op, '', clause)
    new_clause = re.sub(leading_op, '', new_clause)
    new_clause = re.sub(reset_core, '', new_clause)

    # Cleanup
    new_clause = re.sub(r'!\s*\(\s*\)', '', new_clause)
    new_clause = re.sub(r'\(\s*\)', '', new_clause)
    new_clause = re.sub(r'\s+', ' ', new_clause).strip()

    return new_clause if new_clause else "ASYNC_RST_CHECK"


def generate_async_reset_assert(reset_signal_activation: str, final_check: str) -> str:
    """Generate async reset assertion block"""
    return (f"always_comb begin\n"
            f"    if ({reset_signal_activation}) begin\n"
            f"        {get_alpha_uuid()}: assert ({final_check});\n"
            f"    end\n"
            f"end")


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


