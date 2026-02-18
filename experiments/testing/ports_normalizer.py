import re


def normalize_ports_with_range(port_string):
    # Remove outer module parentheses/semicolon
    port_string = port_string.strip().strip('();')

    # Split by commas, avoiding splitting inside bit ranges [3:0]
    parts = re.split(r',\s*(?![^\[]*\])', port_string)

    normalized = []

    # Persistent State
    curr_dir = "input"
    curr_type = "logic"
    curr_range = ""

    for part in parts:
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


# --- Testing with your specific case ---
raw_input = "input logic clk, input logic rst, input logic mode_sel, output logic [1:0] filter_mode, output logic [1:0] val"
expanded = normalize_ports_with_range(raw_input)

for p in expanded:
    print(f"'{p}',")