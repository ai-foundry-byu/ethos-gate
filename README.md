# ethos-gate

Application-layer safety hooks for governing agentic Claude systems.

Built from production patterns running 10+ concurrent autonomous Claude sessions. ethos-gate is the application-level guardrail layer — the PreToolUse and Stop hooks that enforce safety properties your system prompt cannot.

---

## What's in here

| Module | What it does |
|--------|-------------|
| `hooks/irreversible_guard.py` | Blocks irreversible Bash commands (git push, rm -rf, prod deploys) unless the session has already run tests. Blocks Stop if files were edited but no tests were observed. |
| `hooks/credential_scrape.py` | Three-tier policy blocking access to browser cred stores (always), autonomous-session privilege escalation (strict mode), and secret files in untrusted-input contexts (sandbox mode). |
| `hooks/external_action_gate.py` | Governs outbound GitHub actions. Owned repos: full send. External repos: classified + judged. Override token for explicit approvals. Fail-safe: deny when judge is unavailable. |
| `audit/trifecta.py` | Lethal-trifecta combination-exposure scanner. Flags agents that simultaneously hold private data access + untrusted input exposure + outbound channel. Exit 2 = BLIND = failure. |
| `charter.py` | Safety commandments and autonomy-ladder dataclasses — documentation-as-data for your policy layer. |

---

## Quick start

```bash
pip install ethos-gate
# or from source:
git clone https://github.com/ai-foundry-byu/ethos-gate
cd ethos-gate && pip install -e .
```

Wire the hooks in your Claude Code settings (`~/.claude/settings.json`):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": ".*",
        "hooks": [{
          "type": "command",
          "command": "python3 -m ethos_gate.hooks.irreversible_guard",
          "timeout": 5000
        }]
      }
    ],
    "Stop": [
      {
        "hooks": [{
          "type": "command",
          "command": "python3 -m ethos_gate.hooks.irreversible_guard",
          "timeout": 5000
        }]
      }
    ]
  },
  "env": {
    "HARNESS_VERIFY": "1"
  }
}
```

See `examples/claude_settings_example.json` for the full multi-gate config.

---

## The fail-open principle

Every gate in ethos-gate exits `0` (allow) on any internal error. This is intentional:

> "A gate that breaks and blocks everything gets ripped out. A safety gate must degrade gracefully."

Legitimate blocking exits `2` (deny) via the Claude Code hook protocol, never via exception.

---

## The three-tier credential policy

```
UNIVERSAL  — always blocked: browser cred stores, password managers, keychain dump tools
STRICT     — blocked in autonomous sessions (CLAWD_AUTONOMOUS=1): crontab mutations, LaunchAgent writes
SANDBOX    — blocked in untrusted-input contexts: .env, private keys, AWS creds, API key files
```

The SANDBOX tier is separate from STRICT because many legitimate autonomous loops read `.env`
on purpose. Only a context where external inputs could influence tool calls (a "bug-squash fixer"
or similar) needs the sandbox tier.

---

## The lethal trifecta

An agent holding all three of these simultaneously is a latent data-exfiltration path:

1. **Private data access** — can read secrets, PII, credentials
2. **Untrusted input exposure** — ingests web pages, email, user files (prompt-injection surface)
3. **Outbound channel** — can write to email, social media, external repos

Run the audit:
```bash
ethos-trifecta [paths...]          # human-readable report
ethos-trifecta --check --json .    # exit 1 if trifecta agents found
```

---

## The external action gate

Distilled from a 2026-07-04 incident: an autonomous session submitted 248 pull requests and 415 GitHub Discussions to unrelated open-source repos to farm stars. No individual rule was broken; the missing piece was a judgment gate for outbound actions.

```python
from ethos_gate.hooks.external_action_gate import evaluate

verdict = evaluate("gh pr create --repo stranger/repo --title 'Fix bug'")
# verdict.decision == "deny" (external repo, no override token)

verdict = evaluate("OUTWARD_ACTION_APPROVED=1 gh pr create --repo stranger/repo ...")
# verdict.decision == "allow" (explicit override)
```

Configure owned repos via `ETHOS_OWNED_ORGS` (comma-separated GitHub org/user slugs).

---

## Running tests

```bash
pip install -e ".[dev]"
pytest tests/
```

---

## Philosophy

ethos-gate is built on three convictions:

1. **Application-layer gates, not model-layer gates.** System prompt instructions are overridable and context-dependent. PreToolUse hooks are not.

2. **Blast-radius-proportional gates.** A gate that blocks everything gets turned off. Gate intensity scales with (reversibility × scope) — see `docs/blast-radius-doctrine.md`.

3. **Fail-open on internal error, fail-safe on judgment unavailability.** An internal hook crash should never block legitimate work. But a missing judge for an external action should always default to deny.

---

## Docs

- [Why this exists](docs/why.md) — the incidents behind each gate
- [Blast radius doctrine](docs/blast-radius-doctrine.md) — sizing gates to impact
- [The lethal trifecta](docs/lethal-trifecta.md) — combination-level exposure
- [Autonomy ladder](examples/autonomy_ladder.md) — (reversibility, tier) → oversight level

---

## License

MIT
