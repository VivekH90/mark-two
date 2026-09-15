"""Core document model for Mark Two."""

from dataclasses import dataclass, field
from typing import List, Optional, Union


@dataclass
class Button:
    name: str
    href: str = "#"
    color: str = "black"


@dataclass
class Image:
    """An article image with optional accessibility text and caption."""

    src: str
    alt: str = ""
    caption: str = ""


@dataclass
class Environment:
    """A semantic boxed environment such as theorem or definition."""

    kind: str
    title: str = ""
    content: List[Union[str, Image]] = field(default_factory=list)


ContentItem = Union[str, Image, Environment]


@dataclass
class Subsection:
    title: str
    content: List[ContentItem] = field(default_factory=list)
    slug: Optional[str] = None


@dataclass
class Section:
    title: str
    color: str = "#111111"
    content: List[ContentItem] = field(default_factory=list)
    subsections: List[Subsection] = field(default_factory=list)
    slug: Optional[str] = None


@dataclass
class RelatedLink:
    name: str
    href: str


@dataclass
class Document:
    document_title: str = ""
    banner: str = ""
    article_title: str = ""
    buttons: List[Button] = field(default_factory=list)
    sections: List[Section] = field(default_factory=list)
    related_links: List[RelatedLink] = field(default_factory=list)
