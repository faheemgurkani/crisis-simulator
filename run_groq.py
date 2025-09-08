#!/usr/bin/env python3
"""
Convenience script to run the crisis simulation with Groq LLM.
Usage: python3 run_groq.py [strategy] [ticks] [map]
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    # Set environment variable for Groq
    os.environ["LLM_PROVIDER"] = "groq"
    
    # Parse arguments
    strategy = sys.argv[1] if len(sys.argv) > 1 else "react"
    ticks = sys.argv[2] if len(sys.argv) > 2 else "50"
    map_file = sys.argv[3] if len(sys.argv) > 3 else "configs/map_small.yaml"
    
    # Validate strategy
    valid_strategies = ["react", "plan_execute", "reflexion", "cot", "tot"]
    if strategy not in valid_strategies:
        print(f"Invalid strategy: {strategy}")
        print(f"Valid strategies: {', '.join(valid_strategies)}")
        sys.exit(1)
    
    # Validate map file
    if not Path(map_file).exists():
        print(f"Map file not found: {map_file}")
        sys.exit(1)
    
    print(f"Running crisis simulation with Groq LLM...")
    print(f"Strategy: {strategy}")
    print(f"Ticks: {ticks}")
    print(f"Map: {map_file}")
    print("-" * 50)
    
    # Run the simulation
    cmd = [
        "python3", "main.py",
        "--map", map_file,
        "--strategy", strategy,
        "--ticks", ticks,
        "--provider", "groq"
    ]
    
    try:
        result = subprocess.run(cmd, check=True)
        print("\n" + "=" * 50)
        print("Simulation completed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"\nSimulation failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
