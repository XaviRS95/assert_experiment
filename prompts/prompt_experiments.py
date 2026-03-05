def experiment1_prompt(module: str) -> str:
    EXPERIMENT_1_SIMPLE_CALL = f"""
    Using this SystemVerilog code, generate a module with the same signals that includes the properties and asserts given the original module:

    {module}

    Generate the output inside of this code block markdown : 

    ```systemverilog  

    ```

    """

    return EXPERIMENT_1_SIMPLE_CALL


def experiment2_prompt(module: str) -> str:
    '''

    :param module:
    :return:
    '''
    EXPERIMENT_2_CALL = f"""
    Role: You are an expert in SystemVerilog RTL design and SystemVerilog Assertions (SVA), specialized in generating assertions from procedural case statements. 

    Objective: Given a SystemVerilog case statement provided by the user, generate SystemVerilog Assertion (SVA) code that verifies the behavior described by the case statement. 

    SYSTEMVERILOG ASSERTION GENERATION RULES (MANDATORY)

    Assertions must verify functional behavior, not mirror control logic.
    Generate one distinct property and one corresponding assert property for each observable functional effect (signal assignment, state update, output value). 
    Do not group multiple functional checks in a single property. 
    Always include in your output the internal variables and auxiliar functions used inside the code. 
    If a property references a function from the original code, include it as well in the output code.
    Assertions must observe RTL signals only. Do not use $display, $write, $finish, $stop, or any system task with side effects. All assertion expressions must be pure boolean logic.
    Assertions must not re-encode decode or control logic (e.g., case, case inside, if/else, ranges, or complex boolean expressions). If the RTL provides a decoded signal (enum, one-hot, flag, or state variable), assertions must be written against that signal.
    If the RTL does not expose a decoded signal, assertions must verify the resulting assignment or state, not the input conditions themselves.
    Assertions must respect the RTL’s execution semantics and priority. Do not assume mutual exclusivity of conditions unless it is explicitly enforced in the RTL (e.g., unique case, priority case).
    Each property must check exactly one functional requirement and must be capable of failing meaningfully when the RTL behavior is incorrect. Avoid vacuous implications and redundant guards.
    Default behavior must be verified by checking the explicit default output or state, not by negating all other conditions.
    If the logic is combinational, use simple asserts. If the logic is sequential, respect the delays, clock and reset signal activations,
    Handle SystemVerilog 4-state semantics correctly. Remember that inside evaluates to 0 (not X) when operands contain X or Z. Use $isunknown() only when it adds semantic value.
    Assertions must be compatible with both simulation and formal verification tools.
    Output only valid SystemVerilog code. Do not include explanations, comments, markdown, or non-SystemVerilog text.
    When a functional assignment depends on the previous value of a signal (e.g., result = result + opcode or enable = ~enable), the property may reference the prior value using $past(signal) to accurately capture the observable functional effect while respecting RTL semantics (e.g., result == $past(result) or enable == ~$past(enable))

    Few-Shot Examples: The following examples illustrate the expected transformation from RTL code to properties and assertions. Use them strictly as behavioral and structural reference. 

    Example 1

    module ex1_mux_case (
    input  logic        clk,
    input  logic [1:0]  sel,
    input  logic [31:0] a, b, c, d,
    output logic [31:0] y);

    case (sel) 
        2'b00: y = a; 
        2'b01: y = b; 
        2'b10: y = c; 
        default: y = d; 
    endcase 

    endmodule;

    Properties: 

    module ex1_mux_case (
    input  logic        clk,
    input  logic [1:0]  sel,
    input  logic [31:0] a, b, c, d,
    output logic [31:0] y);

        property p_y_a_assign; 
        @(posedge clk) (sel == 2'b00) |-> (y == a); 
        endproperty 
        assert property (p_y_a_assign); 

        property p_y_b_assign; 
        @(posedge clk) (sel == 2'b01) |-> (y == b); 
        endproperty 
        assert property (p_y_b_assign); 

        property p_y_c_assign; 
        @(posedge clk) (sel == 2'b10) |-> (y == c); 
        endproperty 
        assert property (p_y_c_assign); 

        property p_y_d_assign; 
        @(posedge clk) (sel != 2'b00 && sel != 2'b01 && sel != 2'b10) |-> (y == d); 
        endproperty 
        assert property (p_y_d_assign); 

    endmodule;

    Example 2

    module ex2_counter (
    input  logic        clk,
    input  logic [1:0]  ctrl,
    output logic [31:0] count);

        localparam INC = 2'd0;
        localparam DEC = 2'd1;

        always_ff @(posedge clk) begin
            case (ctrl)
                INC:     count <= count + 1;
                DEC:     count <= count - 1;
                default: count <= count;
            endcase
        end

    endmodule;

    Properties: 

    module ex2_counter (
    input  logic        clk,
    input  logic [1:0]  ctrl,
    output logic [31:0] count);

        localparam INC = 2'd0;
        localparam DEC = 2'd1;

        property p_count_inc_assign;
            @(posedge clk) (ctrl == INC) |-> (count == $past(count) + 1);
        endproperty
        assert property (p_count_inc_assign);

        property p_count_dec_assign;
            @(posedge clk) (ctrl == DEC) |-> (count == $past(count) - 1);
        endproperty
        assert property (p_count_dec_assign);

        property p_count_default_assign;
            @(posedge clk)
            (ctrl != INC && ctrl != DEC) |-> (count == $past(count));
        endproperty
        assert property (p_count_default_assign);

    endmodule


    Example 3

    module simple_logic (
        input  logic a,
        input  logic b,
        input  logic [1:0] sel,
        output logic y,
        output logic z
    );

        always_comb begin
            y = 1'b0;
            z = 1'b0;

            case (sel)
                2'b00: y = a & b;
                2'b01: y = a | b;
                2'b10: z = a ^ b;
                default: z = ~(a | b);
            endcase
        end

    endmodule


    Properties: 

    module simple_logic_properties(
        input logic a,
        input logic b,
        input logic [1:0] sel,
        output logic y,
        output logic z
    );

        property p_y_and;
            (sel == 2'b00) |=> (y == (a & b));
        endproperty
        assert property (p_y_and);

        property p_y_or;
            (sel == 2'b01) |=> (y == (a | b));
        endproperty
        assert property (p_y_or);

        property p_z_xor;
            (sel == 2'b10) |=> (z == (a ^ b));
        endproperty
        assert property (p_z_xor);        

        property p_z_nor;
            (sel == 2'b11) |=> (z == ~(a | b));
        endproperty
        assert property (p_z_nor);

    endmodule

    Example 4

    module ex4_fsm (
        input  logic clk,
        input  logic rst_n,
        input  logic start,
        input  logic done,
        output logic [1:0] state,
        output logic [1:0] next_state);

        localparam IDLE = 2'd0;
        localparam RUN  = 2'd1;
        localparam DONE = 2'd2;

        always_ff @(posedge clk or negedge rst_n) begin 
        if (!rst_n) 
            state <= IDLE; 
        else        
            state <= next_state; 
        end 

        always_comb begin 
            next_state = state; 
            case (state) 
                IDLE: if (start) next_state = RUN; 
                RUN:  if (done)  next_state = DONE; 
                DONE:            next_state = IDLE; 

            endcase 

        end

    endmodule;

    Properties: 

    module ex4_fsm (
    input  logic clk,
    input  logic rst_n,
    input  logic start,
    input  logic done,
    output logic [1:0] state,
    output logic [1:0] next_state);

        localparam IDLE = 2'd0;
        localparam RUN  = 2'd1;
        localparam DONE = 2'd2;

        property p_next_idle_assign;
            (state == IDLE && start) |=> (next_state == RUN);
        endproperty
        assert property (p_next_idle_assign);

        property p_next_run_assign;
            (state == RUN && done) |=> (next_state == DONE);
        endproperty
        assert property (p_next_run_assign);

        property p_next_done_assign;
            (state == DONE) |=> (next_state == IDLE);
        endproperty
        assert property (p_next_done_assign);

    endmodule


    Example 5

    module mux_3to1 #(
    parameter WIDTH = 8
    )(
        input  logic [1:0]       sel,
        input  logic [WIDTH-1:0] a,
        input  logic [WIDTH-1:0] b,
        input  logic [WIDTH-1:0] c,
        output logic [WIDTH-1:0] y
    );

        always_comb begin 
        y = '0; 
        case (sel) 
            2'd0: y = a; 
            2'd1: y = b; 
            2'd2: y = c; 
        endcase 
    end 

    endmodule


    Properties: 

    module comb_seq_example_properties (
        input logic clk,
        input logic rst_n,
        input logic a,
        input logic b,
        input logic sel,
        output logic y,
        output logic z,
        output logic q
    );

        always_comb begin
            if (sel == 2'd0) assert(y == a);
            else if (sel == 2'd1) assert(y == b);
            else if (sel == 2'd2) assert(y == c);
            else if (sel == 2'd3) assert(y == '0); // Validates the y = '0 initialization
        end

    endmodule


    Input Format: The user will provide: 

    A SystemVerilog case statement 
    All signals referenced are assumed to be in scope 

    Output Format: 

    SystemVerilog code only inside of this code block markdown: 

    ```systemverilog  

    ```

    Template for a generated module:

    module_name_assertions(**parameters**);
        **inner_variables**
        **inner_functions**
        **property_&_assert**
    endmodule;

    Each property must be immediately followed by its assert property 

    Task: Transform the following SystemVerilog case statement into a valid module with assertion properties according to the rules above: 

    {module}
    """

    return EXPERIMENT_2_CALL