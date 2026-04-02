"""Layer 4: Knowledge Integration — Obsidian vault sync."""

__all__ = ["VaultSync"]


def __getattr__(name: str):
    if name in __all__:
        import importlib
        mod = importlib.import_module("msp.layer4.vault_sync")
        return getattr(mod, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
