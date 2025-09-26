#!/usr/bin/env python3
"""
novel_downloader.apps.cli.commands.base
---------------------------------------

"""

from abc import ABC, abstractmethod
from argparse import ArgumentParser, Namespace, _SubParsersAction


class Command(ABC):
    name: str
    help: str

    @classmethod
    def register(cls, subparsers: "_SubParsersAction[ArgumentParser]") -> None:
        parser = subparsers.add_parser(cls.name, help=cls.help)
        cls.add_arguments(parser)
        parser.set_defaults(func=cls.run)

    @classmethod
    def add_arguments(cls, parser: ArgumentParser) -> None:
        return

    @classmethod
    @abstractmethod
    def run(cls, args: Namespace) -> None:
        pass
