from prompts.prompts_experiment3 import comb_to_tgts, seq_to_tgts
from utils import utils, regex
from prompts import prompts_experiment3


def experiment3(model_name:str, file_path:str):

    #sv_modules = utils.read_code_files(csv_path=file_path)

    sv_modules = ["""
    
    module seq_case73(
        input logic clk, reset, serial_in,
        output logic [3:0] q
    );
        always_ff @(posedge clk or posedge reset) begin
            if(reset)
                q <= 4'b0000;
            else
                case(q)
                    default: q <= {q[2:0], serial_in}; // shift left
                endcase
        end
    endmodule

    """]

    for sv_code in sv_modules:
        clean_code = regex.commentless_code(code=sv_code)
        clean_comb_blocks = regex.get_blocks(code=clean_code, pattern=r'always_comb')
        clean_seq_blocks = regex.get_blocks(code=clean_code, pattern=r'always_(?:ff|latch)')
        clean_func_blocks = regex.extract_functions(code=clean_code)
        header_and_vars = regex.extract_header_and_vars(code=clean_code, comb_blocks=clean_comb_blocks,
                                                  seq_blocks=clean_seq_blocks, func_blocks=clean_func_blocks)

        module_name = header_and_vars['header']['module_name']
        parameters = header_and_vars['header']['parameters']
        ports = header_and_vars['header']['ports']
        inner_vars = header_and_vars['inner_vars']

        assertions = []

        #Combinational blocks
        for block in clean_comb_blocks:
            comb_to_tgts_prompt = comb_to_tgts(parameters=parameters, ports=ports, inner_vars=inner_vars, block=block)
            tgts_rules = utils.query_ollama(prompt=comb_to_tgts_prompt, model=model_name, code_call=False)
            immediate_asserts = regex.immediate_asserts_from_tgts(tgts_rules=tgts_rules)
            assertions.append(immediate_asserts)

        #Sequential blocks
        for block in clean_seq_blocks:
            seq_to_tgts_prompt = seq_to_tgts(parameters=parameters, ports=ports, inner_vars=inner_vars, block=block)
            tgts_rules = utils.query_ollama(prompt=seq_to_tgts_prompt, model=model_name, code_call=False)
            print(tgts_rules)
        #     immediate_asserts = regex.immediate_asserts_from_tgts(tgts_rules=tgts_rules)
        #     assertions.append(immediate_asserts)


        final_module_parameters = f'# ({parameters})' if parameters else ''
        final_module_ports = ports.replace('output logic', 'input logic')
        final_module_assertions = '\n\t'.join(assertions)
        final_module = f"""
        
        module {module_name}_asserts {final_module_parameters} ({final_module_ports});
        
        always_comb begin
            {final_module_assertions}
        end
        
        endmodule
        """

        print(final_module)

experiment3(model_name='deepseek-coder-v2:16b', file_path='')