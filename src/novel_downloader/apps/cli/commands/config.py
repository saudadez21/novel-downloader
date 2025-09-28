#!/usr/bin/env python3
"""
novel_downloader.apps.cli.commands.config
-----------------------------------------

"""

from argparse import ArgumentParser, Namespace, _SubParsersAction
from pathlib import Path

from novel_downloader.apps.cli import ui
from novel_downloader.infra.config import copy_default_config, save_config_file
from novel_downloader.infra.i18n import t
from novel_downloader.infra.paths import DEFAULT_CONFIG_FILENAME
from novel_downloader.infra.persistence.state import state_mgr

from .base import Command

LANG_MAP = {
    "zh": "zh_CN",
    "en": "en_US",
}


class ConfigCmd(Command):
    name = "config"
    help = t("Manage application configuration and settings")

    @classmethod
    def register(cls, subparsers: "_SubParsersAction[ArgumentParser]") -> None:
        parser = subparsers.add_parser(cls.name, help=cls.help)
        sub = parser.add_subparsers(dest="subcommand", required=True)

        for subcmd in (ConfigInitCmd, ConfigSetLangCmd, ConfigSetConfigCmd):
            subcmd.register(sub)

    @classmethod
    def run(cls, args: Namespace) -> None:
        raise NotImplementedError("ConfigCmd should not be executed directly")


class ConfigInitCmd(Command):
    name = "init"
    help = t("Initialize default configuration files in the current directory.")

    @classmethod
    def add_arguments(cls, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--force",
            action="store_true",
            help=t("Force overwrite if the file already exists."),
        )

    @classmethod
    def run(cls, args: Namespace) -> None:
        target_path = Path.cwd() / DEFAULT_CONFIG_FILENAME
        should_copy = True

        if target_path.exists():
            if args.force:
                ui.warn(
                    t("Overwriting existing file: {filename}").format(
                        filename=DEFAULT_CONFIG_FILENAME
                    )
                )
            else:
                ui.info(
                    t("File already exists: {filename}").format(
                        filename=DEFAULT_CONFIG_FILENAME
                    )
                )
                should_copy = ui.confirm(
                    t("Do you want to overwrite {filename}?").format(
                        filename=DEFAULT_CONFIG_FILENAME
                    ),
                    default=False,
                )

        if not should_copy:
            ui.warn(t("Skipped: {filename}").format(filename=DEFAULT_CONFIG_FILENAME))
            return

        try:
            copy_default_config(target_path)
            ui.success(t("Copied: {filename}").format(filename=DEFAULT_CONFIG_FILENAME))
        except Exception as e:
            ui.error(
                t("Failed to copy {filename}: {err}").format(
                    filename=DEFAULT_CONFIG_FILENAME, err=str(e)
                )
            )
            raise


class ConfigSetLangCmd(Command):
    name = "set-lang"
    help = t("Set the interface language.")

    @classmethod
    def add_arguments(cls, parser: ArgumentParser) -> None:
        parser.add_argument("lang", help="Language code (e.g. zh, zh_CN)")

    @classmethod
    def run(cls, args: Namespace) -> None:
        lang_input: str = args.lang
        lang_std = LANG_MAP.get(lang_input, lang_input)
        state_mgr.set_language(lang_std)
        ui.success(t("Language switched to {lang}").format(lang=lang_std))


class ConfigSetConfigCmd(Command):
    name = "set-config"
    help = t("Set and save a custom TOML configuration file.")

    @classmethod
    def add_arguments(cls, parser: ArgumentParser) -> None:
        parser.add_argument("path", type=str, help="Path to the configuration file")

    @classmethod
    def run(cls, args: Namespace) -> None:
        try:
            save_config_file(args.path)
            ui.success(
                t("Configuration file saved from {path}.").format(path=args.path)
            )
        except Exception as e:
            ui.error(t("Failed to save configuration file: {err}").format(err=str(e)))
            raise
