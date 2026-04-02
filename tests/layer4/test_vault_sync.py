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
