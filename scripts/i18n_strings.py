#!/usr/bin/env python3
"""
Some user-facing strings are stored as data structures in the core code
and are not wrapped in `t("...")` calls.

These strings would otherwise be ignored by `xgettext` during
translation template extraction.

This file provides dummy `t("...")` calls so that such strings are
included in `messages.pot`.
"""

from novel_downloader.infra.i18n import t

# Login fields: username & password
t("Username")
t("Password")
t("Enter your username")
t("Enter your password")
t("The username used for login")
t("The password used for login")

# Login field: cookie
t("Cookie")
t("Paste your login cookies here")
t("Copy the cookies from your browser's developer tools while logged in.")
