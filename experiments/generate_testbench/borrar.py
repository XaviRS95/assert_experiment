import re


def parse_signal_declaration(signal):
    """Enhanced parser for SystemVerilog signal declarations"""
    # Remove leading/trailing whitespace
    signal = signal.strip()

    # Patterns for different declarations
    patterns = {
        # Basic types with optional packed dimensions: logic [7:0] sig_name
        'basic': r'^(?P<type>[\w]+)(?:\s+)(?P<name>\w+)$',

        # Packed array: logic [7:0] sig_name
        'packed': r'^(?P<type>\w+)\s+\[\s*(?P<msb>-?\d+)\s*:\s*(?P<lsb>-?\d+)\s*\]\s+(?P<name>\w+)$',

        # Unpacked array: logic sig_name [0:7]
        'unpacked': r'^(?P<type>\w+)\s+(?P<name>\w+)\s*\[\s*(?P<msb>-?\d+)\s*:\s*(?P<lsb>-?\d+)\s*\]$',

        # Multi-dimensional: logic [7:0] sig_name [0:3]
        'multidim': r'^(?P<type>\w+)\s+\[\s*(?P<pmsb>-?\d+)\s*:\s*(?P<plsb>-?\d+)\s*\]\s+(?P<name>\w+)\s*\[\s*(?P<umsb>-?\d+)\s*:\s*(?P<ulsb>-?\d+)\s*\]$',

        # Signed/unsigned: signed int sig_name
        'signed': r'^(?P<signed>signed|unsigned)\s+(?P<type>\w+)(?:\s+)(?P<name>\w+)$',

        # Signed with packed: signed [7:0] sig_name
        'signed_packed': r'^(?P<signed>signed|unsigned)\s+\[\s*(?P<msb>-?\d+)\s*:\s*(?P<lsb>-?\d+)\s*\]\s+(?P<name>\w+)$',

        # Struct/enum/interface (simplified)
        'complex': r'^(?P<type>\w+)\s+(?P<name>\w+)$',
    }

    for pattern_name, pattern in patterns.items():
        match = re.match(pattern, signal)
        if match:
            groups = match.groupdict()

            if pattern_name == 'packed':
                return groups['type'], groups['name'], (groups['msb'], groups['lsb'])
            elif pattern_name == 'unpacked':
                return groups['type'], groups['name'], (groups['msb'], groups['lsb'])
            elif pattern_name == 'multidim':
                # For multi-dimensional, return packed info
                return groups['type'], groups['name'], (groups['pmsb'], groups['plsb'])
            elif pattern_name == 'signed':
                return f"{groups['signed']}_{groups['type']}", groups['name'], None
            elif pattern_name == 'signed_packed':
                return f"{groups['signed']}_{groups['type'] if 'type' in groups else 'logic'}", groups['name'], (
                groups['msb'], groups['lsb'])
            else:  # basic or complex
                return groups['type'], groups['name'], None

    # If no pattern matches
    return None, None, None


def generate_signal_stimulus(signals: list, clock_signal: str, reset_signal: str) -> str:
    """Generate stimulus assignments for input signals only with enhanced type support"""

    # Extended list of SystemVerilog data types
    SV_TYPES = {
        # 2-state types
        'bit': '2-state',
        'byte': '2-state',
        'shortint': '2-state',
        'int': '2-state',
        'longint': '2-state',

        # 4-state types
        'logic': '4-state',
        'reg': '4-state',
        'integer': '4-state',
        'time': '4-state',

        # Net types
        'wire': 'net',
        'wand': 'net',
        'wor': 'net',
        'tri': 'net',
        'triand': 'net',
        'trior': 'net',
        'trireg': 'net',
        'tri0': 'net',
        'tri1': 'net',
        'uwire': 'net',

        # Real types
        'real': 'real',
        'shortreal': 'real',
        'realtime': 'real',

        # Signed/unsigned variants
        'signed_int': 'signed',
        'unsigned_int': 'unsigned',
        'signed_bit': 'signed',
        'unsigned_bit': 'unsigned',
        'signed_logic': 'signed',
        'unsigned_logic': 'unsigned',
    }

    input_signals = []
    for signal in signals:
        if 'input ' in signal and 'output ' not in signal:
            # Remove 'input' keyword and clean up
            cleaned = signal.replace('input ', '').strip().rstrip(',')
            input_signals.append(cleaned)

    template = ''

    for signal in input_signals:
        # Skip clock and reset signals
        if clock_signal and clock_signal in signal:
            continue
        if reset_signal and reset_signal in signal:
            continue

        sig_type, sig_name, array_info = parse_signal_declaration(signal)

        if sig_name:
            template += f"\t\t\t{sig_name} = "

            # Handle different types
            if sig_type in SV_TYPES:
                type_category = SV_TYPES[sig_type]

                # Handle array types (packed arrays)
                if array_info:
                    msb, lsb = int(array_info[0]), int(array_info[1])
                    width = abs(msb - lsb) + 1
                    max_val = (2 ** width) - 1

                    if type_category in ['2-state', '4-state', 'net', 'signed', 'unsigned']:
                        template += f"$urandom_range(0, {max_val});\n"

                # Handle non-array types
                else:
                    if sig_type == 'bit':
                        template += "$urandom_range(0, 1);\n"

                    elif sig_type == 'byte':
                        template += "$urandom_range(-128, 127);\n"

                    elif sig_type == 'shortint':
                        template += "$urandom_range(-32768, 32767);\n"

                    elif sig_type == 'int' or sig_type == 'signed_int' or sig_type == 'unsigned_int':
                        template += "$urandom_range(-2147483648, 2147483647);\n"

                    elif sig_type == 'longint' or sig_type == 'signed_longint' or sig_type == 'unsigned_longint':
                        template += "$urandom_range(-9223372036854775808, 9223372036854775807);\n"

                    elif sig_type in ['logic', 'reg', 'wire', 'wand', 'wor', 'tri', 'triand', 'trior', 'trireg', 'tri0',
                                      'tri1', 'uwire']:
                        template += "$urandom_range(0, 1);\n"

                    elif sig_type == 'integer':
                        template += "$urandom_range(-2147483648, 2147483647);\n"

                    elif sig_type == 'time':
                        template += "$urandom_range(0, 2**64-1);\n"

                    elif sig_type in ['real', 'shortreal', 'realtime']:
                        template += "$urandom() / (2**31-1);  // random real\n"

                    else:
                        template += "$urandom();\n"
            else:
                # For unrecognized types (like user-defined structs, enums, interfaces)
                # You might want to handle these specially
                template += "$urandom();  // Unknown type: {sig_type}\n"

    return template


# Example usage
if __name__ == "__main__":
    test_signals = [
        "input wire clk",
        "input logic rst_n",
        "input logic [7:0] data_in",
        "input int count",
        "input byte status",
        "input signed [15:0] offset",
        "input real temperature",
        "input shortint short_val",
        "input logic data_array [0:7]",
        "input bit [3:0][7:0] matrix",  # multi-dimensional
        "input integer time_val",
        "input uwire test_signal",
        "input my_if interface",  # interface example
        "output logic [7:0] result"  # should be skipped
    ]

    stimulus = generate_signal_stimulus(test_signals, "clk", "rst_n")
    print(stimulus)