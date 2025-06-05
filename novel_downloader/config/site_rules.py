#!/usr/bin/env python3
"""
novel_downloader.config.site_rules
----------------------------------

Handles loading, saving, and caching of site-specific scraping rules.

This module provides functionality to:
- Load site rules from JSON, YAML, or TOML formats.
- Save rules into a standard JSON format.
"""

import json
import logging
from pathlib import Path

from novel_downloader.models import SiteRulesDict
from novel_downloader.utils.cache import cached_load_config
from novel_downloader.utils.constants import SITE_RULES_FILE
from novel_downloader.utils.file_utils import save_as_json

logger = logging.getLogger(__name__)


def save_rules_as_json(
    source_path: str | Path, output_path: str | Path = SITE_RULES_FILE
) -> None:
    """
    Load rules from source_path (toml, yaml, or json) and save as JSON.

    :param source_path: Path to the source rules file
                        (supports .toml, .yaml, .yml, .json).
    :param output_path: Path where the JSON output will be saved.
                        Defaults to SITE_RULES_FILE.
    :raises FileNotFoundError: If the source_path does not exist.
    :raises ValueError: If the source file format is not supported.
    :raises Exception: If file loading or saving fails.
    """
    TAG = "[Config]"
    source_path = Path(source_path)
    output_path = Path(output_path)

    if not source_path.exists():
        raise FileNotFoundError(f"Source file {source_path} not found.")

    suffix = source_path.suffix.lower()

    logger.debug("%s Loading rules from %s (format: %s)", TAG, source_path, suffix)

    try:
        if suffix == ".toml":
            import tomllib

            with source_path.open("rb") as f:
                rules_data = tomllib.load(f)
        elif suffix in {".yaml", ".yml"}:
            import yaml

            with source_path.open("r", encoding="utf-8") as f:
                rules_data = yaml.safe_load(f)
        elif suffix == ".json":
            with source_path.open("r", encoding="utf-8") as f:
                rules_data = json.load(f)
        else:
            raise ValueError(f"Unsupported input format: {suffix}")

    except Exception as e:
        logger.error("%s Failed to load rules from %s: %s", TAG, source_path, str(e))
        raise

    logger.info("%s Saving rules to %s as JSON", TAG, output_path)

    save_as_json(rules_data, output_path)
    return


@cached_load_config
def load_site_rules(json_path: str | Path = SITE_RULES_FILE) -> SiteRulesDict:
    """
    Loads site scraping rules from a JSON file and caches the result for future access.

    :param json_path: Path to the site rules JSON file. Defaults to SITE_RULES_FILE.
    :return: A dictionary containing all site-specific scraping rules.
    """
    json_path = Path(json_path)
    site_rules: SiteRulesDict = {}

    if not json_path.exists():
        return site_rules

    with json_path.open("r", encoding="utf-8") as f:
        site_rules = json.load(f)

    return site_rules
