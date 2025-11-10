#!/usr/bin/env python3
"""
novel_downloader.libs.html_builder.constants
--------------------------------------------
"""

CHAPTER_DIR = "chapters"
CSS_DIR = "css"
JS_DIR = "js"
MEDIA_DIR = "media"

IMAGE_MEDIA_EXTS: dict[str, str] = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/gif": "gif",
    "image/svg+xml": "svg",
    "image/webp": "webp",
}

INDEX_TEMPLATE = """\
<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="utf-8">
  <title>{book_name}</title>
  <link rel="stylesheet" href="css/index.css">
  <script defer src="js/main.js"></script>
</head>
<body>
  <div id="progress-bar"></div>

  <header>
    {header}
  </header>

  <main class="toc">
    <h2>目录</h2>
    {toc_html}
  </main>

  <!-- Floating controls -->
  <div id="floating-controls">
    <button id="font-minus" title="减小字体">A-</button>
    <button id="font-plus" title="增大字体">A+</button>
    <button id="scroll-top" title="回到顶部">↑</button>
    <button id="scroll-bottom" title="到底部">↓</button>
  </div>
</body>
</html>
"""

CHAPTER_TEMPLATE = """\
<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <link rel="stylesheet" href="../css/chapter.css">
  <script defer src="../js/main.js"></script>
</head>
<body>
  <div id="progress-bar"></div>

  <h1>{title}</h1>
  <div class="chapter-content">
    {content}
  </div>

  <nav class="chapter-nav"
       data-prev="{prev_link}"
       data-next="{next_link}"
       data-menu="../index.html">
    <a id="prev-link" href="{prev_link}" class="nav-button">← 上一章</a>
    <a id="menu-link" href="../index.html" class="nav-button">☰ 目录</a>
    <a id="next-link" href="{next_link}" class="nav-button">下一章 →</a>
  </nav>

  <!-- Floating controls -->
  <div id="floating-controls" data-menu="../index.html">
    <button id="menu-button" title="目录">☰</button>
    <button id="toggle-sticky" title="固定导航">S</button>
    <button id="font-minus" title="减小字体">A-</button>
    <button id="font-plus" title="增大字体">A+</button>
    <button id="scroll-top" title="回到顶部">↑</button>
    <button id="scroll-bottom" title="到底部">↓</button>
  </div>
</body>
</html>
"""
