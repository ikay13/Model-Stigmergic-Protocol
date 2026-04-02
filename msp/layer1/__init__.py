"""Layer 1: Coordination Core — re-exports the markspace protocol.

The markspace package provides MSP's Layer 1 foundation:
- 5 typed marks: Intent, Action, Observation, Warning, Need
- Deterministic Guard layer (independent of agent compliance)
- Exponential decay, source-based trust, sublinear reinforcement
- Statistical anomaly detection, absorbing barriers, diagnostic probes
- 66 formal properties (P1-P66) verified via Hypothesis

Usage:
    from msp.layer1 import MarkSpace, Agent, Guard, Scope
    # or equivalently:
    from markspace import MarkSpace, Agent, Guard, Scope
"""

from markspace import *  # noqa: F401, F403
from markspace import __all__, __version__ as _markspace_version

__all__ = __all__
__markspace_version__ = _markspace_version
