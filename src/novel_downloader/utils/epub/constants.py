#!/usr/bin/env python3
"""
novel_downloader.utils.epub.constants
-------------------------------------

EPUB-specific constants used by the builder, including:
- Directory names for OEBPS structure
- XML namespace URIs
- Package attributes and document-type declarations
- Media type mappings for images
- Template strings for container.xml and cover image HTML
"""

PRETTY_PRINT_FLAG = True
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

OPF_PKG_ATTRIB = {
    "version": "3.0",
    "unique-identifier": "id",
    "prefix": "rendition: http://www.idpf.org/vocab/rendition/#",
}
CHAP_DOC_TYPE = (
    '<?xml version="1.0" encoding="utf-8"?>\n'
    "<!DOCTYPE html PUBLIC "
    '"-//W3C//DTD XHTML 1.1//EN" '
    '"http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">\n'
)

IMAGE_MEDIA_TYPES: dict[str, str] = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "gif": "image/gif",
    "svg": "image/svg+xml",
    "webp": "image/webp",
}

CONTAINER_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfiles>
        <rootfile full-path="{root_path}/content.opf"
            media-type="application/oebps-package+xml"/>
    </rootfiles>
</container>"""

COVER_IMAGE_TEMPLATE = (
    f'<div style="text-align: center; margin: 0; padding: 0;">'
    f'<img src="../{IMAGE_FOLDER}/cover.{{ext}}" alt="cover" '
    f'style="max-width: 100%; height: auto;" />'
    f"</div>"
)
