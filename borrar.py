import re


def strip_always_wrapper(text):
    # 1. Identify the header: always_ff/comb/latch + optional @(...) + begin
    # This regex looks for the first occurrence of the always block start
    header_pattern = re.compile(
        r"always_(?:ff|comb|latch)\s*(?:@\s*\(.*?\))?\s*begin",
        re.DOTALL
    )

    header_match = header_pattern.search(text)

    if not header_match:
        return "No always block found."

    # The starting point of our content is right after the 'begin'
    content_start = header_match.end()

    # 2. Find the index of the absolute LAST 'end' in the string
    # We use rfind to search backwards from the end of the file
    last_end_match = list(re.finditer(r'\bend\b(?!\s*\w)', text))

    if not last_end_match:
        return "No closing 'end' found."

    # We take the start position of the very last 'end' keyword found
    content_end = last_end_match[-1].start()

    # 3. Slice the string to extract only the internal content
    extracted_logic = text[content_start:content_end]

    return extracted_logic.strip('\n\r')


# --- Testing with your nested case example ---
sv_input = """
always_ff @(posedge clk or negedge reset) begin
        if(!reset)
            count <= 2'b00;
        else
            case(count)
                2'b00: count <= 2'b01;
                2'b01: count <= 2'b10;
                2'b10: count <= 2'b11;
                2'b11: count <= 2'b00;
                default: count <= 2'b00;
            endcase
    end
"""

result = strip_always_wrapper(sv_input)
print(result)