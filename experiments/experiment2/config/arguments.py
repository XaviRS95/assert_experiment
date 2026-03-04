import argparse


def parse_arguments():
    """Parse command line arguments for experiment 3"""
    parser = argparse.ArgumentParser(description="Run SystemVerilog Experiment 3 (TGTS Generation).")

    parser.add_argument(
        "--model",
        type=str,
        default="qwen3-coder:30b",
        help="Model name in Ollama"
    )
    parser.add_argument(
        "--path",
        type=str,
        default="case_easy_comb.csv",
        help="Path to the source CSV"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Explicit output filename"
    )

    return parser.parse_args()


def get_output_filename(args):
    """Generate output filename if not provided"""
    if args.output:
        return args.output
    return f"sv_results_{args.model.replace(':', '_')}_3.csv"