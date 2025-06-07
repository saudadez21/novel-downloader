#!/usr/bin/env python3
"""
novel_downloader.tui.widgets.richlog_handler
--------------------------------------------

"""

import logging
from logging import LogRecord

from textual.widgets import RichLog


class RichLogHandler(logging.Handler):
    def __init__(self, rich_log_widget: RichLog):
        super().__init__()
        self.rich_log_widget = rich_log_widget

    def emit(self, record: LogRecord) -> None:
        msg = self.format(record)
        try:
            self.rich_log_widget.write(msg)
        except Exception:
            self.handleError(record)
