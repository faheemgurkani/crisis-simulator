# Crisis Simulator (Agentic AI Framework)

Mesa-based ABM + minimal agentic planner (ReAct / Plan-and-Execute / Reflexion skeleton).
Runs in **mock** mode (no API keys) or with **Groq/Gemini** if you supply keys.
Includes GUI, rigorous logging, per-tick metrics, an evaluation harness, and plotting.

---

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Single run (mock, no API keys)

```bash
python main.py --map configs/map_small.yaml --provider mock --strategy react_reflexion --seed 42 --ticks 150
```

### GUI

```bash
python server.py     # then open http://127.0.0.1:8521
```

### Batch evaluation (multi-map × strategy × seed)

```bash
python eval/harness.py \
  --maps configs/map_small.yaml configs/map_medium.yaml configs/map_hard.yaml \
  --strategies react plan_execute reflexion \
  --seeds 0 1 2 3 4 \
  --ticks 200
```

### Plots

```bash
# Generates bar/line/box plots using summary.csv and per-tick JSONL
python eval/plots.py --input results/agg/summary.csv --out results/plots
```

---

## Real LLMs (optional)

```bash
# Groq
export LLM_PROVIDER=groq
export GROQ_API_KEY=YOUR_KEY

# Gemini
export LLM_PROVIDER=gemini
export GEMINI_API_KEY=YOUR_KEY
```

You can still run completely in **mock** mode for deterministic testing.

---

## What’s included (high level)

* **World model (`env/world.py`)**

  * Grid world (roads, buildings, rubble, fires, hospitals, depot).
  * Agents: **Drone**, **Medic**, **Truck**, **Survivor**.
  * Per-tick dynamics: fire spread, aftershocks, hospital queues.
  * **Metrics** tracked on the model and in a `DataCollector`.

* **Agents (`env/agents.py`)**

  * Unified energy system; hooks for **metrics** on actions:

    * `recharge` → `battery_recharges`
    * `clear_rubble` → `rubble_cleared`
    * `extinguish` → `fires_extinguished`
    * `drop_at_hospital` → `survivors_rescued` (accounting aid)

* **GUI (`server.py`)**

  * Canvas with colored shapes + legend.
  * Live **Stats panel** and live **Charts** (Mesa ChartModule).

* **Reasoning (`reasoning/*`)**

  * Planner wrapper with **ReAct / Plan-and-Execute / Reflexion** modes.
  * Prompt scaffolding: **explicit system prompt**, legal **ACTION\_SCHEMA**,
    **FINAL\_JSON** convention, and short few-shot examples.
  * Token/verbosity control: limit thinking steps (≤3) and K-nearest context.

* **Evaluation (`eval/*`)**

  * Harness with fixed seeds, multi-map/strategy CLI.
  * **Structured logging** (per-tick JSONL conversations + metrics).
  * **Run summaries** (per-run JSON + aggregate CSV).
  * Plotting scripts (bar/line/box) for results.

---

## GUI details (server.py)

### Portrayal & Legend

* **Drone**: cyan triangle
* **Medic**: green circle (darker when carrying)
* **Truck**: blue square
* **Survivor**: yellow small circle
* **Hospital**: “H” cell background (rendered via grid cell type)
* **Fire**: cell background marked as fire
* **Rubble**: cell background marked as rubble
* **Depot**: depot marker

(Shapes/colors rendered in the Canvas; Legend panel documents the mapping.)

### Stats panel (per tick)

* Survivors **on map**, **carried**, **in queues**, **rescued**, **deaths**
* Operational: **fires extinguished**, **rubble cleared**, **battery recharges**,
  **hospital overflow events**

### Charts (live)

* **Cumulative rescued** (line)
* **Rescued & deaths by tick** (combo)
* **Fires extinguished over time** (line)

Charts keep their final state when the model stops.

---

## Metrics (what we track)

These live on the model and are also emitted to logs/JSON/CSV:

* `rescued`, `deaths`, `avg_rescue_time`
* `fires_extinguished`, `rubble_cleared` (roads cleared), `aftershocks` (if modeled)
* `energy_used`, `battery_recharges`
* `tool_calls`, `invalid_json`, `replans`, `hospital_overflow_events`
* (Aux) `survivors_rescued` (incremented on medic drop; complements `rescued`)

> `avg_rescue_time` is tracked as a rolling average (ticks to hospital admission).

---

## Logging & results artifacts

We capture both **LLM traces** and **per-tick metrics** so you can fully
reconstruct time series and decisions.

### Conversation logs (per tick JSONL)

Emitted by `eval/logger.log_prompt_response(strategy, run_id, tick, messages, response_text)` to:

```
logs/strategy=<STRATEGY>/run=<RUN_ID>/tick_<T>.jsonl
```

Example lines (one JSON object per line):

```json
{"role":"system","content":"...system prompt..."}
{"role":"user","content":"...context JSON + tool specs..."}
{"role":"assistant","content":"Thought: ..."}
{"role":"assistant","content":"FINAL_JSON: {\"commands\":[...]}"}
```

### Per-tick metrics (JSONL time series)

From `eval.logger.log_metrics_snapshot(...)`, called each tick in `main.run_episode`:

```
logs/strategy=<STRATEGY>/run=<RUN_ID>/metrics.jsonl
```

Each line is a full snapshot for that tick:

```json
{"tick":12,"rescued":5,"deaths":1,"fires_extinguished":9,"rubble_cleared":2,"battery_recharges":3,"energy_used":41,...}
```

### Per-run JSON (final metrics)

```
results/raw/<RUN_ID>.json
```

Example:

```json
{
  "run_id":"map_small_react_seed0",
  "map":"map_small.yaml",
  "strategy":"react",
  "seed":0,
  "ticks":200,
  "rescued":20,
  "deaths":5,
  "avg_rescue_time":12.4,
  "fires_extinguished":30,
  "roads_cleared":4,
  "energy_used":75,
  "tool_calls":56,
  "invalid_json":1,
  "replans":2,
  "hospital_overflow_events":1,
  "battery_recharges":7
}
```

### Aggregate CSV

Appended by the harness:

```
results/agg/summary.csv
```

One row per run with:

```
run_id, map, strategy, seed,
rescued, deaths, avg_rescue_time,
fires_extinguished, roads_cleared, energy_used,
tool_calls, invalid_json, replans, hospital_overflow_events,
battery_recharges
```

---

## Deterministic experiments

The harness and the main loop set all relevant seeds per run:

* `random.seed(seed)`, `numpy.random.seed(seed)`, and CrisisModel RNG (`rng_seed=seed`).

---

## Programmatic entry point

`main.run_episode(...)` is the primary API used by the harness:

```python
from main import run_episode

metrics = run_episode(
    map_path="configs/map_small.yaml",
    seed=0,
    ticks=200,
    strategy="react",         # or "plan_execute", "reflexion"
    run_id="map_small_react_seed0",  # passed through for consistent logging
    render=False
)
print(metrics)
```

**Integration note (already wired):** inside `run_episode`, each tick:

```python
# after model.step()
from eval.logger import log_metrics_snapshot
log_metrics_snapshot(strategy, run_id, tick, current_metrics_dict)
```

---

## Planner & prompts (schema discipline)

* Every LLM call uses an explicit **system prompt** that:

  * Describes the environment briefly.
  * Defines the exact **`ACTION_SCHEMA`** (JSON schema).
  * Instructs: **“YOUR FINAL OUTPUT: a single line starting with `FINAL_JSON:` followed by a JSON object matching `ACTION_SCHEMA`.”**
  * Provides a tiny set of few-shot examples (compact context → actions).

* **Cost control:** ReAct / Plan-and-Execute think up to **3 steps**.

* **Context control:** sensors select the **nearest K** entities to keep context small.

* **Robustness:** increments `tool_calls`, `invalid_json`, and `replans` appropriately.

---

## Folder structure

```
crisis-sim/
  env/             # world, agents, dynamics
  tools/           # utilities (routing, energy, etc.)
  reasoning/       # llm client(s), react, reflexion, planner, prompts
  configs/         # YAML maps
  eval/            # logger, harness, plots
  logs/            # structured per-run logs (JSONL)
  results/         # raw per-run JSON, aggregate CSV, plots
  server.py        # Mesa web UI (legend, stats, charts)
  main.py          # run_episode + CLI
```

---

## Tips

* To compare strategies on the same random world realization, fix the **seed**.
* Use the **GUI** for sanity checks while developing actions/policies.
* Time-series plots (cumulative rescued by tick) are driven by `metrics.jsonl`; ensure you run via the harness or `main.py` so per-tick logging is produced.

---

**Have fun, and break fewer simulated legs! 🧑‍🚒🚑🚁**
