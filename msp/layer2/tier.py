"""L0/L1/L2 tiered content loading for filesystem resources.

Inspired by OpenViking's .abstract/.overview hidden file pattern.
L0: ~100 tokens — quick relevance check
L1: ~2k tokens  — structure and key points
L2: full content — deep read when necessary
"""
from pathlib import Path


class TieredContent:
    """Provides L0/L1/L2 access to a file's content."""

    TOKENS_PER_CHAR = 0.25  # approximation: 1 token ≈ 4 chars

    def __init__(self, path: Path) -> None:
        self.path = path

    def l0(self) -> str:
        """Abstract: one-sentence summary (~100 tokens)."""
        abstract = self.path.parent / ".abstract"
        if abstract.exists():
            return abstract.read_text().strip()
        # fall back: first non-empty line of the file
        for line in self.path.read_text().splitlines():
            if line.strip():
                return line.strip()
        return ""

    def l1(self) -> str:
        """Overview: core information (~2k tokens)."""
        overview = self.path.parent / ".overview"
        if overview.exists():
            return overview.read_text().strip()
        # fall back: full content if under 2k tokens
        content = self.path.read_text()
        if self.token_estimate(content) <= 2000:
            return content
        # truncate to ~2k tokens
        limit = int(2000 / self.TOKENS_PER_CHAR)
        return content[:limit]

    def l2(self) -> str:
        """Full content — load only when necessary."""
        return self.path.read_text()

    def token_estimate(self, text: str) -> int:
        """Approximate token count (1 token ≈ 4 chars)."""
        return int(len(text) * self.TOKENS_PER_CHAR)
