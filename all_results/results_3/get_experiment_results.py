import sys
import os
import pandas as pd

# -----------------------------
# CLI argument
# -----------------------------
if len(sys.argv) != 2:
    print("Usage: python summarize_results.py <experiment_folder>")
    sys.exit(1)

folder = sys.argv[1]

combined_path = os.path.join(folder, "sv_combined_results.csv")
output_path = os.path.join(folder, "sv_experiment_summary.csv")

# -----------------------------
# Load combined dataset
# -----------------------------
df = pd.read_csv(combined_path)

# -----------------------------
# Helper function
# -----------------------------
def compute_stats(prefix, resp_suffix):
    result_col = f"{prefix}_result"
    time_col = f"{prefix}_time(s)"
    prompt_col = f"{prefix}_prmpt_tkns"
    resp_col = resp_suffix

    total = len(df)

    ok_pct = round((df[result_col] == "OK").sum() / total * 100, 2)

    return {
        "experiment": prefix,
        "syntax_correct(%)": ok_pct,
        "mean_prompt_tokens": df[prompt_col].mean(),
        "mean_output_tokens": df[resp_col].mean(),
        "avg_time_seconds": df[time_col].mean(),
    }

# -----------------------------
# Experiments registry
# -----------------------------
experiments = [
    ("exp1", "exp1_resp_tkns"),
    ("exp2", "exp2_resp_tkns"),
    ("exp3", "exp3_resp_tkns"),
]

# -----------------------------
# Compute stats
# -----------------------------
stats = []

for prefix, resp_col in experiments:
    stats.append(compute_stats(prefix, resp_col))

summary_df = pd.DataFrame(stats)

# Friendly names
summary_df["experiment"] = summary_df["experiment"].map({
    "exp1": "Experiment 1",
    "exp2": "Experiment 2",
    "exp3": "Experiment 3",
})

# Round numeric columns
summary_df = summary_df.round({
    "mean_prompt_tokens": 2,
    "mean_output_tokens": 2,
    "avg_time_seconds": 2,
})

# -----------------------------
# Save
# -----------------------------
summary_df.to_csv(output_path, index=False)

print(f"✅ Summary written to {output_path}")
print(summary_df)
