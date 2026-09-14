"""ethos_gate.hooks — PreToolUse and Stop hook implementations."""

from .irreversible_guard import handle_pretooluse, handle_stop, main as irreversible_main
from .credential_scrape import evaluate as credential_evaluate, Verdict, ALLOW

__all__ = [
    "handle_pretooluse",
    "handle_stop",
    "irreversible_main",
    "credential_evaluate",
    "Verdict",
    "ALLOW",
]
