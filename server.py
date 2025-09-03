# server.py — Mesa 1.2.1 compatible, enhanced GUI (legend, stats, charts)
import os
import yaml
from typing import Dict, Tuple, Iterable
from mesa.visualization.modules import CanvasGrid, ChartModule, TextElement
from mesa.visualization.ModularVisualization import ModularServer
from env.world import CrisisModel
from env.agents import DroneAgent, MedicAgent, TruckAgent, Survivor

MAP_PATH = "configs/map_small.yaml"  # change if needed
SEED = 42
CANVAS_W = 600
CANVAS_H = 600


# ---------------- Portrayal ----------------

def agent_portrayal(agent):
    if agent is None:
        return
    p = {"Layer": 1, "Filled": "true"}

    # Drone: cyan triangle
    if isinstance(agent, DroneAgent):
        p.update({
            "Shape": "triangle",
            "Color": "#00bcd4",
            "scale": 0.8,
            "heading_x": 0.0, "heading_y": 1.0
        })
        p["Layer"] = 4

    # Medic: green circle (darker if carrying)
    elif isinstance(agent, MedicAgent):
        color = "#2ecc71" if not getattr(agent, "carrying", False) else "#1e8449"
        p.update({"Shape": "circle", "Color": color, "r": 0.5})
        p["Layer"] = 5

    # Truck: blue square / rect
    elif isinstance(agent, TruckAgent):
        p.update({"Shape": "rect", "Color": "#3498db", "w": 0.9, "h": 0.9})
        p["Layer"] = 4

    # Survivor: small yellow dot
    elif isinstance(agent, Survivor):
        p.update({"Shape": "circle", "Color": "#f1c40f", "r": 0.35})
        p["Layer"] = 3

    # Generic fallback
    else:
        p.update({"Shape": "circle", "Color": "#aaaaaa", "r": 0.3})
        p["Layer"] = 1

    return p


# ---------------- Config helpers ----------------

def load_cfg(path: str) -> Dict:
    if not os.path.exists(path):
        # No YAML — run with an empty config
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _iter_points_from_cfg(cfg: Dict) -> Iterable[Tuple[int, int]]:
    """Yield all (x,y) points referenced in the cfg to infer bounds."""
    depot = cfg.get("depot")
    if isinstance(depot, (list, tuple)) and len(depot) == 2:
        yield (int(depot[0]), int(depot[1]))

    for key in ("hospitals", "rubble", "initial_fires", "buildings"):
        for item in cfg.get(key, []) or []:
            if isinstance(item, (list, tuple)) and len(item) == 2:
                yield (int(item[0]), int(item[1]))

    for s in (cfg.get("survivors_list") or []):
        if isinstance(s, dict) and "pos" in s and isinstance(s["pos"], (list, tuple)) and len(s["pos"]) == 2:
            yield (int(s["pos"][0]), int(s["pos"][1]))
        elif isinstance(s, (list, tuple)) and len(s) == 2:
            yield (int(s[0]), int(s[1]))


def infer_grid_size(cfg: Dict, default: Tuple[int, int] = (20, 20)) -> Tuple[int, int]:
    """Determine (width, height) from cfg, supporting multiple schema variants."""
    grid = cfg.get("grid") or {}
    if isinstance(grid, dict) and "w" in grid and "h" in grid:
        return int(grid["w"]), int(grid["h"])

    if "width" in cfg and "height" in cfg:
        return int(cfg["width"]), int(cfg["height"])

    max_x = max_y = -1
    for (x, y) in _iter_points_from_cfg(cfg):
        if x > max_x: max_x = x
        if y > max_y: max_y = y
    if max_x >= 0 and max_y >= 0:
        return max_x + 1, max_y + 1

    return default


# ---------------- UI panels ----------------

class StatsPanel(TextElement):
    """
    Render textual stats summary. Charts use datacollector; this panel provides
    a concise human-readable snapshot for the sidebar.
    """
    def render(self, model) -> str:
        # survivors still on the map (not picked, not dead)
        on_map = sum(
            1 for a in model.schedule.agents
            if a.__class__.__name__ == "Survivor"
            and not getattr(a, "_picked", False)
            and not getattr(a, "_dead", False)
        )

        # survivors currently being carried by medics
        carrying_now = sum(
            1 for a in model.schedule.agents
            if a.__class__.__name__ == "MedicAgent" and getattr(a, "carrying", False)
        )

        # survivors waiting in hospital queues (not yet admitted)
        queued = sum(len(q) for q in getattr(model, "hospital_queues", {}).values())

        # termination / final lock
        terminated = not getattr(model, "running", True)

        # metrics (use getattr safe access to preserve compatibility)
        rescued = getattr(model, "rescued", 0)
        deaths = getattr(model, "deaths", 0)
        fires_extinguished = getattr(model, "fires_extinguished", 0)
        rubble_cleared = getattr(model, "rubble_cleared", 0)
        battery_recharges = getattr(model, "battery_recharges", 0)
        hospital_overflow = getattr(model, "hospital_overflow_events", 0)

        # optional total
        total = getattr(model, "total_survivors", None)
        if total is None:
            total = on_map + carrying_now + queued + rescued + deaths

        status = "TERMINATED" if terminated else "RUNNING"

        html = (
            f"<div style='font-family: sans-serif; line-height:1.5; padding:6px'>"
            f"<strong>Step:</strong> {getattr(model,'time',0)} &nbsp; "
            f"<strong>Status:</strong> {status}<br/>"
            f"<strong>Survivors:</strong> total {total} | on-map {on_map} | carried {carrying_now} | queued {queued} | rescued {rescued} | deaths {deaths} <br/>"
            f"<strong>Events:</strong> fires extinguished {fires_extinguished} | rubble cleared {rubble_cleared} | battery recharges {battery_recharges} | hospital overflows {hospital_overflow} <br/>"
        )
        if terminated:
            html += "<em>Simulation terminated — charts frozen.</em>"
        html += "</div>"
        return html


class LegendPanel(TextElement):
    """
    Simple HTML legend with colored swatches and labels for entities.
    """
    def render(self, model) -> str:
        return (
            '<div style="font-family: sans-serif; line-height:1.5; padding:6px;">'
            '<strong>Legend</strong><br/>'
            '<span style="display:inline-block;width:12px;height:12px;background:#00bcd4;margin:0 6px 0 0;vertical-align:middle;"></span> Drone (cyan triangle)<br/>'
            '<span style="display:inline-block;width:12px;height:12px;background:#2ecc71;border-radius:50%;margin:0 6px 0 0;vertical-align:middle;"></span> Medic (green circle; darker when carrying)<br/>'
            '<span style="display:inline-block;width:12px;height:12px;background:#3498db;margin:0 6px 0 0;vertical-align:middle;"></span> Truck (blue square)<br/>'
            '<span style="display:inline-block;width:12px;height:12px;background:#f1c40f;border-radius:50%;margin:0 6px 0 0;vertical-align:middle;"></span> Survivor (yellow dot)<br/>'
            '<span style="display:inline-block;width:12px;height:12px;background:#e74c3c;margin:0 6px 0 0;vertical-align:middle;"></span> Fire<br/>'
            '<span style="display:inline-block;width:12px;height:12px;background:#7f8c8d;margin:0 6px 0 0;vertical-align:middle;"></span> Rubble<br/>'
            '<span style="display:inline-block;width:12px;height:12px;background:#9b59b6;margin:0 6px 0 0;vertical-align:middle;"></span> Hospital<br/>'
            '<span style="display:inline-block;width:12px;height:12px;background:#34495e;margin:0 6px 0 0;vertical-align:middle;"></span> Depot'
            '</div>'
        )


# ---------------- Launch ----------------

def launch(port: int = 8521):
    cfg = load_cfg(MAP_PATH)
    width, height = infer_grid_size(cfg, default=(20, 20))

    grid = CanvasGrid(agent_portrayal, width, height, CANVAS_W, CANVAS_H)

    # Charts: model metrics stored cumulatively in model, so ChartModule works well.
    charts = ChartModule(
        [
            {"Label": "rescued", "Color": "Black"},
            {"Label": "deaths", "Color": "Red"},
            {"Label": "fires_extinguished", "Color": "Blue"},
        ],
        data_collector_name="datacollector",
    )

    legend = LegendPanel()
    stats = StatsPanel()

    server = ModularServer(
        CrisisModel,
        [legend, stats, grid, charts],  # order = top-to-bottom in UI
        "CrisisSim",
        {"width": width, "height": height, "rng_seed": SEED, "config": cfg, "render": True},
    )
    server.port = port
    print(f"Starting web UI at http://127.0.0.1:{port}  (Ctrl+C to stop)")
    server.launch()


if __name__ == "__main__":
    launch(port=8522)  # different port to avoid conflicts
