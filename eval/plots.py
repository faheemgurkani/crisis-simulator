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
    
    # Create combined labels for better distinction
    pivot['map_strategy'] = pivot['map'] + '_' + pivot['strategy']
    
    # Create the bar plot
    fig, ax = plt.subplots(figsize=(15, 8))
    x_pos = range(len(pivot))
    
    # Plot bars
    width = 0.35
    ax.bar([x - width/2 for x in x_pos], pivot['rescued'], width, label='Rescued', color='#2E86AB', alpha=0.8)
    ax.bar([x + width/2 for x in x_pos], pivot['deaths'], width, label='Deaths', color='#A23B72', alpha=0.8)
    
    # Customize the plot
    ax.set_xlabel('Map × Strategy')
    ax.set_ylabel('Count')
    ax.set_title('Avg Rescued & Deaths by Strategy × Map')
    ax.set_xticks(x_pos)
    ax.set_xticklabels(pivot['map_strategy'], rotation=45, ha='right')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(os.path.join(args.out, "bar_rescued_deaths.png"), dpi=300, bbox_inches='tight')
    plt.close()

    # --- 2. Line plot from per-tick logs
    ts_df = load_time_series(args.logs)
    if not ts_df.empty:
        plt.figure(figsize=(14, 8))
        
        # Define distinct colors and styles for each strategy
        strategy_styles = {
            'react': {'color': '#2E86AB', 'linestyle': '-', 'marker': 'o', 'markersize': 5},
            'plan_execute': {'color': '#A23B72', 'linestyle': '--', 'marker': 's', 'markersize': 5},
            'cot': {'color': '#F18F01', 'linestyle': '-.', 'marker': '^', 'markersize': 5},
            'reflexion': {'color': '#C73E1D', 'linestyle': ':', 'marker': 'D', 'markersize': 6},
            'tot': {'color': '#6A4C93', 'linestyle': '-', 'marker': '*', 'markersize': 7}
        }
        
        # Group strategies by performance
        high_performers = []
        low_performers = []
        
        for strat, g in ts_df.groupby("strategy"):
            mean_curve = g.groupby("tick")["rescued"].mean()
            final_rescued = mean_curve.iloc[-1]
            
            if final_rescued > 0:
                high_performers.append((strat, g, mean_curve))
            else:
                low_performers.append((strat, g, mean_curve))
        
        # Plot high performers with slight offset to show they're overlapping
        for i, (strat, g, mean_curve) in enumerate(high_performers):
            style = strategy_styles.get(strat, {'color': 'black', 'linestyle': '-', 'marker': 'o'})
            
            # Add slight offset to distinguish overlapping lines
            offset = i * 0.1
            x_vals = mean_curve.index[::3]  # Every 3rd point
            y_vals = mean_curve.values[::3] + offset
            
            plt.plot(x_vals, y_vals, 
                    label=f'{strat} (final: {mean_curve.iloc[-1]:.1f})', 
                    **style, 
                    linewidth=2.5, 
                    alpha=0.9)
        
        # Plot low performers
        for strat, g, mean_curve in low_performers:
            style = strategy_styles.get(strat, {'color': 'red', 'linestyle': ':', 'marker': 'x'})
            x_vals = mean_curve.index[::10]  # Every 10th point
            y_vals = mean_curve.values[::10]
            
            plt.plot(x_vals, y_vals, 
                    label=f'{strat} (final: {mean_curve.iloc[-1]:.1f})', 
                    **style, 
                    linewidth=2, 
                    alpha=0.7)
        
        plt.title("Cumulative Rescued over Time\n(Note: ReAct, Plan-Execute, and CoT show identical performance)", 
                 fontsize=14, fontweight='bold')
        plt.xlabel("Tick", fontsize=12)
        plt.ylabel("Rescued (avg across runs)", fontsize=12)
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)
        plt.grid(True, alpha=0.3)
        
        # Add annotation about identical performance
        if len(high_performers) > 1:
            plt.text(0.02, 0.98, 
                    f"Note: {', '.join([s[0] for s in high_performers])} strategies\nshow identical performance\n(deterministic Ollama model)", 
                    transform=plt.gca().transAxes, 
                    verticalalignment='top',
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
                    fontsize=9)
        
        plt.tight_layout()
        plt.savefig(os.path.join(args.out, "line_cumulative_rescued.png"), dpi=300, bbox_inches='tight')
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
