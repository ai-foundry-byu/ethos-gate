"""charter.py — Safety commandments and autonomy-ladder dataclasses.

These are not enforcement code — they are documentation-as-data, so your
policy layer can introspect, validate against, and surface the relevant
commandment when blocking or questioning an action.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AgentTier(Enum):
    """Canonical agent tiers, in ascending authority order."""
    HUMAN = 0       # T0 — the operator/human
    CEO = 1         # T1 — Orchestrator / CEO-class Opus agent
    ORCHESTRATOR = 2  # T2 — C-Suite / domain orchestrators
    SPECIALIST = 3  # T3 — Specialists
    WORKER = 4      # T4 — Workers (profiled or generic Haiku)


@dataclass(frozen=True)
class Commandment:
    number: int
    title: str
    text: str


# Core commandments distilled from a production agentic system.
# See docs/why.md for the incident history behind each one.
COMMANDMENTS = [
    Commandment(
        1,
        "No broken work to humans",
        "Verify before delivering. A human should never see work that hasn't passed "
        "the agent's own definition-of-done check.",
    ),
    Commandment(
        3,
        "Human-in-the-loop for irreversible external actions",
        "An autonomous agent must not send email, post to social media, spend money, "
        "deploy to production, delete data, or contact external parties without explicit "
        "human approval for that specific action.",
    ),
    Commandment(
        10,
        "Delegate down, verify up",
        "Orchestrators delegate to specialists; specialists verify before reporting done. "
        "A tier never punts a decision upward that it can make itself.",
    ),
    Commandment(
        11,
        "Open source and document everything",
        "After building anything useful, strip personal data, push to a public repo, "
        "and document it so others can learn from it.",
    ),
    Commandment(
        14,
        "Inventory before spawning",
        "Before creating a new agent or tool, check whether an existing one already covers "
        "the need. Building what already exists wastes tokens and creates divergence.",
    ),
]

COMMANDMENTS_BY_NUMBER = {c.number: c for c in COMMANDMENTS}


class ReversibilityTier(Enum):
    """How reversible is a proposed action?"""
    REVERSIBLE = "reversible"           # can undo with no lasting effect
    HARD_TO_REVERSE = "hard_to_reverse" # difficult or costly to undo
    IRREVERSIBLE = "irreversible"       # cannot be undone (sent email, deployed prod)


class AutonomyLevel(Enum):
    """The autonomy ladder — how much human oversight does this action require?"""
    AUTO = "auto"           # T1 — agent may execute without asking
    VERIFY = "verify"       # T2 — agent should verify with orchestrator
    GATE = "gate"           # T3 — agent must pause and get explicit approval
    DENY = "deny"           # T4 — always denied; not the agent's call


@dataclass(frozen=True)
class AutonomyRule:
    """Maps (reversibility, agent_tier) → required autonomy level."""
    reversibility: ReversibilityTier
    max_tier_for_auto: AgentTier
    level: AutonomyLevel
    rationale: str


AUTONOMY_LADDER: list[AutonomyRule] = [
    AutonomyRule(
        ReversibilityTier.REVERSIBLE,
        AgentTier.WORKER,
        AutonomyLevel.AUTO,
        "Reversible actions (file edits, test runs, local builds) may proceed without approval.",
    ),
    AutonomyRule(
        ReversibilityTier.HARD_TO_REVERSE,
        AgentTier.ORCHESTRATOR,
        AutonomyLevel.VERIFY,
        "Hard-to-reverse actions (schema migrations, cross-service calls) need orchestrator confirmation.",
    ),
    AutonomyRule(
        ReversibilityTier.IRREVERSIBLE,
        AgentTier.CEO,
        AutonomyLevel.GATE,
        "Irreversible actions (email sends, prod deploys, money) require human explicit approval.",
    ),
]


def required_autonomy(reversibility: ReversibilityTier, tier: AgentTier) -> AutonomyLevel:
    """Compute the required autonomy level for an action."""
    for rule in AUTONOMY_LADDER:
        if reversibility == rule.reversibility:
            if tier.value <= rule.max_tier_for_auto.value:
                return rule.level
            return AutonomyLevel.GATE
    return AutonomyLevel.DENY
