#!/usr/bin/env python3
"""
Async health check for novel sites.

  * Concurrency limited (default 12)
  * Runs aiohttp, curl_cffi, and httpx concurrently
  * Each site locked across libs to avoid duplicate hits

Usage:
  python scripts/check_sites_health.py
"""

from __future__ import annotations

import asyncio
import html
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from time import perf_counter
from typing import Any

import aiohttp
import httpx
from curl_cffi.requests import AsyncSession
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Table
from rich.text import Text

# ----------------------------
# Configuration
# ----------------------------

CONFIG_PATH = Path("scripts/data/site_health_config.json")
OUTPUT_PATH = Path("dev/site_health_report.html")

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/136.0.0.0 Safari/537.36"
)
USER_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",  # noqa: E501
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en,zh;q=0.9,zh-CN;q=0.8",
    "User-Agent": USER_AGENT,
    "Connection": "keep-alive",
}

HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Site Health Report</title>

<!-- Optional Highlight.js -->
<link rel="stylesheet"
      href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>

<script>
document.addEventListener('DOMContentLoaded', function() {
  if (typeof hljs !== 'undefined') {
    document.querySelectorAll('#failed-responses pre code').forEach(block => {
      hljs.highlightElement(block);
    });
  }
});
</script>

<style>
body {{
    font-family: monospace;
    background: #1e1e1e;
    color: #e0e0e0;
    padding: 1em 2em;
}}
pre {{
    background: #2a2a2a;
    color: #ccc;
    padding: 0.75em;
    white-space: pre-wrap;
    border-radius: 4px;
    overflow-x: auto;
}}
a {{
    color: #4ea1ff;
}}
h1 {{
    color: #ffd166;
    margin-bottom: 0.2em;
}}
h2 {{
    color: #06d6a0;
    margin-top: 1.5em;
    border-bottom: 1px solid #333;
    padding-bottom: 0.3em;
}}
h3 {{
    color: #ef476f;
    margin-top: 1em;
}}
hr {{
    border: 0;
    border-top: 1px solid #333;
    margin: 2em 0;
}}
</style>
</head>
<body>
<h1>Site Health Summary ({timestamp})</h1>
{summary_html}
<hr>
<h2>Failed Responses</h2>
<div id="failed-responses">
{failed_html}
</div>
</body>
</html>
"""

console = Console()

# ----------------------------
# Data structure
# ----------------------------


@dataclass
class SiteResult:
    site: str
    lib: str
    url: str
    status: int
    text: str
    elapsed: float


# ----------------------------
# Utilities
# ----------------------------


def load_config(cfg_path: Path) -> dict[str, Any] | None:
    if not cfg_path.is_file():
        return None
    with open(cfg_path, encoding="utf-8") as f:
        return json.load(f)


def save_html_summary(
    grouped: dict[str, dict[str, list[SiteResult]]],
    slow_t: float,
    very_slow_t: float,
    output_path: Path = OUTPUT_PATH,
) -> None:
    """Render the site check summary as a standalone HTML report."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    console = Console(record=True, width=140)
    console.print("\n[bold cyan]=== Site Health Summary ===[/bold cyan]\n")
    failed_entries: list[tuple[str, str, str, str]] = []  # (lib, site, url, text)

    for lib_name, sites in grouped.items():
        table = Table(
            title=f"[cyan]{lib_name}[/cyan]",
            show_header=True,
            header_style="bold magenta",
            expand=True,
        )
        table.add_column("Status", justify="center", no_wrap=True)
        table.add_column("Time", justify="right", no_wrap=True)
        table.add_column("Site", justify="left", no_wrap=True)
        table.add_column("URL", justify="left")

        for res_list in sites.values():
            for r in res_list:
                # Status color
                if r.status <= 0:
                    s_style = "red"
                    status_text = Text("ERR", style=s_style)
                elif r.status < 300:
                    s_style = "green"
                    status_text = Text(str(r.status), style=s_style)
                elif r.status < 400:
                    s_style = "yellow"
                    status_text = Text(str(r.status), style=s_style)
                else:
                    s_style = "red"
                    status_text = Text(str(r.status), style=s_style)

                # Time color
                if r.elapsed > very_slow_t:
                    t_style = "red"
                elif r.elapsed > slow_t:
                    t_style = "yellow"
                else:
                    t_style = "green"
                time_text = Text(f"{r.elapsed:.2f}s", style=t_style)

                table.add_row(status_text, time_text, r.site, r.url)

                if r.status >= 400 or r.status == 0:
                    failed_entries.append((lib_name, r.site, r.url, r.text))

        console.print(table)

    # Rich-rendered console HTML
    summary_html = console.export_html(inline_styles=True)

    # Build failed response section
    failed_parts: list[str] = []
    for lib, site, url, text in failed_entries:
        failed_parts.append(
            f"<h3>{lib} :: {site}</h3>"
            f"<p><a href='{url}' target='_blank'>{url}</a></p>"
            f"<pre><code class='language-html'>{html.escape(text or '')}</code></pre>"
        )

    # Fill in template
    html_output = HTML_TEMPLATE.format(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        summary_html=summary_html,
        failed_html="\n".join(failed_parts),
    )

    output_path.write_text(html_output, encoding="utf-8")
    print(f"[HTML] Report saved to: {output_path.resolve()}")


# ----------------------------
# Fetchers
# ----------------------------


async def fetch_aiohttp(
    site: str, urls: list[str], cfg: dict[str, Any]
) -> list[SiteResult]:
    results = []
    async with aiohttp.ClientSession(
        headers=USER_HEADERS, timeout=aiohttp.ClientTimeout(total=cfg["timeout"])
    ) as sess:
        for url in urls:
            start = perf_counter()
            try:
                async with sess.get(url) as resp:
                    text = await resp.text(errors="ignore")
                    results.append(
                        SiteResult(
                            site,
                            "aiohttp",
                            url,
                            resp.status,
                            text,
                            perf_counter() - start,
                        )
                    )
            except Exception as e:
                results.append(
                    SiteResult(site, "aiohttp", url, 0, str(e), perf_counter() - start)
                )
    return results


async def fetch_httpx(
    site: str, urls: list[str], cfg: dict[str, Any]
) -> list[SiteResult]:
    results = []
    async with httpx.AsyncClient(
        headers=USER_HEADERS, timeout=cfg["timeout"], follow_redirects=True
    ) as client:
        for url in urls:
            start = perf_counter()
            try:
                resp = await client.get(url)
                results.append(
                    SiteResult(
                        site,
                        "httpx",
                        url,
                        resp.status_code,
                        resp.text,
                        perf_counter() - start,
                    )
                )
            except Exception as e:
                results.append(
                    SiteResult(site, "httpx", url, 0, str(e), perf_counter() - start)
                )
    return results


async def fetch_curl_cffi(
    site: str, urls: list[str], cfg: dict[str, Any]
) -> list[SiteResult]:
    results = []
    async with AsyncSession(
        headers=USER_HEADERS, timeout=cfg["timeout"], impersonate="chrome136"
    ) as sess:
        for url in urls:
            start = perf_counter()
            try:
                resp = await sess.get(url)
                results.append(
                    SiteResult(
                        site,
                        "curl_cffi",
                        url,
                        resp.status_code,
                        resp.text,
                        perf_counter() - start,
                    )
                )
            except Exception as e:
                results.append(
                    SiteResult(
                        site, "curl_cffi", url, 0, str(e), perf_counter() - start
                    )
                )
    return results


# ----------------------------
# Main Runner
# ----------------------------


async def run_check_for_lib(
    lib_name: str,
    config: dict[str, Any],
    site_locks: dict[str, asyncio.Lock],
    progress: Progress,
    task_id: TaskID,
) -> dict[str, list[SiteResult]]:
    sem = asyncio.Semaphore(config.get("max_concurrent", 12))
    sites = config["sites"]
    results: dict[str, list[SiteResult]] = {}

    async def run_site(site_key: str, urls: list[str]):
        lock = site_locks[site_key]
        async with sem, lock:
            if lib_name == "aiohttp":
                r = await fetch_aiohttp(site_key, urls, config)
            elif lib_name == "httpx":
                r = await fetch_httpx(site_key, urls, config)
            else:
                r = await fetch_curl_cffi(site_key, urls, config)
            results[site_key] = r
            progress.advance(task_id)

    await asyncio.gather(*(run_site(k, v["urls"]) for k, v in sites.items()))
    return results


# ----------------------------
# Orchestrator
# ----------------------------


async def async_main() -> int:
    config = load_config(CONFIG_PATH)
    if config is None:
        console.print(f"[red]Config file not found: {CONFIG_PATH}[/red]")
        return 1

    slow_t = config["speed_levels"]["slow"]
    very_slow_t = config["speed_levels"]["very_slow"]
    site_locks = {k: asyncio.Lock() for k in config["sites"]}

    grouped: dict[str, dict[str, list[SiteResult]]] = {}

    with Progress(
        SpinnerColumn(),
        TextColumn("{task.description}"),
        BarColumn(),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        tasks = {}
        for lib in ("aiohttp", "curl_cffi", "httpx"):
            task_id = progress.add_task(
                f"[cyan]{lib}[/cyan]", total=len(config["sites"])
            )
            coro = run_check_for_lib(lib, config, site_locks, progress, task_id)
            tasks[lib] = asyncio.create_task(coro)

        for lib, t in tasks.items():
            grouped[lib] = await t

    save_html_summary(grouped, slow_t, very_slow_t)
    return 0


def main() -> None:
    raise SystemExit(asyncio.run(async_main()))


if __name__ == "__main__":
    main()
