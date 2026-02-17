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
- ONLY use variable names that are in the original module without any modification
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
- clock and reset signals are forbidden to be used in TGTS clauses
- ONLY use variable names that are in the original module without any modification
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