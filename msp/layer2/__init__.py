"""Layer 2: Context Engineering Infrastructure."""

__all__ = ["Workspace", "ContextLoader", "StageContract", "TieredContent"]

def __getattr__(name):
    if name in __all__:
        import importlib
        mod = importlib.import_module(f"msp.layer2.{name.lower()}")
        return getattr(mod, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
