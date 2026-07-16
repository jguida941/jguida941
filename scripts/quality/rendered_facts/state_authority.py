"""Project the governed Studio capture states from the admissibility decision source."""
from __future__ import annotations

from functools import lru_cache
import json


@lru_cache(maxsize=1)
def _canonical_studio_state_plan() -> str:
    from scripts.quality.settings_admissibility import active_profiles, admissible_space

    profiles = active_profiles()
    space = admissible_space()
    states = []
    for base in profiles:
        states.append({
            "state_id": f"base:{base}", "base": base, "component": "button",
            "source": base, "variant": f"{base}-base",
        })
        for row in space:
            if (row["base"] != base or row["source"] == base
                    or row["admissible"] is not True):
                continue
            states.append({
                "state_id": f"base:{base}|swap:{row['component']}:{row['source']}",
                "base": base, "component": row["component"], "source": row["source"],
                "variant": f"{base}-{row['component']}-{row['source']}",
            })
    return json.dumps(states, allow_nan=False, sort_keys=True, separators=(",", ":"))


def studio_state_plan() -> list[dict]:
    """Return a fresh copy so callers cannot mutate the cached authority projection."""
    return json.loads(_canonical_studio_state_plan())
