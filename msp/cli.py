"""MSP CLI entrypoint — SEED, PAUL, and AEGIS from the command line.

Usage:
  python -m msp seed --type software --name myproject --goal "Build auth" [--root PATH]
  python -m msp paul plan --project myproject --milestone "m1:Build auth:tests pass" [--root PATH]
  python -m msp aegis --project myproject [--root PATH]
"""
from __future__ import annotations

import argparse
import sys
import uuid
from pathlib import Path
from unittest.mock import MagicMock

from markspace import Agent, MarkSpace, Scope

from msp.layer5.aegis import AuditScope, EpistemicAudit
from msp.layer5.base import WorkspaceState
from msp.layer5.paul import Milestone, PlanApplyUnify
from msp.layer5.seed import Ideation, ProjectGenesis

# Scopes used by SEED, PAUL, AEGIS, and BASE — must be registered before writing marks.
_CLI_SCOPES = ["seed", "paul", "aegis", "base"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_infrastructure(project: str, root: Path):
    """Return (markspace, agent, workspace_state) ready for CLI use.

    VaultSync requires a real Obsidian path which we don't have in the CLI,
    so vault is replaced with a MagicMock that satisfies WorkspaceState's
    interface without attempting filesystem access.
    """
    markspace = MarkSpace()
    for scope_name in _CLI_SCOPES:
        markspace.register_scope(Scope(name=scope_name))

    # Grant the CLI agent write access to all mark types in all CLI scopes.
    _all_types = ["intent", "action", "observation", "warning", "need"]
    agent = Agent(
        id=uuid.uuid4(),
        name="msp-cli",
        scopes={scope_name: _all_types for scope_name in _CLI_SCOPES},
    )
    vault = MagicMock()

    workspace_state = WorkspaceState(
        project=project,
        root=root,
        markspace=markspace,
        vault=vault,
        agent=agent,
    )
    return markspace, agent, workspace_state


def _make_paul(project: str, root: Path, markspace: MarkSpace, agent: Agent,
               workspace_state: WorkspaceState) -> PlanApplyUnify:
    return PlanApplyUnify(
        project=project,
        state=workspace_state,
        markspace=markspace,
        agent=agent,
    )


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

def cmd_seed(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    project = args.name

    markspace, agent, workspace_state = _make_infrastructure(project, root)
    paul = _make_paul(project, root, markspace, agent, workspace_state)

    seed = ProjectGenesis(
        markspace=markspace,
        paul=paul,
        root=root,
        agent=agent,
    )

    ideation = Ideation(
        project_type=args.type,
        name=project,
        goals=args.goal,
        constraints=[],
    )

    plan = seed.launch(ideation)

    planning_path = root / project / "PLANNING.md"
    print(f"SEED complete.")
    print(f"  Project : {project}")
    print(f"  Type    : {args.type}")
    print(f"  Goals   : {len(args.goal)}")
    print(f"  Plan ID : {plan.id}")
    print(f"  PLANNING: {planning_path}")
    return 0


def cmd_paul_plan(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    project = args.project

    markspace, agent, workspace_state = _make_infrastructure(project, root)
    paul = _make_paul(project, root, markspace, agent, workspace_state)

    milestones: list[Milestone] = []
    for raw in args.milestone:
        parts = raw.split(":", 2)
        if len(parts) != 3:
            print(
                f"ERROR: --milestone must be 'id:description:acceptance_criteria', got: {raw!r}",
                file=sys.stderr,
            )
            return 1
        milestones.append(
            Milestone(id=parts[0], description=parts[1], acceptance_criteria=parts[2])
        )

    plan = paul.plan(milestones)

    state_path = root / "paul" / "STATE.md"
    print(f"PAUL plan complete.")
    print(f"  Project    : {project}")
    print(f"  Plan ID    : {plan.id}")
    print(f"  Milestones : {len(milestones)}")
    print(f"  STATE.md   : {state_path}")
    return 0


def cmd_aegis(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    project = args.project

    markspace, agent, workspace_state = _make_infrastructure(project, root)
    paul = _make_paul(project, root, markspace, agent, workspace_state)

    aegis = EpistemicAudit(
        project=project,
        root=root,
        markspace=markspace,
        agent=agent,
        paul=paul,
        base=workspace_state,
    )

    scope = AuditScope(codebase_root=root)
    report = aegis.run(scope)

    findings_dir = root / project / "aegis" / "findings"
    print(f"AEGIS audit complete.")
    print(f"  Project     : {project}")
    print(f"  Findings    : {len(report.findings)}")
    print(f"  Findings dir: {findings_dir}")
    return 0


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="msp",
        description="Model Stigmergic Protocol — CLI for SEED, PAUL, and AEGIS",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # ---- seed ---------------------------------------------------------------
    seed_p = sub.add_parser("seed", help="Run SEED: project ideation → PLANNING.md")
    seed_p.add_argument("--type", required=True,
                        choices=["software", "workflow", "research", "campaign", "utility"],
                        help="Project type")
    seed_p.add_argument("--name", required=True, help="Project name")
    seed_p.add_argument("--goal", action="append", default=[],
                        metavar="GOAL", help="Goal string (repeat for multiple goals)")
    seed_p.add_argument("--root", default=".", metavar="PATH",
                        help="Workspace root directory (default: cwd)")

    # ---- paul ---------------------------------------------------------------
    paul_p = sub.add_parser("paul", help="Run PAUL subcommands")
    paul_sub = paul_p.add_subparsers(dest="paul_command", required=True)

    plan_p = paul_sub.add_parser("plan", help="Create a plan → STATE.md + MILESTONES.md")
    plan_p.add_argument("--project", required=True, help="Project name")
    plan_p.add_argument("--milestone", action="append", default=[],
                        metavar="id:description:acceptance_criteria",
                        help="Milestone (repeat for multiple); colon-separated triple")
    plan_p.add_argument("--root", default=".", metavar="PATH",
                        help="Workspace root directory (default: cwd)")

    # ---- aegis --------------------------------------------------------------
    aegis_p = sub.add_parser("aegis", help="Run AEGIS: epistemic audit")
    aegis_p.add_argument("--project", required=True, help="Project name")
    aegis_p.add_argument("--root", default=".", metavar="PATH",
                         help="Workspace root directory (default: cwd)")

    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "seed":
        rc = cmd_seed(args)
    elif args.command == "paul":
        if args.paul_command == "plan":
            rc = cmd_paul_plan(args)
        else:
            parser.error(f"Unknown paul subcommand: {args.paul_command}")
    elif args.command == "aegis":
        rc = cmd_aegis(args)
    else:
        parser.error(f"Unknown command: {args.command}")

    sys.exit(rc)


if __name__ == "__main__":
    main()
