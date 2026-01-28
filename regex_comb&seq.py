import re

# Example usage:
sv_code = """
module obi_txn_decoder (
    input  logic        req,
    input  logic        we,
    input  logic [1:0]  prot,
    input  logic [1:0]  burst,
    output logic        allow,
    output logic        fault
);

    // prot[1] = privileged
    // prot[0] = secure

    always_comb begin
        allow = 1'b0;
        fault = 1'b0;

        if (req) begin
            unique case (we)
                1'b0: begin // READ
                    case (prot)
                        2'b00, 2'b01: begin
                            case (burst)
                                2'b00, 2'b01: allow = 1'b1;
                                default: fault = 1'b1;
                            endcase
                        end
                        default: fault = 1'b1;
                    endcase
                end

                1'b1: begin // WRITE
                    case (prot)
                        2'b10: begin // privileged non-secure
                            case (burst)
                                2'b00: allow = 1'b1;
                                default: fault = 1'b1;
                            endcase
                        end
                        default: fault = 1'b1;
                    endcase
                end

                default: fault = 1'b1;
            endcase
        end
    end

endmodule

"""



def get_always_comb_block(code):
    # 1. Locate the start of the always_comb
    start_match = re.search(r'always_comb', code)
    if not start_match:
        return None

    start_pos = start_match.start()

    # 2. Search for 'begin' or 'end' only AFTER the always_comb
    # We use finditer to get the positions (match.start() and match.end())
    search_area = code[start_pos:]
    stack = 0
    first_begin_found = False
    block_end_pos = -1

    # This regex finds 'begin' and 'end' as whole words
    for match in re.finditer(r'\b(begin|end)\b', search_area):
        word = match.group(1)

        if word == 'begin':
            if not first_begin_found:
                first_begin_found = True
            stack += 1

        elif word == 'end':
            stack -= 1

        # 3. When stack hits 0, we've found the matching 'end'
        if first_begin_found and stack == 0:
            block_end_pos = start_pos + match.end()
            break

    if block_end_pos != -1:
        return code[start_pos:block_end_pos]

    return None

print(get_always_comb_block(sv_code))