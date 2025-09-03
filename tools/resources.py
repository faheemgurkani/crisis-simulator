def inventory_state(model, agent_id: str):
    for a in model.schedule.agents:
        if str(a.unique_id) == str(agent_id):
            return {
                "agent_id": str(agent_id),
                "battery": getattr(a, "battery", None),
                "energy": getattr(a, "energy", None),
                "water": getattr(a, "water", None),
                "tools": getattr(a, "tools", None),
                "carrying": getattr(a, "carrying", False)
            }
    return {"status": "error", "reason": "agent_not_found"}


def consume_energy(agent, cost):
    """Deduct energy from agent. If depleted, mark as dead_battery."""
    agent.energy = max(0, getattr(agent, "energy", 0) - cost)
    if agent.energy == 0:
        agent.status = "dead_battery"
