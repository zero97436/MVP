"""Points d'extension (hooks) — séparation open-core, Phase 2.

Permet au paquet privé `orbisys_enterprise` d'injecter de la logique payante dans
le noyau SANS que le noyau connaisse ce code. Le noyau appelle
`extensions.call("nom", ...)` ; si aucun hook n'est enregistré (édition Community),
il reçoit `default` et se comporte comme si la fonctionnalité était absente.

Les hooks sont enregistrés au démarrage de CHAQUE process qui en a besoin
(api, worker, scheduler) via `app.plugins.load_enterprise_hooks`.
"""
from __future__ import annotations

from typing import Any, Callable

_hooks: dict[str, Callable[..., Any]] = {}


def register(name: str, fn: Callable[..., Any]) -> None:
    """Enregistre (ou remplace) le hook `name`."""
    _hooks[name] = fn


def unregister(name: str) -> None:
    _hooks.pop(name, None)


def has(name: str) -> bool:
    return name in _hooks


def call(name: str, *args: Any, default: Any = None, **kwargs: Any) -> Any:
    """Appelle le hook `name` s'il existe, sinon retourne `default`."""
    fn = _hooks.get(name)
    if fn is None:
        return default
    return fn(*args, **kwargs)
