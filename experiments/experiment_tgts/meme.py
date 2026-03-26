import re

code = """
typedef enum logic [4:0] {
    IDLE,
    LP_STATE,
    HS_START,
    SYNC_PATTERN,
    ECC_CHECK,
    PH_HEADER,
    PH_DATA_TYPE,
    PH_WORD_COUNT,
    PH_ECC,
    PAYLOAD_DATA,
    CRC_CHECK,
    LINE_END,
    FRAME_START,
    FRAME_END,
    ERROR_RECOVERY,
    WAIT_HS_TRAIL,
    LP_11_STATE
} state_t;

state_t state, next_state;
logic [31:0] word_count;
logic [15:0] pixel_count [0:3];
logic [7:0] lane_data [0:3];
logic [3:0] lane_align;
logic [5:0] ecc_calc;
logic [5:0] ecc_recv;
logic [15:0] crc_calc;
logic [15:0] crc_recv;
logic [31:0] packet_data [0:255];
logic [2:0] lane_index;
logic sync_detected;
logic [7:0] sync_pattern;

parameter SYNC_CODE = 8'hB8;
parameter BLANKING_CODE = 8'h00;
"""

# 1. Split by semicolon to handle line-by-line (statement by statement)
statements = code.split(';')

results = []
reserved_typedef_names = []


for stmt in statements:
    stmt = stmt.strip()
    if not stmt:
        continue

    # Ignore parameters entirely
    if stmt.startswith('parameter'):
        continue

    # Handle typedef: Extract only the name at the end (e.g., 'state_t')
    if stmt.startswith('typedef'):
        typedef_name = re.search(r'}\s*([a-zA-Z_]\w*)', stmt)
        if typedef_name:
            reserved_typedef_names.append(typedef_name.group(1))
        continue

    # Remove bit-ranges like [31:0] or [0:3] first to simplify
    clean_stmt = re.sub(r'\[[^\]]*\]', '', stmt)

    # Extract words: skip the first word (the type like 'logic') and grab the rest as variable names
    parts = re.findall(r'\b[a-zA-Z_]\w*\b', clean_stmt)

    for part in parts:
        if part not in reserved_typedef_names and part != 'logic': #Part is not a typedef enum variable name:
            results.append(part)


# Flatten or print line by line
for line_vars in results:
    print(line_vars)