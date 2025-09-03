# eval/logger.py
import os, json

def log_prompt_response(strategy, run_id, tick, messages, response_text, logdir="logs"):
    """Append structured conversation entries into logs/strategy=<name>/run=<id>/tick_x.jsonl"""
    run_dir = os.path.join(logdir, f"strategy={strategy}", f"run={run_id}")
    os.makedirs(run_dir, exist_ok=True)
    out_path = os.path.join(run_dir, f"tick_{tick}.jsonl")

    with open(out_path, "a", encoding="utf-8") as f:
        for msg in messages:
            f.write(json.dumps(msg, ensure_ascii=False) + "\n")
        f.write(json.dumps({"role": "assistant", "content": response_text}, ensure_ascii=False) + "\n")


def log_metrics_snapshot(strategy, run_id, tick, metrics, logdir="logs"):
    """
    Store a compact JSON line per tick with the current metrics snapshot.
    Example entry:
    {"tick":12,"rescued":3,"deaths":1,"fires_extinguished":4,...}
    """
    run_dir = os.path.join(logdir, f"strategy={strategy}", f"run={run_id}")
    os.makedirs(run_dir, exist_ok=True)
    out_path = os.path.join(run_dir, "metrics.jsonl")

    snapshot = {"tick": tick}
    snapshot.update(metrics)

    with open(out_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(snapshot, ensure_ascii=False) + "\n")


def save_run_metrics(run_id, metrics, outdir="results/raw"):
    """Dump one JSON file per run with all final metrics"""
    os.makedirs(outdir, exist_ok=True)
    out_path = os.path.join(outdir, f"{run_id}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
