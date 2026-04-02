"""Layer 3: Multi-Provider Orchestration."""

__all__ = ["AgentURI", "AgentRound", "AgentResponse", "ProviderAdapter", "AgentSession"]

_MODULE_MAP = {
    "AgentURI": "msp.layer3.identity",
    "AgentRound": "msp.layer3.adapter",
    "AgentResponse": "msp.layer3.adapter",
    "ProviderAdapter": "msp.layer3.adapter",
    "AgentSession": "msp.layer3.session",
}


def __getattr__(name):
    if name in _MODULE_MAP:
        import importlib
        mod = importlib.import_module(_MODULE_MAP[name])
        return getattr(mod, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
