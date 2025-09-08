# eval/harness.py
import argparse, os, csv, random
import numpy as np
from pathlib import Path
from tqdm import trange
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from eval.logger import save_run_metrics
from main import run_episode  # assuming run_episode returns dict of metrics


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--maps", nargs="+", required=True)
    ap.add_argument("--strategies", nargs="+", required=True)
    ap.add_argument("--seeds", nargs="+", type=int, default=[0,1,2,3,4])
    ap.add_argument("--ticks", type=int, default=200)
    args = ap.parse_args()

    os.makedirs("results/raw", exist_ok=True)
    os.makedirs("results/agg", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    fieldnames = [
        "run_id","map","strategy","seed",
        "rescued","deaths","avg_rescue_time",
        "fires_extinguished","roads_cleared","energy_used",
        "tool_calls","invalid_json","replans","hospital_overflow_events",
        "battery_recharges"
    ]

    summary_csv = "results/agg/summary.csv"
    write_header = not os.path.exists(summary_csv)
    with open(summary_csv, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()

        for mappath in args.maps:
            mapname = Path(mappath).stem
            for strategy in args.strategies:
                for seed in args.seeds:
                    run_id = f"{mapname}_{strategy}_seed{seed}"

                    # 🔒 seed fixing
                    random.seed(seed)
                    np.random.seed(seed)

                    # Run one episode (pass run_id explicitly)
                    metrics = run_episode(
                        mappath,
                        seed=seed,
                        ticks=args.ticks,
                        strategy=strategy,
                        run_id=run_id,          # 🔹 NEW
                        log_path=None,
                        render=False
                    )

                    # Attach identifiers (safety, in case run_episode doesn’t add all)
                    metrics.update({
                        "run_id": run_id,
                        "map": mapname,
                        "strategy": strategy,
                        "seed": seed
                    })

                    # Save JSON per run
                    save_run_metrics(run_id, metrics)

                    # Append CSV row
                    row = {k: metrics.get(k,"") for k in fieldnames}
                    writer.writerow(row)

    print(f"Done. Results in results/raw/ and results/agg/summary.csv")


if __name__ == "__main__":
    main()
