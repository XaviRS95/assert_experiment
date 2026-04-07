import argparse


def parse_arguments():
    """Parse command line arguments for experiment 3"""
    parser = argparse.ArgumentParser(description="Generate Testbench for all OK SystemVerilog modules")

    parser.add_argument(
        "--path",
        type=str,
        default="all_results/results_7/experiment3/sv_results_qwen2.5-coder_14b_3.csv",
        help="Path to the source CSV"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Explicit output filename"
    )

    return parser.parse_args()