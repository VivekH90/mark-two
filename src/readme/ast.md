# Abstract Syntax Tree 

~~~text
DEFINE Button
    name
    href = "#"
    color = "black"
END Button

DEFINE Image
    source
    alternative_text = ""
    caption = ""
    label = ""
    width = ""
    height = ""
    group = NONE
END Image

DEFINE MathBlock
    content
END MathBlock

DEFINE TextBlock
    text
    bold = FALSE
    italic = FALSE
    color = ""
END TextBlock

DEFINE Label
    name
END Label

DEFINE Reference
    target
    text = ""
END Reference

DEFINE ListItem
    content = EMPTY LIST
    title = ""
END ListItem

DEFINE ListBlock
    ordered
    items = EMPTY LIST
    color = "black"
END ListBlock

DEFINE Environment
    kind
    title = ""
    label = ""
    content = EMPTY LIST
END Environment

CONTENT_ITEM CAN BE
    String
    Image
    MathBlock
    TextBlock
    Label
    Reference
    ListBlock
    Environment
END CONTENT_ITEM

DEFINE Subsection
    title
    content = EMPTY LIST
    slug = NONE
    label = ""
END Subsection

DEFINE Section
    title
    color = "#111111"
    content = EMPTY LIST
    subsections = EMPTY LIST
    slug = NONE
    label = ""
END Section

DEFINE RelatedLink
    name
    href
END RelatedLink

DEFINE Document
    document_title = ""
    banner = ""
    banner_color = ""
    author = ""
    article_title = ""

    buttons = EMPTY LIST
    sections = EMPTY LIST
    related_links = EMPTY LIST
END Document
~~~
