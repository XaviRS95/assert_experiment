import pandas as pd

import pandas as pd

# -----------------------------
# File paths
# -----------------------------
cases_path = "sv_cases.csv"

exp1_path = "sv_results_1_deepseek-coder-v2_16b.csv"
exp2_ai_path = "sv_results_2_FULL_AI_deepseek-coder-v2_16b.csv"
exp2_regex_path = "sv_results_2_REGEX_AIDED_deepseek-coder-v2_16b.csv"

# -----------------------------
# Load datasets
# -----------------------------
cases = pd.read_csv(cases_path)

exp1 = pd.read_csv(exp1_path)
exp2_ai = pd.read_csv(exp2_ai_path)
exp2_regex = pd.read_csv(exp2_regex_path)

# -----------------------------
# Replace original_code in all experiments
# (row-aligned copy)
# -----------------------------
for df in (exp1, exp2_ai, exp2_regex):
    df["original_code"] = cases["original_code"]

# -----------------------------
# Rename columns per experiment
# -----------------------------

exp1 = exp1.rename(columns={
    "generated_code": "exp1_generated_code",
    "iverilog_output": "exp1_result",
    "time(s)": "exp1_time(s)",
    "prompt_tkns": "exp1_prmpt_tkns",
    "output_tkns": "expr1_resp_tkns",
})

exp2_ai = exp2_ai.rename(columns={
    "generated_code": "exp2_ai_generated_code",
    "iverilog_output": "exp2_ai_result",
    "time(s)": "exp2_ai_time(s)",
    "prompt_tkns": "exp2_ai_prmpt_tkns",
    "output_tkns": "expr2_ai_resp_tkns",
})

exp2_regex = exp2_regex.rename(columns={
    "generated_code": "exp2_regex_generated_code",
    "iverilog_output": "exp2_regex_result",
    "time(s)": "exp2_regex_time(s)",
    "prompt_tkns": "exp2_regex_prmpt_tkns",
    "output_tkns": "expr2_regex_resp_tkns",
})

# -----------------------------
# Merge everything on original_code
# -----------------------------

final_df = (
    exp1.merge(exp2_ai, on="original_code")
        .merge(exp2_regex, on="original_code")
)

# Keep only desired columns (clean ordering)

final_df = final_df[[
    "original_code",

    "exp1_generated_code",
    "exp1_result",
    "exp1_time(s)",
    "exp1_prmpt_tkns",
    "expr1_resp_tkns",

    "exp2_ai_generated_code",
    "exp2_ai_result",
    "exp2_ai_time(s)",
    "exp2_ai_prmpt_tkns",
    "expr2_ai_resp_tkns",

    "exp2_regex_generated_code",
    "exp2_regex_result",
    "exp2_regex_time(s)",
    "exp2_regex_prmpt_tkns",
    "expr2_regex_resp_tkns",
]]

# -----------------------------
# Save final dataset
# -----------------------------
final_df.to_csv("sv_combined_results.csv", index=False)

print("✅ Combined dataset written to sv_combined_results.csv")


