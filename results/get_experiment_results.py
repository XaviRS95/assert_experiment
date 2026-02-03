import pandas as pd

df = pd.read_csv("sv_combined_results.csv")

# -----------------------------
# Helper function
# -----------------------------
def compute_stats(prefix):
    result_col = f"{prefix}_result"
    time_col = f"{prefix}_time(s)"
    prompt_col = f"{prefix}_prmpt_tkns"
    resp_col = f"expr{prefix[3:]}_resp_tkns"  # handles exp1 / exp2_ai / exp2_regex

    total = len(df)

    ok_pct = round((df[result_col] == "OK").sum() / total * 100, 2)

    return {
        "experiment": prefix,
        "ok_percent": ok_pct,
        "mean_prompt_tokens": df[prompt_col].mean(),
        "mean_output_tokens": df[resp_col].mean(),
        "avg_time_seconds": df[time_col].mean(),
    }

# -----------------------------
# Compute stats
# -----------------------------
stats = []

stats.append(compute_stats("exp1"))
stats.append(compute_stats("exp2_ai"))
stats.append(compute_stats("exp2_regex"))

summary_df = pd.DataFrame(stats)

# Optional: nicer experiment names
summary_df["experiment"] = summary_df["experiment"].map({
    "exp1": "Experiment 1",
    "exp2_ai": "Experiment 2 Full AI",
    "exp2_regex": "Experiment 2 Regex Aided",
})

# Round numeric columns for presentation
summary_df = summary_df.round({
    "mean_prompt_tokens": 2,
    "mean_output_tokens": 2,
    "avg_time_seconds": 2,
})

# -----------------------------
# Save CSV
# -----------------------------
summary_df.to_csv("sv_experiment_summary.csv", index=False)

print("✅ Summary written to sv_experiment_summary.csv")
print(summary_df)
