import re


class SVExtractor:
    def __init__(self, code):
        self.code = code

    def extract_all(self):
        return {
            "module_name": self.get_module_name(),
            "ports": self.get_ports(),
            "triggers": self.get_triggers()
        }

    def get_module_name(self):
        # Look for 'module' followed by the name
        match = re.search(r'module\s+(\w+)', self.code)
        return match.group(1) if match else None

    def get_ports(self):
        # Captures everything between 'module name (...);'
        # Handles multi-line port lists
        port_block = re.search(r'module\s+\w+\s*\((.*?)\)\s*;', self.code, re.DOTALL)
        if not port_block:
            return []

        # Split by comma and clean up whitespace/newlines
        raw_ports = port_block.group(1).split(',')
        clean_ports = [re.sub(r'\s+', ' ', p).strip() for p in raw_ports]
        return [p for p in clean_ports if p]

    def get_triggers(self):
        # Find all always blocks and capture their trigger/type
        results = []

        # 1. Capture sequential blocks: always_ff @(...) or always @(...)
        seq_matches = re.finditer(r'always(?:_ff)?\s*@\s*\((.*?)\)', self.code)

        for m in seq_matches:
            trigger = m.group(1).strip().split(' or ')
            clk = ''
            rst = ''
            if trigger:
                clk = trigger[0]
                if len(trigger) > 1:
                    rst = trigger[1]
            results.append({"type": "sequential", "trigger": {'clk_trigger': clk, 'rst_trigger': rst}})

        # 2. Capture combinational blocks: always_comb
        if re.search(r'always_comb', self.code):
            results.append({"type": "combinational", "trigger": "implicit (all signals)"})

        # 3. Capture latch blocks: always_latch
        if re.search(r'always_latch', self.code):
            results.append({"type": "latch", "trigger": "implicit (enable/data)"})

        return results


# --- Example Usage ---
sv_code = """
module case_filter_mode(
    input logic clk, rst, mode_sel, 
    output logic [1:0] filter_mode
);
    always_ff @(posedge clk or posedge rst) begin
        // logic here
    end

    always_comb begin
        // logic here
    end
endmodule
"""

extractor = SVExtractor(sv_code)
data = extractor.extract_all()

print(f"Module: {data['module_name']}")
print(f"Ports:  {data['ports']}")
print("Triggers:")
for t in data['triggers']:
    print(f"  - {t['type']}: {t['trigger']}")