#!/usr/bin/env python3
"""
novel_downloader.cli.services.login
-----------------------------------

"""

from typing import Any

from novel_downloader.cli import ui
from novel_downloader.core import FetcherProtocol
from novel_downloader.models import LoginField
from novel_downloader.utils.cookies import parse_cookies
from novel_downloader.utils.i18n import t


async def ensure_login(
    fetcher: FetcherProtocol,
    login_config: dict[str, str] | None = None,
) -> bool:
    if await fetcher.load_state():
        return True

    login_data = await _prompt_login_fields(fetcher.login_fields, login_config)
    if not await fetcher.login(**login_data):
        ui.error(t("download_login_failed"))
        return False

    await fetcher.save_state()
    return True


async def _prompt_login_fields(
    fields: list[LoginField],
    login_config: dict[str, str] | None = None,
) -> dict[str, Any]:
    """
    Prompt for required login fields, honoring defaults and config-provided values.

    :param fields: Field descriptors from the fetcher (name/label/type/etc.).
    :param login_config: Optional values already configured by the user.
    :return: A dict suitable to pass to `fetcher.login(**kwargs)`.
    """
    login_config = login_config or {}
    result: dict[str, Any] = {}

    for field in fields:
        ui.info(f"\n{field.label} ({field.name})")
        if field.description:
            ui.info(f"{t('login_description')}: {field.description}")
        if field.placeholder:
            ui.info(f"{t('login_hint')}: {field.placeholder}")

        existing_value = login_config.get(field.name, "").strip()
        if existing_value:
            result[field.name] = existing_value
            ui.info(t("login_use_config"))
            continue

        value: str | dict[str, str] = ""
        for _ in range(5):
            if field.type == "password":
                value = ui.prompt_password(t("login_enter_password"))
            elif field.type == "cookie":
                value = ui.prompt(t("login_enter_cookie"))
                value = parse_cookies(value)
            else:
                value = ui.prompt(t("login_enter_value"))

            if not value and field.default:
                value = field.default

            if not value and field.required:
                ui.warn(t("login_required_field"))
            else:
                break

        result[field.name] = value

    return result
