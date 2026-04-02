"""CARL: ContextAugmentation — intent detection and JIT rule injection.

Reads active Intent marks from the markspace, scores them against domain
trigger lists, and injects matching rule files into the ContextLoader before
an AgentSession launches.

Marks emitted:
  Observation(scope="carl", topic="rules-injected") recording injected domains.
"""
from __future__ import annotations

import time
from pathlib import Path

from markspace import Agent, Intent, MarkSpace, Observation, Source

from msp.layer2.context_loader import ContextLoader

# Keyword triggers per domain. Any match scores +1 for that domain.
DOMAIN_TRIGGERS: dict[str, list[str]] = {
    "development": ["implement", "build", "feature", "code", "tdd", "test", "write"],
    "debugging":   ["fix", "bug", "error", "debug", "broken", "failing", "issue"],
    "planning":    ["plan", "milestone", "roadmap", "design", "spec", "architect"],
    "research":    ["research", "investigate", "analyse", "analyze", "explore", "survey"],
    "review":      ["review", "audit", "check", "inspect", "validate", "verify"],
    "content":     ["write", "document", "draft", "content", "copy", "narrative"],
    "stigmergy":   ["mark", "marks", "coordinate", "stigmerg", "pheromone", "signal"],
    "orchestration": ["orchestrate", "paul", "plan-apply", "workflow", "pipeline", "schedule"],
    "audit":       ["aegis", "audit", "persona", "domain", "finding", "epistemic"],
}


class ContextAugmentation:
    """Detects intent from marks and injects domain rules into AgentSession context.

    Attributes:
        markspace: Shared MarkSpace instance (for reading Intent marks).
        loader:    ContextLoader to inject rules into.
        rules_dir: Path to the rules directory (default: msp/layer5/rules/).
        agent:     Authorized Agent for writing Observation marks.
        scope:     MarkSpace scope to read Intent marks from.
    """

    def __init__(
        self,
        markspace: MarkSpace,
        loader: ContextLoader,
        rules_dir: Path | None = None,
        agent: Agent | None = None,
        scope: str = "paul",
        max_age: float = 3600.0,
    ) -> None:
        self.markspace = markspace
        self.loader = loader
        self.rules_dir = rules_dir or (Path(__file__).parent / "rules")
        self.agent = agent
        self.scope = scope
        self.max_age = max_age

    def _score_domains(self, marks: list) -> dict[str, int]:
        """Score each domain against mark content. Returns domain → score dict."""
        scores = {domain: 0 for domain in DOMAIN_TRIGGERS}
        for mark in marks:
            text = f"{getattr(mark, 'action', '')} {getattr(mark, 'resource', '')}".lower()
            for domain, keywords in DOMAIN_TRIGGERS.items():
                scores[domain] += sum(1 for kw in keywords if kw in text)
        return scores

    def detect_domains(self, marks: list) -> list[str]:
        """Return domains with score > 0, sorted by score descending."""
        scores = self._score_domains(marks)
        return [d for d, s in sorted(scores.items(), key=lambda x: -x[1]) if s > 0]

    def load_rules(self, domains: list[str]) -> list[Path]:
        """Resolve domain names to existing rule file paths."""
        paths = []
        for domain in domains:
            path = self.rules_dir / f"{domain}.md"
            if path.exists():
                paths.append(path)
        return paths

    def inject(self, session_config: dict) -> dict:
        """Detect domains from live Intent marks and inject rule files.

        Reads active Intent marks from markspace, detects domains,
        loads matching rule files, calls loader.load(extra_paths=...),
        emits an Observation mark, and returns an augmented session config.
        """
        marks = self.markspace.read(scope=self.scope)
        cutoff = time.time() - self.max_age
        intent_marks = [
            m for m in marks
            if isinstance(m, Intent)
            and (m.created_at == 0.0 or m.created_at > cutoff)
        ]
        domains = self.detect_domains(intent_marks)
        rule_paths = self.load_rules(domains)

        if rule_paths:
            self.loader.load(extra_paths=rule_paths)

        self.observe(domains)

        return {**session_config, "carl_domains": domains, "carl_rules": [str(p) for p in rule_paths]}

    def observe(self, domains: list[str]) -> None:
        """Emit an Observation mark recording which domains were injected."""
        if self.agent is not None:
            self.markspace.write(
                self.agent,
                Observation(
                    scope="carl",
                    topic="rules-injected",
                    content={"domains": domains},
                    confidence=1.0,
                    source=Source.FLEET,
                ),
            )
