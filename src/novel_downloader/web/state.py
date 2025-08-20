#!/usr/bin/env python3
"""
novel_downloader.web.state
--------------------------

"""

from typing import Any

from nicegui import ui

from novel_downloader.config import load_config
from novel_downloader.web.task_manager import TaskManager

settings = load_config()
task_manager: TaskManager = TaskManager(settings)
ui_portal: Any | None = None
_portals: dict[str, Any] = {}


def get_portal(client_id: str | None) -> Any:
    """
    Return the portal for the given client, or any existing one as fallback.
    """
    if client_id is not None and client_id in _portals:
        return _portals[client_id]
    return next(iter(_portals.values()), None)


def register_portal() -> str:
    """
    Create/replace a portal for the current client.
    """
    client = ui.context.client
    cid = client.id
    _portals[cid] = ui.element("div")
    return cid  # type: ignore[no-any-return]
