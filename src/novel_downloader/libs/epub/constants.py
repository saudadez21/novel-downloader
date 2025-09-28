#!/usr/bin/env python3
"""
novel_downloader.libs.epub.constants
------------------------------------

EPUB-specific constants used by the builder.
"""

ROOT_PATH = "OEBPS"
IMAGE_FOLDER = "Images"
TEXT_FOLDER = "Text"
CSS_FOLDER = "Styles"

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

CONTAINER_TEMPLATE = """\
<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfiles>
        <rootfile full-path="{root_path}/content.opf"
            media-type="application/oebps-package+xml"/>
    </rootfiles>
</container>
"""

COVER_IMAGE_TEMPLATE = (
    f'<div style="text-align: center; margin: 0; padding: 0;">'
    f'<img src="../{IMAGE_FOLDER}/cover.{{ext}}" alt="cover" '
    f'style="max-width: 100%; height: auto;" />'
    f"</div>"
)

CSS_TMPLATE = (
    f'<link href="../{CSS_FOLDER}/{{filename}}" '
    f'rel="stylesheet" type="{{media_type}}"/>'
)

CHAP_TMPLATE = f"""\
<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="{XHTML_NS}" xmlns:epub="{EPUB_NS}" lang="{{lang}}" xml:lang="{{lang}}">
  <head>
    <title>{{title}}</title>
{{xlinks}}
  </head>
  <body>{{content}}</body>
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
{{guide_section}}</package>
"""  # noqa: E501
