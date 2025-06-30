#!/usr/bin/env python3
"""
novel_downloader.tui.screens.login
----------------------------------

"""

from typing import Any

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Static

from novel_downloader.models import LoginField


class LoginScreen(Screen):  # type: ignore[misc]
    """
    A modal screen that gathers login fields, then fires LoginScreen.Submitted.
    """

    BINDINGS = [("escape", "app.pop_screen", "取消")]

    def __init__(
        self,
        fields: list[LoginField],
        cfg: dict[str, Any] | None = None,
    ) -> None:
        super().__init__()
        self.fields = fields
        self.cfg = cfg or {}

    def compose(self) -> ComposeResult:
        widgets = []
        for field in self.fields:
            # show label and optional description
            widgets.append(Static(field.label))
            if field.description:
                widgets.append(Static(f"[i]{field.description}[/]"))

            # pick input type
            if field.type == "password":
                inp = Input(
                    placeholder=field.placeholder or "",
                    password=True,
                    id=field.name,
                )
            else:
                inp = Input(
                    placeholder=field.placeholder or "",
                    id=field.name,
                )

            # pre-fill from config if present
            existing = self.cfg.get(field.name, "").strip()
            if existing:
                inp.value = existing

            widgets.append(inp)

        # submit button at the end
        widgets.append(Button("提交", id="submit"))
        yield Vertical(*widgets, id="login-form")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "submit":
            data: dict[str, Any] = {}
            for field in self.fields:
                inp = self.query_one(f"#{field.name}", Input)
                value = inp.value
                if not value and self.cfg.get(field.name):
                    value = self.cfg[field.name]
                data[field.name] = value
