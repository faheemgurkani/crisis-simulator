# reasoning/planner.py
import logging
from .utils import get_validated_actions, get_validated_actions_with_logging

# Import your strategy implementations
from .react import react_plan
from .reflexion import reflexion_plan
from .plan_execute import plan_execute_plan
from .cot import cot_plan
from .tot import tot_plan

logger = logging.getLogger(__name__)


def make_plan(context, strategy="react", scratchpad=""):
    """
    Top-level planner dispatcher.

    Args:
        context: JSON context from sensors.py (world state).
        strategy: Which LLM planning strategy to use.
        scratchpad: Optional running memory/log for strategies like Reflexion.

    Returns:
        dict with "commands" key (validated against ACTION_SCHEMA).
    """
    # --- Choose the planner function ---
    if strategy == "react":
        messages = react_plan(context, scratchpad=scratchpad)
    elif strategy == "reflexion":
        messages = reflexion_plan(context, scratchpad=scratchpad)
    elif strategy == "plan_execute":
        messages = plan_execute_plan(context, scratchpad=scratchpad)
    elif strategy == "cot":
        messages = cot_plan(context, scratchpad=scratchpad)
    elif strategy == "tot":
        messages = tot_plan(context, scratchpad=scratchpad)
    else:
        logger.warning(f"Unknown strategy={strategy}, defaulting to react.")
        messages = react_plan(context, scratchpad=scratchpad)

    # --- Always run through validated JSON wrapper ---
    actions = get_validated_actions(messages, logger=logger)
    return actions


def make_plan_with_logging(context, strategy="react", scratchpad=""):
    """
    Top-level planner dispatcher with logging support.

    Args:
        context: JSON context from sensors.py (world state).
        strategy: Which LLM planning strategy to use.
        scratchpad: Optional running memory/log for strategies like Reflexion.

    Returns:
        tuple: (actions_dict, messages, response_text) for logging
    """
    # --- Choose the planner function ---
    if strategy == "react":
        messages = react_plan(context, scratchpad=scratchpad)
    elif strategy == "reflexion":
        messages = reflexion_plan(context, scratchpad=scratchpad)
    elif strategy == "plan_execute":
        messages = plan_execute_plan(context, scratchpad=scratchpad)
    elif strategy == "cot":
        messages = cot_plan(context, scratchpad=scratchpad)
    elif strategy == "tot":
        messages = tot_plan(context, scratchpad=scratchpad)
    else:
        logger.warning(f"Unknown strategy={strategy}, defaulting to react.")
        messages = react_plan(context, scratchpad=scratchpad)

    # --- Get validated actions and response text ---
    actions, response_text = get_validated_actions_with_logging(messages, logger=logger)
    return actions, messages, response_text
