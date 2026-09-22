# Mark Two AST

## 1. What is the AST?

The **AST**, or **Abstract Syntax Tree**, is the internal data model used by Mark Two to represent a parsed `.mt` document.

It sits between the parser and the renderer:

~~~text
Mark Two source (.mt)
        │
        ▼
     PARSER
        │
        ▼
       AST
   (ast.py model)
        │
        ▼
    RENDERER
        │
        ▼
     HTML/CSS/JS
~~~

The AST does not store the source merely as raw text. It stores the **meaning and structure** of the document.

For example, the source

~~~text
@section{Real Analysis}
~~~

can become a structured object:

~~~text
Section
    title = "Real Analysis"
~~~

The renderer can then inspect that object and decide how the section becomes HTML.

---

## 2. AST hierarchy

A Mark Two document can be viewed as this tree:

~~~text
DOCUMENT
│
├── BUTTONS
│     └── Button
│
├── SECTIONS
│     │
│     └── Section
│           │
│           ├── CONTENT
│           │     ├── String
│           │     ├── Image
│           │     ├── MathBlock
│           │     ├── TextBlock
│           │     ├── Label
│           │     ├── Reference
│           │     ├── ListBlock
│           │     └── Environment
│           │
│           └── SUBSECTIONS
│                 └── Subsection
│                       └── CONTENT
│
└── RELATED LINKS
      └── RelatedLink
~~~

The root node is always a `Document`.

---

# 11. Raw algorithmic view

`ast.py` does not contain a parsing algorithm in the normal sense.

There is no:

~~~text
FOR each line...
~~~

and there is no:

~~~text
IF line starts with @section...
~~~

Those operations belong to the parser.

The AST is instead a **data structure specification**.

A raw algorithmic description is:

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
    article_title = ""

    buttons = EMPTY LIST
    sections = EMPTY LIST
    related_links = EMPTY LIST
END Document
~~~
