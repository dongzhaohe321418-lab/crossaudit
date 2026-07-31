"""Provider lookup. Unknown names deny; they never fall back to a default."""
from __future__ import annotations

from typing import Callable

from ..errors import ConfigDenial
from . import anthropic, openai_compat, replay

_PROVIDERS: dict[str, Callable[..., object]] = {
    "anthropic": anthropic.complete,
    "openai_compat": openai_compat.complete,
    "replay": replay.complete,
}

#: Providers that make no external claim about a model's judgement.
NON_EVIDENTIAL = frozenset({"replay"})


def list_providers() -> list[str]:
    return sorted(_PROVIDERS)


def get_provider(name: str) -> Callable[..., object]:
    try:
        return _PROVIDERS[name]
    except KeyError:
        raise ConfigDenial(f"unknown provider {name!r}; available: {list_providers()}",
                           provider=name) from None
