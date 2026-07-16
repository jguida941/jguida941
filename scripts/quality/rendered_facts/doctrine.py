"""Independent W4 policy pin.

The policy binds WCAG 2.2 contrast/target-size clauses and owner-ratified responsive,
density, capture, and evidence rules in ``docs/design/pageshell.md#d-w4-rendered-facts``.
Changing DATA cannot weaken those rules without also advancing this separate code pin.
"""
from __future__ import annotations

import hashlib
import json


ADMITTED_POLICY_SHA256 = "edc8e01d7b6f61a2211d6fcfab58acf3f0e177c2ca47ca4092dd52d2f368c2c9"


def policy_doctrine_sha256(policy: dict) -> str:
    if not isinstance(policy, dict):
        raise RuntimeError("rendered fact policy must be an object")
    canonical = json.dumps(
        policy, allow_nan=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def validate_policy_doctrine(policy: dict) -> None:
    """Reject every unratified policy change, including exception/allowlist drift."""
    if policy_doctrine_sha256(policy) != ADMITTED_POLICY_SHA256:
        raise RuntimeError("rendered fact policy differs from its independent doctrine pin")
