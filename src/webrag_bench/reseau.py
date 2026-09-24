"""Garde réseau : aucun site tiers n'est contacté, jamais.

Installée au démarrage de chaque worker. Toute connexion sortante vers un hôte
absent de la liste blanche lève une exception, au lieu d'être tentée. La liste
blanche ne contient que la boucle locale et les points d'accès des générateurs
et de l'embedder déclarés dans le plan (clés API, machine OVH).
"""

from __future__ import annotations

import ipaddress
import socket

_ORIGINAL_CONNECT = socket.socket.connect
_ORIGINAL_CREATE_CONNECTION = socket.create_connection
_hotes_autorises: set[str] = set()


class ConnexionInterdite(RuntimeError):
    pass


def _est_locale(hote: str) -> bool:
    if hote in {"localhost", ""}:
        return True
    try:
        return ipaddress.ip_address(hote).is_loopback
    except ValueError:
        return False


def _controler(adresse: object) -> None:
    if isinstance(adresse, tuple) and adresse:
        hote = str(adresse[0])
        if _est_locale(hote) or hote in _hotes_autorises:
            return
        raise ConnexionInterdite(
            f"connexion sortante refusée vers {hote!r} : hors liste blanche "
            "(aucun site tiers n'est contacté ; seuls les générateurs déclarés le sont)"
        )
    # sockets Unix et autres familles : locales par construction


def installer_garde(hotes_autorises: set[str]) -> None:
    """Active la garde. `hotes_autorises` : noms d'hôte ET adresses résolues."""
    resolus = set(hotes_autorises)
    for h in hotes_autorises:
        try:
            for info in socket.getaddrinfo(h, None):
                resolus.add(str(info[4][0]))
        except OSError:
            pass
    _hotes_autorises.clear()
    _hotes_autorises.update(resolus)

    def connect(self: socket.socket, adresse: object) -> None:
        _controler(adresse)
        return _ORIGINAL_CONNECT(self, adresse)

    def create_connection(adresse: tuple, *args: object, **kwargs: object) -> socket.socket:
        _controler(adresse)
        return _ORIGINAL_CREATE_CONNECTION(adresse, *args, **kwargs)  # type: ignore[arg-type]

    socket.socket.connect = connect  # type: ignore[method-assign]
    socket.create_connection = create_connection  # type: ignore[assignment]


def retirer_garde() -> None:
    socket.socket.connect = _ORIGINAL_CONNECT  # type: ignore[method-assign]
    socket.create_connection = _ORIGINAL_CREATE_CONNECTION  # type: ignore[assignment]
    _hotes_autorises.clear()
