def experiment2_simple_call(code: str) -> str:
    #Code made by Geralt of Rivia
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

    {code}
    """

    return EXPERIMENT_2_CALL

def experiment2_only_properties_call(code: str):
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
    Use @(posedge clk) as the sampling event unless another clock is explicitly specified. Do not invent clocks, resets, signals, or conditions that are not present in the RTL. Do not use disable iff unless explicitly instructed.
    Handle SystemVerilog 4-state semantics correctly. Remember that inside evaluates to 0 (not X) when operands contain X or Z. Use $isunknown() only when it adds semantic value.
    Assertions must be compatible with both simulation and formal verification tools.
    Output only valid SystemVerilog code. Do not include explanations, comments, markdown, or non-SystemVerilog text.
    When a functional assignment depends on the previous value of a signal (e.g., result = result + opcode or enable = ~enable), the property may reference the prior value using $past(signal) to accurately capture the observable functional effect while respecting RTL semantics (e.g., result == $past(result) or enable == ~$past(enable))

    Few-Shot Examples: The following examples illustrate the expected transformation from RTL code to properties and assertions. Use them strictly as behavioral and structural reference. 

    Example 1

    case (sel) 
        2'b00: y = a; 
        2'b01: y = b; 
        2'b10: y = c; 
        default: y = d; 
    endcase 

    Properties: 

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

    Example 2

    always_ff @(posedge clk) begin 
        case (ctrl) 
            INC: count <= count + 1; 
            DEC: count <= count - 1; 
            default: count <= count; 
        endcase 
    end 

    Properties: 

    property p_count_inc_assign; 
    @(posedge clk) (ctrl == INC) |-> (count == count + 1); 
    endproperty 

    assert property (p_count_inc_assign); 

    property p_count_dec_assign; 
    @(posedge clk) (ctrl == DEC) |-> (count == count - 1); 
    endproperty 

    assert property (p_count_dec_assign); 

    property p_count_default_assign; 
    @(posedge clk) (ctrl != INC && ctrl != DEC) |-> (count == count); 
    endproperty 

    assert property (p_count_default_assign); 

    Example 3

    case (addr) 
        [0:15]:   region = LOW; 
        [16:31]:  region = MID; 
        default:  region = HIGH; 
    endcase 

    Properties: 

    property p_region_low_assign; 
    @(posedge clk) (addr >= 0 && addr <= 15) |-> (region == LOW); 
    endproperty 

    assert property (p_region_low_assign); 

    property p_region_mid_assign; 
    @(posedge clk) (addr >= 16 && addr <= 31) |-> (region == MID); 
    endproperty 

    assert property (p_region_mid_assign); 

    property p_region_default_assign; 
    @(posedge clk) (addr < 0 || addr > 31) |-> (region == HIGH); 
    endproperty 

    assert property (p_region_default_assign); 

    Example 4

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

    Properties: 

        // 1. Reset Check: State must be IDLE after reset
    property p_reset_state;
        @(posedge clk) !rst_n |=> (state == IDLE);
    endproperty
    
    // 2. State Transition Check: State must follow next_state logic
    property p_state_update;
        @(posedge clk) disable iff (!rst_n)
        (state == $past(next_state));
    endproperty
    
    // 3. Functional Sequence: IDLE to RUN
    property p_idle_to_run;
        @(posedge clk) disable iff (!rst_n)
        (state == IDLE && start) |=> (state == RUN);
    endproperty
    
    // 4. Functional Sequence: RUN to DONE
    property p_run_to_done;
        @(posedge clk) disable iff (!rst_n)
        (state == RUN && done) |=> (state == DONE);
    endproperty
    
    // 5. Functional Sequence: DONE to IDLE
    property p_done_to_idle;
        @(posedge clk) disable iff (!rst_n)
        (state == DONE) |=> (state == IDLE);
    endproperty
    
    // Assertion Directives
    assert_reset:        assert property (p_reset_state);
    assert_state_update: assert property (p_state_update);
    assert_trans_run:    assert property (p_idle_to_run);
    assert_trans_done:   assert property (p_run_to_done);
    assert_trans_idle:   assert property (p_done_to_idle);

    always_comb begin
        case (state)
            IDLE: begin
                if (start) assert(next_state == RUN);
                else       assert(next_state == IDLE);
            end
            RUN: begin
                if (done)  assert(next_state == DONE);
                else       assert(next_state == RUN);
            end
            DONE: begin
                assert(next_state == IDLE);
            end
            default: begin
                // Ensures state doesn't enter an undefined encoding
                assert(state == IDLE || state == RUN || state == DONE);
            end
        endcase
    end

    Example 5

    always_comb begin 
        y = '0; 
        case (sel) 
            2'd0: y = a; 
            2'd1: y = b; 
            2'd2: y = c; 
        endcase 
    end 

    Properties: 

    always_comb begin
    if (sel == 2'd0) assert(y == a);
    else if (sel == 2'd1) assert(y == b);
    else if (sel == 2'd2) assert(y == c);
    else if (sel == 2'd3) assert(y == '0); // Validates the y = '0 initialization
    end

    Input Format: The user will provide: 

    A SystemVerilog case statement 
    All signals referenced are assumed to be in scope 

    Output Format: 

    SystemVerilog code only inside of this code block markdown: 
    
    ```systemverilog  
        
    ```
    Each property must be immediately followed by its assert property 

    Task: Transform the following SystemVerilog case statement into assertion properties according to the rules above: 

    {code}
    """

    return EXPERIMENT_2_CALL