import re

def get_module_name(module: str):
    # Look for 'module' followed by the name
    match = re.search(r'module\s+(\w+)', module)
    return match.group(1) if match else None

def get_port_signals(module: str):
    # Captures everything between 'module name (...);'
    # Handles multi-line port lists
    port_block = re.search(r'module\s+\w+\s*\((.*?)\)\s*;', module, re.DOTALL)
    if not port_block:
        return []

    # Split by comma and clean up whitespace/newlines
    raw_ports = port_block.group(1).split(',')
    clean_ports = [re.sub(r'\s+', ' ', p).strip() for p in raw_ports]
    return [p for p in clean_ports if p]

def get_triggers(module: str):
    # Find all always blocks and capture their trigger/type

    # 1. Capture sequential blocks: always_ff @(...) or always_latch @(...)
    seq_matches = re.finditer(r'always_(?:ff|latch) @(.*) begin', module)

    clk_trigger = ''
    rst_trigger = ''

    for m in seq_matches:
        trigger = m.group(1).strip().replace('(','').replace(')','').split(' or ')
        if trigger:
            clk_trigger = trigger[0]
            if len(trigger) > 1:
                rst_trigger = trigger[1]
        continue

    return clk_trigger, rst_trigger

def normalize_ports_with_range(input_signals: list):
    # Remove outer module parentheses/semicolon

    normalized = []

    # Persistent State
    curr_dir = "input"
    curr_type = "logic"
    curr_range = ""

    for part in input_signals:
        part = part.strip()
        if not part: continue

        # Regex breakdown:
        # 1. (dir)?    -> Optional input/output/inout
        # 2. (type)?   -> Optional logic/reg/wire
        # 3. (range)?  -> Optional [3:0]
        # 4. (name)    -> Signal name (Required)
        pattern = r'^(?P<dir>input|output|inout)?\s*(?P<type>logic|reg|wire)?\s*(?P<range>\[.*?\])?\s*(?P<name>\w+)$'
        match = re.search(pattern, part)

        if match:
            # Update state if a NEW direction or type is explicitly mentioned
            # If a new direction/type appears, we usually reset the range
            # UNLESS a new range is also provided in the same part.
            new_dir = match.group('dir')
            new_type = match.group('type')
            new_range = match.group('range')

            if new_dir:
                curr_dir = new_dir
                curr_range = ""  # Reset range on direction change
            if new_type:
                curr_type = new_type
                curr_range = ""  # Reset range on type change
            if new_range:
                curr_range = new_range

            p_name = match.group('name')

            # Construct the explicit string using the current persistent state
            full_decl = f"{curr_dir} {curr_type} {curr_range}".replace("  ", " ").strip()
            normalized.append(f"{full_decl} {p_name}")

    return normalized