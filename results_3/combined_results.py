import sys
import os
import pandas as pd

# -----------------------------
# CLI argument
# -----------------------------
if len(sys.argv) != 2:
    print("Usage: python combine_results.py <experiment_folder>")
    sys.exit(1)

folder = sys.argv[1]
model_name = os.path.basename(folder.rstrip("/"))

# -----------------------------
# File paths
# -----------------------------
cases_path = "sv_cases.csv"

exp1_path = os.path.join(folder, f"sv_results_{model_name}_1.csv")
exp2_path = os.path.join(folder, f"sv_results_{model_name}_2.csv")
exp3_path = os.path.join(folder, f"sv_results_{model_name}_3.csv")

output_path = os.path.join(folder, "sv_combined_results.csv")

# -----------------------------
# Load datasets
# -----------------------------
cases = pd.read_csv(cases_path)

exp1 = pd.read_csv(exp1_path)
exp2 = pd.read_csv(exp2_path)
exp3 = pd.read_csv(exp3_path)

# -----------------------------
# Safety: row alignment
# -----------------------------
print(len(exp1), len(cases))
print(len(exp2), len(cases))
print(len(exp3), len(cases))
assert len(exp1) == len(cases)
assert len(exp2) == len(cases)
assert len(exp3) == len(cases)

# -----------------------------
# Replace original_code
# -----------------------------
for df in (exp1, exp2, exp3):
    df["original_code"] = cases["original_code"]

# -----------------------------
# Rename columns
# -----------------------------

exp1 = exp1.rename(columns={
    "generated_code": "exp1_generated_code",
    "iverilog_output": "exp1_result",
    "time(s)": "exp1_time(s)",
    "prompt_tkns": "exp1_prmpt_tkns",
    "output_tkns": "exp1_resp_tkns",
})

exp2 = exp2.rename(columns={
    "generated_code": "exp2_generated_code",
    "iverilog_output": "exp2_result",
    "time(s)": "exp2_time(s)",
    "prompt_tkns": "exp2_prmpt_tkns",
    "output_tkns": "exp2_resp_tkns",
})

exp3 = exp3.rename(columns={
    "generated_code": "exp3_generated_code",
    "iverilog_output": "exp3_result",
    "time(s)": "exp3_time(s)",
    "prompt_tkns": "exp3_prmpt_tkns",
    "output_tkns": "exp3_resp_tkns",
})

# -----------------------------
# Merge all experiments
# -----------------------------
final_df = (
    exp1
    .merge(exp2, on="original_code")
    .merge(exp3, on="original_code")
)

# -----------------------------
# Column ordering
# -----------------------------
final_df = final_df[[
    "original_code",

    "exp1_generated_code",
    "exp1_result",
    "exp1_time(s)",
    "exp1_prmpt_tkns",
    "exp1_resp_tkns",

    "exp2_generated_code",
    "exp2_result",
    "exp2_time(s)",
    "exp2_prmpt_tkns",
    "exp2_resp_tkns",

    "exp3_generated_code",
    "exp3_result",
    "exp3_time(s)",
    "exp3_prmpt_tkns",
    "exp3_resp_tkns",
]]

# -----------------------------
# Save
# -----------------------------
final_df.to_csv(output_path, index=False)

print(f"✅ Combined dataset written to {output_path}")