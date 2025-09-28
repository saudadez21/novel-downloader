#!/usr/bin/env python3
"""
novel_downloader.apps.web.services.client_dialog
------------------------------------------------

Register a per-page login dialog and a polling timer to claim/handle credential requests
"""

import asyncio
import contextlib
from typing import Any

from nicegui import ui

from novel_downloader.infra.i18n import t
from novel_downloader.schemas import LoginField

from .cred_broker import (
    claim_next_request,
    complete_request,
    get_req_state,
    refresh_claim,
)


def setup_dialog() -> None:
    """
    Register the login dialog and a small poller in the current page context.
    """
    client_id = ui.context.client.id

    # local state per page instance
    curr_req_id: str | None = None

    with ui.dialog() as dialog, ui.card().classes("min-w-[360px]"):
        title_label = ui.label(t("Login Request")).classes("text-base font-medium")

        # dynamic form container
        form_col = ui.column().classes("w-full gap-2 mt-2")

        # name -> widget
        inputs: dict[str, Any] = {}

        def _build_form(req_fields: list[LoginField], prefill: dict[str, str]) -> None:
            """
            (Re)build inputs inside the dialog's form_col based on LoginField list.
            """
            form_col.clear()
            inputs.clear()
            with form_col:
                for idx, f in enumerate(req_fields):
                    with ui.column().classes("w-full gap-1"):
                        ui.label(f.label).classes("text-sm font-medium")
                        if getattr(f, "description", ""):
                            ui.label(t(f.description)).classes("text-xs text-caption")

                        initial = prefill.get(f.name, f.default or "")

                        # choose widget by type
                        if f.type == "password":
                            w = (
                                ui.input(
                                    t(f.label),
                                    password=True,
                                    value=initial,
                                    placeholder=t(f.placeholder) or "",
                                )
                                .props("dense")
                                .classes("w-full")
                            )
                            w.label = None
                        elif f.type == "cookie":
                            # cookie can be long
                            w = (
                                ui.textarea(
                                    t(f.label),
                                    value=initial,
                                    placeholder=t(f.placeholder) or "",
                                )
                                .props("dense")
                                .classes("w-full")
                            )
                            w.label = None
                        else:
                            # default: text
                            w = (
                                ui.input(
                                    t(f.label),
                                    value=initial,
                                    placeholder=t(f.placeholder) or "",
                                )
                                .props("dense")
                                .classes("w-full")
                            )
                            w.label = None

                        # optional niceties
                        if getattr(f, "required", False):
                            w.props("required")
                        if idx == 0:
                            w.props("autofocus")

                        inputs[f.name] = w

        def on_cancel() -> None:
            nonlocal curr_req_id
            if curr_req_id:
                asyncio.create_task(complete_request(curr_req_id, None))
            curr_req_id = None
            dialog.close()
            ui.notify(t("Login canceled"))

        def on_submit() -> None:
            nonlocal curr_req_id
            if not curr_req_id:
                return
            # collect values
            values: dict[str, str] = {}
            for name, w in inputs.items():
                values[name] = (w.value or "").strip()
            # send to broker
            asyncio.create_task(complete_request(curr_req_id, values))
            curr_req_id = None
            dialog.close()
            ui.notify(t("Submitted successfully"))

        with ui.row().classes("justify-end w-full mt-2"):
            ui.button(t("Cancel"), on_click=on_cancel).props("flat color=secondary")
            ui.button(t("Submit"), on_click=on_submit)

    dialog.props("persistent")

    async def check_and_open() -> None:
        nonlocal curr_req_id
        rid = curr_req_id
        if rid:
            exists, done = await get_req_state(rid)
            if (not exists) or done:
                curr_req_id = None
                if dialog.visible:
                    dialog.close()
            else:
                await refresh_claim(rid, client_id)
            return

        req = await claim_next_request(client_id)
        if not req:
            return
        curr_req_id = req.req_id
        title_label.text = f"'{req.title}' 需要登录信息"
        _build_form(req.fields, req.prefill)
        dialog.open()

    ui.timer(0.5, check_and_open)

    # Clean up if this page's websocket disconnects
    def _on_disconnect() -> None:
        nonlocal curr_req_id
        if curr_req_id:
            asyncio.create_task(complete_request(curr_req_id, None))
        curr_req_id = None

    with contextlib.suppress(Exception):
        ui.context.client.on_disconnect(_on_disconnect)
        # Fallback: CLAIM_TTL will release stale claims anyway
