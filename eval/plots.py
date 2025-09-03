# eval/plots.py
import argparse, os, pandas as pd, json
import matplotlib.pyplot as plt
from glob import glob

def load_time_series(logdir="logs"):
    """Return DataFrame with columns [run_id, strategy, tick, rescued, deaths, ...]"""
    rows = []
    for metrics_file in glob(os.path.join(logdir, "strategy=*/run=*/metrics.jsonl")):
        parts = metrics_file.split(os.sep)
        strategy = parts[-3].split("=")[1]
        run_id = parts[-2].split("=")[1]
        with open(metrics_file, "r", encoding="utf-8") as f:
            for line in f:
                snap = json.loads(line)
                snap["strategy"] = strategy
                snap["run_id"] = run_id
                rows.append(snap)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary", type=str, default="results/agg/summary.csv")
    ap.add_argument("--logs", type=str, default="logs")
    ap.add_argument("--out", type=str, default="results/plots")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    # --- Load summary
    if not os.path.exists(args.summary):
        print("No summary.csv found.")
        return
    df = pd.read_csv(args.summary)

    # --- 1. Bar plot
    pivot = df.groupby(["map","strategy"])[["rescued","deaths"]].mean().reset_index()
    pivot.plot(kind="bar", x="strategy", y=["rescued","deaths"])
    plt.title("Avg Rescued & Deaths by Strategy × Map")
    plt.ylabel("Count")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(os.path.join(args.out, "bar_rescued_deaths.png"))
    plt.close()

    # --- 2. Line plot from per-tick logs
    ts_df = load_time_series(args.logs)
    if not ts_df.empty:
        plt.figure()
        for strat, g in ts_df.groupby("strategy"):
            mean_curve = g.groupby("tick")["rescued"].mean()
            plt.plot(mean_curve.index, mean_curve.values, label=strat)
        plt.title("Cumulative Rescued over Time")
        plt.xlabel("Tick")
        plt.ylabel("Rescued (avg across runs)")
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(args.out, "line_cumulative_rescued.png"))
        plt.close()

    # --- 3. Box plot
    df.boxplot(column="avg_rescue_time", by="strategy")
    plt.suptitle("")
    plt.title("Distribution of Avg Rescue Time by Strategy")
    plt.ylabel("Ticks")
    plt.tight_layout()
    plt.savefig(os.path.join(args.out, "box_avg_rescue_time.png"))
    plt.close()

    print("Plots saved.")

if __name__ == "__main__":
    main()
