#!/usr/bin/env python3
"""
novel_downloader.web.state
--------------------------

"""

from novel_downloader.config import load_config
from novel_downloader.web.task_manager import TaskManager

settings = load_config()
task_manager: TaskManager = TaskManager(settings)
