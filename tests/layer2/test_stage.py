from pathlib import Path
import pytest
from msp.layer2.stage import StageContract, StageInput, StageOutput

VALID_CONTEXT = """\
## Inputs

| Source | File/Location | Section/Scope | Why |
|--------|--------------|---------------|-----|
| Previous stage | ../01-research/output/notes.md | Full file | Source material |
| Style guide | ../../_config/voice.md | Voice Rules section | Tone guidance |

## Process

1. Read inputs
2. Produce output

## Outputs

| Artifact | Location | Format |
|----------|----------|--------|
| Script | output/script.md | Markdown |
"""


def test_parse_inputs(tmp_path):
    """Parses Inputs table into StageInput list."""
    ctx = tmp_path / "CONTEXT.md"
    ctx.write_text(VALID_CONTEXT)
    contract = StageContract.from_file(ctx)
    assert len(contract.inputs) == 2
    assert contract.inputs[0].source == "Previous stage"
    assert contract.inputs[0].location == "../01-research/output/notes.md"


def test_parse_outputs(tmp_path):
    """Parses Outputs table into StageOutput list."""
    ctx = tmp_path / "CONTEXT.md"
    ctx.write_text(VALID_CONTEXT)
    contract = StageContract.from_file(ctx)
    assert len(contract.outputs) == 1
    assert contract.outputs[0].artifact == "Script"
    assert contract.outputs[0].location == "output/script.md"


def test_parse_process(tmp_path):
    """Parses Process section into list of steps."""
    ctx = tmp_path / "CONTEXT.md"
    ctx.write_text(VALID_CONTEXT)
    contract = StageContract.from_file(ctx)
    assert len(contract.process_steps) == 2
    assert contract.process_steps[0] == "Read inputs"


def test_missing_section_raises(tmp_path):
    """Raises ValueError if required section is missing."""
    ctx = tmp_path / "CONTEXT.md"
    ctx.write_text("## Process\n1. Only process, no inputs or outputs")
    with pytest.raises(ValueError, match="Inputs"):
        StageContract.from_file(ctx)


def test_context_under_500_tokens(tmp_path):
    """A well-formed CONTEXT.md stays within the 500 token budget."""
    ctx = tmp_path / "CONTEXT.md"
    ctx.write_text(VALID_CONTEXT)
    contract = StageContract.from_file(ctx)
    assert contract.token_estimate() <= 500
