"""Core document model for Mark Two.

The AST intentionally models the things the author writes about rather than
HTML elements. HTML is a rendering detail handled by renderer.py.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Button:
    name: str
    href: str = "#"
    color: str = "black"


@dataclass
class Subsection:
    title: str
    content: List[str] = field(default_factory=list)
    slug: Optional[str] = None


@dataclass
class Section:
    title: str
    content: List[str] = field(default_factory=list)
    subsections: List[Subsection] = field(default_factory=list)
    slug: Optional[str] = None


@dataclass
class RelatedLink:
    name: str
    href: str


@dataclass
class Document:
    document_title: str = ""
    article_title: str = ""
    buttons: List[Button] = field(default_factory=list)
    sections: List[Section] = field(default_factory=list)
    related_links: List[RelatedLink] = field(default_factory=list)
