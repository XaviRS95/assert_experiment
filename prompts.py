def experiment1_simple_call(code:str) -> str:
    EXPERIMENT_1_SIMPLE_CALL = f"""
    Using this SystemVerilog code, generate only the property assertion to test the given code without the original module:
    
    {code}
    """

    return EXPERIMENT_1_SIMPLE_CALL


def experiment2_simple_call(code: str) -> str:
    EXPERIMENT_1_SIMPLE_CALL = f"""
    Role: You are an expert in SystemVerilog RTL design and SystemVerilog Assertions (SVA), specialized in generating assertions from procedural case statements. 

    Objective: Given a SystemVerilog case statement provided by the user, generate SystemVerilog Assertion (SVA) code that verifies the behavior described by the case statement. 
    
    SYSTEMVERILOG ASSERTION GENERATION RULES (MANDATORY)
    
    Assertions must verify functional behavior, not mirror control logic.
    Generate one distinct property and one corresponding assert property for each observable functional effect (signal assignment, state update, output value). 
    Do not group multiple functional checks in a single property. 
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
    
    property p_y_a;
      @(posedge clk) (sel == 2'b00) |-> (y == a);
    endproperty
    assert property (p_y_a);
    
    property p_y_b;
      @(posedge clk) (sel == 2'b01) |-> (y == b);
    endproperty
    assert property (p_y_b);
    
    property p_y_c;
      @(posedge clk) (sel == 2'b10) |-> (y == c);
    endproperty
    assert property (p_y_c);
    
    property p_y_d;
      @(posedge clk) (sel != 2'b00 && sel != 2'b01 && sel != 2'b10) |-> (y == d);
    endproperty
    assert property (p_y_d);

    Example 2
    
    always_ff @(posedge clk) begin
      case (ctrl)
        INC: count <= count + 1;
        DEC: count <= count - 1;
        default: count <= count;
      endcase
    end

    Properties: 
    
    property p_inc;
      @(posedge clk) (ctrl == INC) |-> (count == $past(count) + 1);
    endproperty
    assert property (p_inc);
    
    property p_dec;
      @(posedge clk) (ctrl == DEC) |-> (count == $past(count) - 1);
    endproperty
    assert property (p_dec);
    
    property p_hold;
      @(posedge clk) (ctrl != INC && ctrl != DEC) |-> (count == $past(count));
    endproperty
    assert property (p_hold);

    Example 3
    
    casez (addr)
      8'b10??????: hit = 1;
      8'b01??????: hit = 0;
      default:    hit = 0;
    endcase

    Properties: 
    
    property p_hit_hi;
      @(posedge clk) (addr[7:6] == 2'b10) |-> (hit == 1);
    endproperty
    assert property (p_hit_hi);
    
    property p_hit_lo;
      @(posedge clk) (addr[7:6] == 2'b01) |-> (hit == 0);
    endproperty
    assert property (p_hit_lo);

    
    Example 4
    
    case (op)
      2'b00: begin
        case (func)
          2'b00: y = a + b;
          2'b01: y = a - b;
        endcase
      end
      2'b01: y = a & b;
    endcase

    Properties: 
    
    property p_add;
      @(posedge clk) (op == 2'b00 && func == 2'b00) |-> (y == a + b);
    endproperty
    assert property (p_add);
    
    property p_sub;
      @(posedge clk) (op == 2'b00 && func == 2'b01) |-> (y == a - b);
    endproperty
    assert property (p_sub);
    
    property p_and;
      @(posedge clk) (op == 2'b01) |-> (y == (a & b));
    endproperty
    assert property (p_and);
    
    Example 5
    
    case (mode)
      2'b00: begin en = 0; valid = 0; end
      2'b01: begin en = 1; valid = 0; end
      2'b10: begin en = 1; valid = 1; end
    endcase

    Properties: 
    
    property p_valid_implies_en;
      @(posedge clk) valid |-> en;
    endproperty
    assert property (p_valid_implies_en);
    
    property p_mode_valid;
      @(posedge clk) (mode == 2'b10) |-> (valid == 1 && en == 1);
    endproperty
    assert property (p_mode_valid);

    Example 6
    
    always_comb begin
      case (sel)
        2'b01: y = d;
      endcase
    end

    Properties:
    
    property p_update;
      @(posedge clk) (sel == 2'b01) |-> (y == d);
    endproperty
    assert property (p_update);
    
    property p_hold;
      @(posedge clk) (sel != 2'b01) |-> (y == $past(y));
    endproperty
    assert property (p_hold);
    
    Example 7
    
    priority casez (a)
      8'b1???????: y = 1;
      8'b10??????: y = 0;
      default:    y = 0;
    endcase

    
    Properties:
    
    property p_priority_hi;
      @(posedge clk) (a[7] == 1'b1) |-> (y == 1);
    endproperty
    assert property (p_priority_hi);
    
    property p_priority_lo;
      @(posedge clk) (a[7:6] == 2'b10) |-> (y == 0);
    endproperty
    assert property (p_priority_lo);
    
    
    
    Input Format: The user will provide: 

    A SystemVerilog case statement 
    All signals referenced are assumed to be in scope 
    
    Output Format: 
    
    SystemVerilog code only 
    Each property must be immediately followed by its assert property 
    
    Task: Transform the following SystemVerilog case statement into assertion properties according to the rules above: 

    {code}
    """

    return EXPERIMENT_1_SIMPLE_CALL