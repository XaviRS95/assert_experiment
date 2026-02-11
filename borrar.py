import re


def clean_reset_logic(text, signal_name):
    sig = re.escape(signal_name)

    # 1. Pattern to match the reset signal and any comparison to a value (e.g., == 1'b1)
    # Matches: rst_n, rst_n == 1, rst_n == 1'b1, !rst_n, etc.
    val_pattern = r"(\d+'b[01xXzZ]|\d+)"  # Matches 1'b1, 0, 1, etc.
    comparison = rf"(?:\s*(?:==|!=)\s*{val_pattern})?"
    reset_core = rf"(?:!\s*)?\(?\b{sig}\b{comparison}\)?"

    # 2. Check for the reset logic and remove it along with leading/trailing operators
    # Pattern A: Matches "reset && ..." or "reset || ..."
    trailing_op = rf"{reset_core}\s*(?:&&|\|\|)\s*"
    # Pattern B: Matches "... && reset" or "... || reset"
    leading_op = rf"\s*(?:&&|\|\|)\s*{reset_core}"

    # Execute removals
    new_text = re.sub(trailing_op, '', text)
    new_text = re.sub(leading_op, '', new_text)
    new_text = re.sub(reset_core, '', new_text)

    # 3. Final Cleanup
    # Remove any stray "!()" or "()" left behind
    new_text = re.sub(r'!\s*\(\s*\)', '', new_text)
    new_text = re.sub(r'\(\s*\)', '', new_text)

    # Clean up double spaces
    new_text = re.sub(r'\s+', ' ', new_text).strip()

    return new_text


# --- Test Case ---
signal = "rst_n"
test_input = "WHEN state == 2'b00 && !(rst_n == 1'b1) THEN state[t+1] == 2'b01"

cleaned = clean_reset_logic(test_input, signal)

print(f"Input : {test_input}")
print(f"Output: {cleaned}")
# --- Test ---
signal = "rst_n"
examples = [
    f"!{signal} && state == SAFE",
    f"{signal} == 1 || mode == DEBUG",
    f"{signal} == 0",
    f"state == DANGER && {signal}",
    f" WHEN state == !({signal} == 1'b1) && 2'b00 THEN state[t+1] == 2'b01"

]

for ex in examples:
    result = clean_reset_logic(ex, signal)
    print(f"Input:  {ex}")
    print(f"Output: {result}\n")