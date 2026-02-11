def experiment3_sv_to_tgts(code: str) -> str:
    TEMPLATE = f"""
    You are a hardware-semantics extraction engine.
    
    Your job is to read a SystemVerilog module and rewrite it as a
    Typed Guarded Transition System.
    
    A Typed Guarded Transition System is a formal description of:
      • signals and their types
      • clocks and resets
      • how state and registers evolve over time
      • how case statements and if statements control transitions
    
    You must extract the exact behavior of the RTL without guessing
    or simplifying.
    
    1) WHAT YOU MUST OUTPUT
    
    You must output only the Typed Guarded Transition System.
    
    The output must be structured using only these sections:
    
    SIGNALS
    EVENTS
    FUNCTIONS
    RULE
    
    Do not output any natural language explanation.
    
    2) TIME MODEL
    
    All sequential logic is expressed using explicit time indices.
    
    Use:
      x[t]   = value of x in the current clock cycle
      x[t+1] = value of x in the next clock cycle
    
    Never use x', next(x), or temporal operators.
    Always use [t] and [t+1].
    
    3) CLOCKS AND RESETS
    
    If the RTL has:
    
      always_ff @(posedge clk)
    
    Then every rule for that block must include:
      EVENT(posedge(clk))
    
    If the RTL has an asynchronous reset:
    
      always_ff @(posedge clk or negedge rst)
    
    Then you must create a rule:
    
      RULE RST
        WHEN EVENT(negedge(rst))
        THEN <reset assignments>
    
    If the reset is synchronous, it must appear as:
      WHEN EVENT(posedge(clk)) AND rst == 0
    
    4) SIGNAL DECLARATION
    
    Every signal must be declared in SIGNALS.
    
    Use these types:
      bit
      bit[N:M]
      enum {{A, B, C, ...}}
    
    State variables and registers must be marked:
      clocked(clk)
      reset(rst, async|sync, value=V)
    
    Example:
      state : enum {{IDLE, RUN}} clocked(clk) reset(rst_n, async, value=IDLE)
    
    5) CASE AND IF LOGIC
    
    Every branch of every if and case statement must become a RULE.
    
    Each RULE has:
      WHEN <guard>
      THEN <assignments>
    
    Rules must be:
      • mutually exclusive
      • collectively exhaustive for each state
    
    6) HOLD BEHAVIOR
    
    If a register is not assigned in a branch,
    it must hold its previous value.
    
    This must be written explicitly:
      x[t+1] == x[t]
    
    Never leave a register without an assignment.
    
    7) case, casez, casex
    
    Normal case:
      use equality (==)
    
    casez:
      use pattern matching:
        MATCH(signal[t], "pattern", CASEZ)
    
    casex:
      use:
        MATCH(signal[t], "pattern", CASEX)
    
    Use '?' for wildcards.
    
    Example:
      4'b01??  →  MATCH(req[t], "01??", CASEZ)
    
    Default must be written as:
      NOT (pattern1 OR pattern2 OR ...)
    
    8) BIT SELECTS
    
    For expressions like:
      req[selected]
    
    Write:
      req[t][ selected[t] ]
    
    9) FUNCTIONS
    
    If the RTL calls a function, declare it:
    
    FUNCTION name(arg1, arg2) : return_type
    
    Then use it symbolically:
      name(x[t], y[t]) == value
    
    Do NOT expand or rewrite the function.
    
    10) ILLEGAL STATE HANDLING
    
    For every enum state, you must add a rule:
    
      RULE ILLEGAL
        WHEN EVENT(posedge(clk)) AND state[t] ∉ {{all valid states}}
        THEN state[t+1] == <reset or recovery state>
    
    11) INPUT
    
    The SystemVerilog module will be provided below.
    
    {code}
    
    
    12) OUTPUT
    
    Produce the complete Typed Guarded Transition System.
    
    Do not explain.
    Do not summarize.
    Do not use abbreviations.
    Only emit SIGNALS, EVENTS, FUNCTIONS, and RULE blocks.
    """

    return TEMPLATE



def comb_to_tgts_prompt(parameters: str, ports: str, inner_vars:str, block: str):
    """

    :param parameters:
    :param ports:
    :param block:
    :param inner_vars:
    :return:
    """

    TEMPLATE = f"""

ROLE: SystemVerilog → TGTS translator (COMBINATIONAL ONLY).
    
IMPORTANT:
- This module is PURELY COMBINATIONAL.
- Do NOT introduce clocks, events, or t/t+1.
- LOGIC OPERATORS: Use '&&', '||', '!', '==', '!=', '>', '<', '<=', '>='.
- Use ONLY same-cycle assignments respecting the original variable names:  == 
- Do NOT invent signals or use dummy variables.
- Do NOT explain.
- ONLY output TGTS rules only.
- IGNORE ALL UNCONDITIONAL ASSIGNATIONS.

TASK:
Convert the SystemVerilog block below into TGTS rules.
    
Follow this TGTS format EXACTLY:

RULE <signal_name>_<index>
  WHEN <boolean_expression>
  THEN <signal_name> == <literal_value>

CONSTRAINTS:
1. The <signal_name> in the THEN clause MUST match the original SystemVerilog variable name (e.g., tl_o_d_valid).
2. NEVER use 'x' or placeholder variables.
3. Every RULE must be self-contained.
    
Use:
- RULE per assignment or conditional branch
- DO NOT use ELSE statements
- WHEN true for unconditional assignments
- Explicit guards for if statements
- FUNCTION(...) for function calls
- Explicit default rules if a signal is conditionally assigned
    
    MODULE PARAMETERS:
    {parameters}
    
    PORTS:
    {ports}
    
    AUXILIARY VARIABLES:
    {inner_vars}
    
    COMBINATIONAL BLOCK:
    {block}
    
    OUTPUT:
    TGTS only.

    """

    return TEMPLATE


def seq_to_tgts_prompt(parameters: str, ports: str, inner_vars: str, block: str):
    """

    :param parameters:
    :param ports:
    :param block:
    :param inner_vars:
    :return:
    """

    TEMPLATE = f"""

ROLE: SystemVerilog → TGTS translator (SEQUENTIAL ONLY).

TGTS GRAMMAR RUES

IMPORTANT:
- This module is PURELY SEQUENTIAL.
- NEVER include |=> or |->
- TEMPORAL NOTATION: Use [t] for current and [t+1] for the next cycle
- DELAYS: Represent #N as [t + N units].
- LOGIC OPERATORS: Use '&&', '||', '!', '==', '!=', '>', '<', '<=', '>='.
- AVOID using IF, ELSE clauses. Every branch must be its own RULE with a unique, full guard.  
- IGNORE ALL UNCONDITIONAL ASSIGNMENTS. Include only assignemnts inside case, if/else and for loops.
- clock signals are forbidden to be used in TGTS clauses
- Do NOT invent signals or use dummy variables.
- Do NOT explain.
- ONLY output TGTS rules only.


TASK:
Convert the SystemVerilog block below into TGTS rules.

Follow this TGTS format EXACTLY:

RULE <signal_name>_<index>
  WHEN <boolean_expression_at_t>
  THEN <signal_name>[t+1] == <expression_at_t>

CONSTRAINTS:
1. NEVER use 'x' or placeholder variables.
2. Every RULE must be self-contained.

Use:
- RULE per assignment or conditional branch
- DO NOT use IF ELSE statements
- Explicit guards for if statements
- FUNCTION(...) for function calls
- Explicit default rules if a signal is conditionally assigned

MODULE PARAMETERS:

{parameters}

PORTS:

{ports}

AUXILIARY VARIABLES:

{inner_vars}

SEQUENTIAL BLOCK:

{block}

OUTPUT:
TGTS only.

"""

    return TEMPLATE