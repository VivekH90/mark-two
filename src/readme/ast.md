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

## 2. What `src/ast.py` actually does

`src/ast.py` defines the Python classes that make up the Mark Two document model.

It mainly contains:

- data classes
- fields stored by each node
- default values
- type relationships between nodes

It does **not** parse `.mt` source files.

It does **not** generate HTML.

It defines the structures that the parser creates and the renderer consumes.

Conceptually:

~~~text
parser.py
    │
    │ creates
    ▼
ast.py objects
    │
    │ consumed by
    ▼
renderer.py
~~~

---

## 3. The complete pipeline

~~~text
                 MARK TWO COMPILER

       .mt SOURCE FILE
              │
              ▼
        ┌─────────────┐
        │   PARSER    │
        └─────────────┘
              │
              │ creates semantic objects
              ▼
        ┌─────────────┐
        │     AST     │
        │   ast.py    │
        └─────────────┘
              │
              │ traverses objects
              ▼
        ┌─────────────┐
        │  RENDERER   │
        │ renderer.py │
        └─────────────┘
              │
              ▼
          HTML/CSS/JS
~~~

The responsibilities are separated:

~~~text
PARSER
"What did the author write?"

AST
"What structure does it represent?"

RENDERER
"How should that structure become HTML?"
~~~

---

## 4. AST hierarchy

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

# 5. Node definitions

## 5.1 Button

~~~text
Button
├── name
├── href = "#"
└── color = "black"
~~~

A `Button` represents a navigation or action button.

| Field | Meaning |
|---|---|
| `name` | Text displayed on the button |
| `href` | Destination URL or anchor |
| `color` | Button color |

Conceptually:

~~~python
Button(
    name="Home",
    href="/",
    color="black"
)
~~~

---

## 5.2 Image

~~~text
Image
├── src
├── alt = ""
├── caption = ""
├── label = ""
├── width = ""
├── height = ""
└── group = NONE
~~~

An `Image` represents an article image.

| Field | Meaning |
|---|---|
| `src` | Image source/path |
| `alt` | Alternative text |
| `caption` | Caption |
| `label` | Identifier used for references |
| `width` | Requested width |
| `height` | Requested height |
| `group` | Optional image group identifier |

---

## 5.3 MathBlock

~~~text
MathBlock
└── content
~~~

A `MathBlock` stores a display-math expression.

Example:

~~~python
MathBlock(
    content="E = mc^2"
)
~~~

The AST stores the mathematical content. Rendering and MathJax handling belong to the renderer/output stage.

---

## 5.4 TextBlock

~~~text
TextBlock
├── text
├── bold = FALSE
├── italic = FALSE
└── color = ""
~~~

A `TextBlock` is used when prose carries formatting information.

| Field | Meaning |
|---|---|
| `text` | Text content |
| `bold` | Bold flag |
| `italic` | Italic flag |
| `color` | Optional CSS color |

For example:

~~~text
@text{
    bold = true,
    italic = true,
    text = "Important result."
}
~~~

can become:

~~~text
TextBlock
    text   = "Important result."
    bold   = TRUE
    italic = TRUE
    color  = ""
~~~

The reason this is not represented as just a string is that the formatting must survive parsing.

---

## 5.5 Label

~~~text
Label
└── name
~~~

A `Label` gives a piece of content a named target.

Example:

~~~text
Label
    name = "gauss-law"
~~~

It is used as the target of a cross-reference.

---

## 5.6 Reference

~~~text
Reference
├── target
└── text = ""
~~~

A `Reference` represents a cross-reference.

| Field | Meaning |
|---|---|
| `target` | Label or target being referenced |
| `text` | Visible link text |

Conceptually:

~~~text
Reference(
    target="gauss-law",
    text="Gauss's law"
)
~~~

The parser represents the relationship, while the renderer turns it into a link.

---

## 5.7 ListItem

~~~text
ListItem
├── content = EMPTY LIST
└── title = ""
~~~

A `ListItem` represents one item in a list.

The important part is that its `content` is a list of `ContentItem` objects rather than a single string.

Therefore a list item can contain structured content such as:

~~~text
ListItem
│
├── TextBlock
├── MathBlock
├── Image
└── nested ListBlock
~~~

This is what allows nested and rich list content.

---

## 5.8 ListBlock

~~~text
ListBlock
├── ordered
├── items = EMPTY LIST
└── color = "black"
~~~

A `ListBlock` represents an ordered or unordered list.

| Field | Meaning |
|---|---|
| `ordered` | TRUE for an ordered list, FALSE for an unordered list |
| `items` | List of `ListItem` objects |
| `color` | Marker color |

Conceptually:

~~~text
ListBlock
│
├── ordered = TRUE
├── item 1
│    └── content
├── item 2
│    └── content
└── item 3
     └── content
~~~

---

## 5.9 Environment

~~~text
Environment
├── kind
├── title = ""
├── label = ""
└── content = EMPTY LIST
~~~

An `Environment` represents a semantic boxed construction such as a theorem or definition.

| Field | Meaning |
|---|---|
| `kind` | Type of environment |
| `title` | Optional displayed title |
| `label` | Optional reference label |
| `content` | Content inside the environment |

Conceptually:

~~~text
Environment
    kind  = "theorem"
    title = "Intermediate Value Theorem"
    label = "ivt"
    content = [...]
~~~

The key idea is **semantic structure**. A theorem is represented as a theorem-like environment rather than as a random block of styled text.

---

# 6. ContentItem

One of the most important definitions in `ast.py` is `ContentItem`.

In raw logic:

~~~text
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
~~~

In Python it is represented by a union type:

~~~python
ContentItem = Union[
    str,
    Image,
    MathBlock,
    TextBlock,
    Label,
    Reference,
    ListBlock,
    Environment,
]
~~~

This means the content of a section can be **heterogeneous**.

For example:

~~~text
Section
│
├── "Some introductory text."
├── MathBlock
├── Image
├── Environment
├── ListBlock
└── Reference
~~~

The renderer can inspect which concrete object it received and apply the correct rendering operation.

---

# 7. Subsection

~~~text
Subsection
├── title
├── content = EMPTY LIST
├── slug = NONE
└── label = ""
~~~

A `Subsection` is nested inside a `Section`.

Its `content` again consists of `ContentItem` objects.

The `slug` is a URL-friendly identifier.

The `label` is a semantic reference label.

---

# 8. Section

~~~text
Section
├── title
├── color = "#111111"
├── content = EMPTY LIST
├── subsections = EMPTY LIST
├── slug = NONE
└── label = ""
~~~

A `Section` contains:

~~~text
Section
│
├── direct content
│
└── subsections
       ├── Subsection
       ├── Subsection
       └── ...
~~~

This mirrors the logical structure of a Mark Two article.

---

# 9. RelatedLink

~~~text
RelatedLink
├── name
└── href
~~~

A `RelatedLink` stores a related navigation link.

Example:

~~~python
RelatedLink(
    name="Linear Algebra",
    href="/mathematics/linear-algebra/"
)
~~~

---

# 10. Document

`Document` is the root node of the AST.

~~~text
Document
├── document_title = ""
├── banner = ""
├── banner_color = ""
├── article_title = ""
├── buttons = []
├── sections = []
└── related_links = []
~~~

Everything in the parsed article is reachable from this object.

Conceptually:

~~~text
Document
│
├── metadata
│
├── navigation
│    └── Button[]
│
├── article structure
│    └── Section[]
│          ├── ContentItem[]
│          └── Subsection[]
│                └── ContentItem[]
│
└── RelatedLink[]
~~~

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

---

# 12. How objects flow through Mark Two

The parser reads the source and constructs these objects.

Conceptually:

~~~text
READ .mt FILE
      │
      ▼
INSPECT SOURCE
      │
      ▼
PARSER
      │
      ├── read document metadata
      ├── detect sections
      ├── detect subsections
      ├── parse text
      ├── parse mathematics
      ├── parse images
      ├── parse lists
      ├── parse labels
      ├── parse references
      └── parse environments
      │
      ▼
CREATE AST OBJECTS
      │
      ▼
Document
      │
      ├── Section
      │     ├── ContentItem
      │     └── Subsection
      │
      ├── Button
      │
      └── RelatedLink
      │
      ▼
RENDERER
      │
      ├── render document
      ├── render sections
      ├── render text
      ├── render mathematics
      ├── render images
      ├── render lists
      ├── render environments
      └── render references
      │
      ▼
HTML
~~~

The parser therefore answers the syntactic question, while the AST stores the result in a structured form.

---

# 13. Why use an AST?

Without an AST, the renderer would have to understand the raw Mark Two language directly:

~~~text
.mt source
   │
   ▼
renderer
   │
   ├── understand @section
   ├── understand @text
   ├── understand @image
   ├── understand @enumerate
   ├── understand @theorem
   └── generate HTML
~~~

With an AST:

~~~text
.mt source
   │
   ▼
parser
   │
   ▼
semantic structure
   │
   ▼
renderer
   │
   ▼
HTML
~~~

This gives a clean separation of responsibilities.

### Parser

> What did the author write?

### AST

> What is the structured meaning of it?

### Renderer

> How should that meaning be represented in HTML?

This separation makes each stage easier to reason about and change independently.

---

# 14. AST as an intermediate representation

The AST can be viewed as an **intermediate representation** between two languages.

Input language:

~~~text
@documenttitle{Mathematics}
@section{Real Analysis}
@text{A statement.}
~~~

Intermediate representation:

~~~text
Document
│
├── document_title = "Mathematics"
│
└── Section
      ├── title = "Real Analysis"
      └── TextBlock
            └── text = "A statement."
~~~

Output language:

~~~html
<h1>Real Analysis</h1>
<p>A statement.</p>
~~~

So the transformation is:

~~~text
Mark Two
   ↓
  AST
   ↓
 HTML
~~~

The renderer no longer needs to rediscover the meaning of the original Mark Two syntax.

---

# 15. Complete simplified example

Consider:

~~~text
@documenttitle{Physics}

@section{Classical Mechanics}

@text{Newton's second law is}

\[
F = ma
\]

@theorem{Newton's Second Law}
~~~

The parser can conceptually produce:

~~~text
Document
│
├── document_title
│      └── "Physics"
│
└── Section
      │
      ├── title
      │      └── "Classical Mechanics"
      │
      ├── TextBlock
      │      └── "Newton's second law is"
      │
      ├── MathBlock
      │      └── "F = ma"
      │
      └── Environment
             ├── kind
             │    └── "theorem"
             └── title
                  └── "Newton's Second Law"
~~~

The renderer can then traverse this structure directly.

---

# 16. The mental model

The most useful way to think about `ast.py` is:

~~~text
AST = the shape of the document in memory
~~~

Or, more explicitly:

~~~text
SOURCE
  │
  ▼
PARSER
  │
  ▼
AST
  │
  ▼
RENDERER
  │
  ▼
OUTPUT
~~~

`ast.py` therefore is not the parser and not the renderer.

It defines the **structured memory of what the parser understood**.
