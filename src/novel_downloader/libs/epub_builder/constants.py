#!/usr/bin/env python3
"""
novel_downloader.libs.epub_builder.constants
--------------------------------------------

EPUB-specific constants used by the builder.
"""

ROOT_PATH = "OEBPS"
IMAGE_DIR = "Images"
TEXT_DIR = "Text"
CSS_DIR = "Styles"
FONT_DIR = "Fonts"

XHTML_NS = "http://www.w3.org/1999/xhtml"
EPUB_NS = "http://www.idpf.org/2007/ops"
XML_NS = "http://www.w3.org/XML/1998/namespace"
NCX_NS = "http://www.daisy.org/z3986/2005/ncx/"
OPF_NS = "http://www.idpf.org/2007/opf"
DC_NS = "http://purl.org/dc/elements/1.1/"

IMAGE_MEDIA_TYPES: dict[str, str] = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "gif": "image/gif",
    "svg": "image/svg+xml",
    "webp": "image/webp",
}

FONT_FORMAT_MAP: dict[str, str] = {
    "ttf": "truetype",
    "otf": "opentype",
    "woff": "woff",
    "woff2": "woff2",
}

FONT_MEDIA_TYPES: dict[str, str] = {
    "ttf": "font/ttf",
    "otf": "font/otf",
    "woff": "font/woff",
    "woff2": "font/woff2",
}

CONTAINER_TEMPLATE = f"""\
<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfiles>
        <rootfile full-path="{ROOT_PATH}/content.opf"
            media-type="application/oebps-package+xml"/>
    </rootfiles>
</container>
"""

COVER_IMAGE_TEMPLATE = (
    '<div style="text-align: center; margin: 0; padding: 0;">'
    f'<img src="../{IMAGE_DIR}/cover.{{ext}}" alt="cover" '
    'style="max-width: 100%; height: auto;" />'
    "</div>"
)

DEFAULT_FONT_FALLBACK_STACK = (
    'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
)

FONT_FACE_TEMPLATE = """\
@font-face {{
  font-family: "{family}";
  src: url("../{font_dir}/{filename}") format("{format}");
}}
"""

COVER_TEMPLATE = f"""\
<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="{XHTML_NS}" xmlns:epub="{EPUB_NS}" lang="{{lang}}" xml:lang="{{lang}}">
<head>
  <title>{{title}}</title>
</head>
<body>
<div style="text-align: center; margin: 0; padding: 0;">
  <img src="../{IMAGE_DIR}/cover.{{ext}}" alt="cover" style="max-width: 100%; height: auto;" />
</div>
</body>
</html>
"""  # noqa: E501

XHTML_TEMPLATE = f"""\
<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="{XHTML_NS}" xmlns:epub="{EPUB_NS}" lang="{{lang}}" xml:lang="{{lang}}">
<head>
  <title>{{title}}</title>
  <link rel="stylesheet" href="../{CSS_DIR}/style.css" type="text/css"/>
{{font_styles}}
</head>
<body>
{{content}}
</body>
</html>
"""

INTRO_TEMPLATE = f"""\
<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="{XHTML_NS}" xmlns:epub="{EPUB_NS}" lang="{{lang}}" xml:lang="{{lang}}">
<head>
  <title>{{title}}</title>
  <link rel="stylesheet" href="../{CSS_DIR}/style.css" type="text/css"/>
{{font_styles}}
</head>
<body>
  <div class="intro">
    <h2 class="intro-title">{{title}}</h2>
    <div class="intro-info">
      {{info_block}}
    </div>
    {{description_block}}
  </div>
</body>
</html>
"""

VOLUME_COVER_TEMPLATE = f"""\
<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="{XHTML_NS}" xmlns:epub="{EPUB_NS}" lang="{{lang}}" xml:lang="{{lang}}">
<head>
  <title>{{title}}</title>
  <link rel="stylesheet" href="../{CSS_DIR}/style.css" type="text/css"/>
</head>
<body>
  <img class="width100" src="../{IMAGE_DIR}/{{image_name}}" alt="{{title}}"/>
</body>
</html>
"""

VOLUME_TITLE_TEMPLATE = f"""\
<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="{XHTML_NS}" xmlns:epub="{EPUB_NS}" lang="{{lang}}" xml:lang="{{lang}}">
<head>
  <title>{{full_title}}</title>
  <link rel="stylesheet" href="../{CSS_DIR}/style.css" type="text/css"/>
</head>
<body>
  <h1 class="head">{{line1}}<br/><b>{{line2}}</b></h1>
</body>
</html>
"""

VOLUME_INTRO_TEMPLATE = f"""\
<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="{XHTML_NS}" xmlns:epub="{EPUB_NS}" lang="{{lang}}" xml:lang="{{lang}}">
<head>
  <title>{{title}}</title>
  <link rel="stylesheet" href="../{CSS_DIR}/style.css" type="text/css"/>
{{font_styles}}
</head>
<body>
  <div>
    <h2 class="vol-title">{{title}}</h2>
    <div class="vol-description">
      {{description}}
    </div>
  </div>
</body>
</html>
"""

VOLUME_INTRO_DESC_TEMPLATE = f"""\
<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="{XHTML_NS}" xmlns:epub="{EPUB_NS}" lang="{{lang}}" xml:lang="{{lang}}">
<head>
  <title>{{title}}</title>
  <link rel="stylesheet" href="../{CSS_DIR}/style.css" type="text/css"/>
{{font_styles}}
</head>
<body>
  <div>
    <h3 class="vol-title">简介</h3>
    <div class="vol-description">
      {{description}}
    </div>
  </div>
</body>
</html>
"""

CHAP_TMPLATE = f"""\
<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="{XHTML_NS}" xmlns:epub="{EPUB_NS}" lang="{{lang}}" xml:lang="{{lang}}">
<head>
  <title>{{title}}</title>
  <link rel="stylesheet" href="../{CSS_DIR}/style.css" type="text/css"/>
{{font_styles}}
</head>
<body>
  <h2 class="chapter-title">{{title}}</h2>
  <div class="chapter-content">
    {{content}}
  </div>
  {{extra_block}}
</body>
</html>
"""

NAV_TEMPLATE = f"""\
<?xml version='1.0' encoding='utf-8'?>
<!DOCTYPE html>
<html xmlns="{XHTML_NS}" xmlns:epub="{EPUB_NS}" lang="{{lang}}" xml:lang="{{lang}}">
  <head>
    <title>{{title}}</title>
  </head>
  <body>
    <nav epub:type="toc" id="{{id}}" role="doc-toc">
      <h2>{{title}}</h2>
      <ol>
{{items}}
      </ol>
    </nav>
  </body>
</html>
"""

NCX_TEMPLATE = f"""\
<?xml version='1.0' encoding='utf-8'?>
<ncx xmlns="{NCX_NS}" version="2005-1">
  <head>
    <meta name="dtb:uid" content="{{uid}}"/>
    <meta name="dtb:depth" content="{{depth}}"/>
    <meta name="dtb:totalPageCount" content="0"/>
    <meta name="dtb:maxPageNumber" content="0"/>
  </head>
  <docTitle>
    <text>{{title}}</text>
  </docTitle>
  <navMap>
{{navpoints}}
  </navMap>
</ncx>
"""

OPF_TEMPLATE = f"""\
<?xml version='1.0' encoding='utf-8'?>
<package xmlns="{OPF_NS}" xmlns:dc="{DC_NS}" xmlns:opf="{OPF_NS}" version="3.0" unique-identifier="id" prefix="rendition: http://www.idpf.org/vocab/rendition/#">
  <metadata>
{{metadata}}
  </metadata>
  <manifest>
{{manifest_items}}
  </manifest>
  <spine{{spine_toc}}>
{{spine_items}}
  </spine>
</package>
"""  # noqa: E501
