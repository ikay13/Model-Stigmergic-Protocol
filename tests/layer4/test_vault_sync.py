# tests/layer4/test_vault_sync.py
from msp.layer4.vault_sync import _parse_frontmatter, _has_tag


def test_parse_frontmatter_with_tags():
    """Parses YAML frontmatter and returns body separately."""
    text = "---\ntags: [session, msp]\ndate: 2026-04-02\n---\n\n# Hello\n\nBody text."
    fm, body = _parse_frontmatter(text)
    assert fm["tags"] == ["session", "msp"]
    assert fm["date"].isoformat() == "2026-04-02"
    assert body == "# Hello\n\nBody text."


def test_parse_frontmatter_no_frontmatter():
    """Returns empty dict and full text when no frontmatter present."""
    text = "# Just a heading\n\nNo frontmatter here."
    fm, body = _parse_frontmatter(text)
    assert fm == {}
    assert body == text


def test_parse_frontmatter_empty_frontmatter():
    """Returns empty dict when frontmatter block is empty."""
    text = "---\n---\n\n# Body"
    fm, body = _parse_frontmatter(text)
    assert fm == {}
    assert "# Body" in body


def test_has_tag_true():
    """_has_tag returns True when tag is in frontmatter tags list."""
    fm = {"tags": ["session", "msp", "multi-agent"]}
    assert _has_tag(fm, "msp") is True


def test_has_tag_false():
    """_has_tag returns False when tag is absent."""
    fm = {"tags": ["session", "notes"]}
    assert _has_tag(fm, "msp") is False


def test_has_tag_no_tags_key():
    """_has_tag returns False when frontmatter has no tags key."""
    fm = {"date": "2026-04-02"}
    assert _has_tag(fm, "msp") is False


# --- VaultSync.import_tagged tests ---

from pathlib import Path
from markspace import Agent, MarkSpace, Scope, DecayConfig, Source
from msp.layer4.vault_sync import VaultSync


def _make_vault(tmp_path: Path) -> Path:
    """Create a minimal fake vault for testing."""
    vault = tmp_path / "vault"
    msp_dir = vault / "MSP"
    msp_dir.mkdir(parents=True)

    # Tagged page — should be imported
    (msp_dir / "tagged.md").write_text(
        "---\ntags: [msp, project]\ntitle: Tagged Page\n---\n\n# Tagged\n\nSome content."
    )
    # Untagged page — should be skipped
    (msp_dir / "untagged.md").write_text(
        "---\ntags: [notes]\n---\n\n# Untagged\n\nIgnored."
    )
    # No frontmatter — should be skipped
    (msp_dir / "bare.md").write_text("# No frontmatter\n\nJust text.")
    return vault


def _make_vault_scope_and_agent():
    """Create a minimal MarkSpace with vault scope."""
    scope = Scope(
        name="vault",
        observation_topics=["*"],
        decay=DecayConfig(
            observation_half_life=3600.0,
            warning_half_life=3600.0,
            intent_ttl=1800.0,
        ),
    )
    space = MarkSpace(scopes=[scope])
    agent = Agent(name="vault-importer", scopes={"vault": ["observation"]})
    return space, agent


def test_import_tagged_imports_only_tagged_pages(tmp_path):
    """import_tagged writes only #msp-tagged pages as Observation marks."""
    vault = _make_vault(tmp_path)
    space, agent = _make_vault_scope_and_agent()

    syncer = VaultSync(vault_root=vault, mark_space=space, agent=agent)
    count = syncer.import_tagged(directory="MSP", tag="msp")

    assert count == 1
    marks = space.read(scope="vault", mark_type=None)
    assert len(marks) == 1
    assert marks[0].topic == "vault-page"
    assert marks[0].source == Source.EXTERNAL_VERIFIED
    assert marks[0].confidence == 1.0


def test_import_tagged_content_has_path_and_text(tmp_path):
    """Imported mark content includes the vault-relative path and page body."""
    vault = _make_vault(tmp_path)
    space, agent = _make_vault_scope_and_agent()

    syncer = VaultSync(vault_root=vault, mark_space=space, agent=agent)
    syncer.import_tagged(directory="MSP", tag="msp")

    marks = space.read(scope="vault", mark_type=None)
    content = marks[0].content
    assert "MSP/tagged.md" in content["path"]
    assert "Some content." in content["text"]


def test_import_tagged_returns_count(tmp_path):
    """import_tagged returns the number of pages imported."""
    vault = _make_vault(tmp_path)
    space, agent = _make_vault_scope_and_agent()

    syncer = VaultSync(vault_root=vault, mark_space=space, agent=agent)
    count = syncer.import_tagged(directory="MSP", tag="msp")
    assert count == 1


def test_import_tagged_empty_directory(tmp_path):
    """import_tagged returns 0 when no tagged pages exist."""
    vault = tmp_path / "vault"
    (vault / "MSP").mkdir(parents=True)
    space, agent = _make_vault_scope_and_agent()

    syncer = VaultSync(vault_root=vault, mark_space=space, agent=agent)
    count = syncer.import_tagged(directory="MSP", tag="msp")
    assert count == 0


# --- VaultSync.export_observations tests ---

import yaml as _yaml
from markspace import Observation, Source


def _make_export_space_and_agent():
    """MarkSpace with an 'msp' scope for agent observations."""
    scope = Scope(
        name="msp",
        observation_topics=["*"],
        decay=DecayConfig(
            observation_half_life=3600.0,
            warning_half_life=3600.0,
            intent_ttl=1800.0,
        ),
    )
    space = MarkSpace(scopes=[scope])
    agent = Agent(name="test-agent", scopes={"msp": ["observation"]})
    return space, agent


def _write_observation(space, agent, topic, content, confidence=0.9):
    space.write(
        agent,
        Observation(
            scope="msp",
            topic=topic,
            content=content,
            confidence=confidence,
            source=Source.FLEET,
        ),
    )


def test_export_observations_writes_files(tmp_path):
    """export_observations writes one markdown file per observation."""
    vault = tmp_path / "vault"
    (vault / "MSP" / "agent-output").mkdir(parents=True)
    space, agent = _make_export_space_and_agent()
    _write_observation(space, agent, "progress", {"status": "on track"})

    syncer = VaultSync(vault_root=vault, mark_space=space, agent=agent, scope="vault")
    count = syncer.export_observations(read_scope="msp")

    assert count == 1
    output_files = list((vault / "MSP" / "agent-output").glob("*.md"))
    assert len(output_files) == 1


def test_export_observations_frontmatter_tags(tmp_path):
    """Exported files are tagged with #msp-agent-output."""
    vault = tmp_path / "vault"
    (vault / "MSP" / "agent-output").mkdir(parents=True)
    space, agent = _make_export_space_and_agent()
    _write_observation(space, agent, "progress", {"status": "ok"})

    syncer = VaultSync(vault_root=vault, mark_space=space, agent=agent, scope="vault")
    syncer.export_observations(read_scope="msp")

    output_file = list((vault / "MSP" / "agent-output").glob("*.md"))[0]
    text = output_file.read_text()
    fm, _ = _parse_frontmatter(text)
    assert "msp-agent-output" in fm["tags"]


def test_export_observations_content_in_body(tmp_path):
    """Exported file body contains the observation topic and content."""
    vault = tmp_path / "vault"
    (vault / "MSP" / "agent-output").mkdir(parents=True)
    space, agent = _make_export_space_and_agent()
    _write_observation(space, agent, "progress", {"status": "on track", "detail": "all good"})

    syncer = VaultSync(vault_root=vault, mark_space=space, agent=agent, scope="vault")
    syncer.export_observations(read_scope="msp")

    output_file = list((vault / "MSP" / "agent-output").glob("*.md"))[0]
    body = output_file.read_text()
    assert "progress" in body
    assert "on track" in body


def test_export_observations_overwrites_existing(tmp_path):
    """export_observations overwrites existing files for the same mark id."""
    vault = tmp_path / "vault"
    (vault / "MSP" / "agent-output").mkdir(parents=True)
    space, agent = _make_export_space_and_agent()
    _write_observation(space, agent, "progress", {"status": "first"})

    syncer = VaultSync(vault_root=vault, mark_space=space, agent=agent, scope="vault")

    # Export twice — should still be 1 file
    syncer.export_observations(read_scope="msp")
    syncer.export_observations(read_scope="msp")

    output_files = list((vault / "MSP" / "agent-output").glob("*.md"))
    assert len(output_files) == 1


def test_export_observations_no_marks(tmp_path):
    """export_observations returns 0 when no marks exist."""
    vault = tmp_path / "vault"
    (vault / "MSP" / "agent-output").mkdir(parents=True)
    space, agent = _make_export_space_and_agent()

    syncer = VaultSync(vault_root=vault, mark_space=space, agent=agent, scope="vault")
    count = syncer.export_observations(read_scope="msp")
    assert count == 0
