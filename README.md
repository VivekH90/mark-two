# Mark Two

Mark Two is a lightweight mathematical document language that compiles `.mt` source files into clean HTML articles.

It is designed for notes, mathematical writing, physics articles, and other documents where normal prose, TeX mathematics, semantic environments, figures, references, and small pieces of metadata should live together in a readable source file.

## Installation

From the root of the Mark Two repository:

```bash
python3 -m pip install -e .
```

This installs the `mark-two` command in editable mode, so source-code changes are picked up immediately.

Mark Two requires Python 3.10 or newer.

## Usage

A document can be stored anywhere in a project:

```text
mathematics/
└── real-analysis/
    └── completeness/
        └── completeness.mt
```

Compile it with:

```bash
mark-two mathematics/real-analysis/completeness/completeness.mt
```

By default, the compiler writes a complete web bundle beside the source file:

```text
completeness/
├── completeness.mt
├── index.html
├── style.css
└── script.js
```

A custom output path can be selected with:

```bash
mark-two completeness.mt --output build/article.html
```

A custom HTML template can be selected with:

```bash
mark-two completeness.mt --template path/to/index.html
```

Mark Two can also be invoked as a Python module:

```bash
python3 -m mark_two completeness.mt
```

## Updating Mark Two

When Mark Two is installed with `pip install -e`, normal source changes do not require reinstallation.

For a normal clone:

```bash
cd mark-two
git pull
```

When Mark Two is used as a Git submodule:

```bash
git submodule update --remote resources/templates/mark-two
```

## Mark Two Syntax

Mark Two has two kinds of syntax:

- **directives**, such as `@section{...}` and `@image{...}`
- **enclosed environments**, written with `@begin(...)` and `@end(...)`

Normal prose is written directly. There is no `@text` command.

### Document directives

Common document-level directives are:

| Directive | Purpose | Example |
| --- | --- | --- |
| `@documenttitle` | Sets the document classification tag and can set the banner image/color. | `@documenttitle{Physics, banner = images/banner.jpg}` |
| `@folder` | Sets the folder/category text used by the generated page metadata. | `@folder{Electromagnetism}` |
| `@author` | Sets the author name. | `@author{Vivek}` |
| `@date` | Sets the document date. | `@date{26 September 2026}` |
| `@title` | Sets the article title. | `@title{Electromagnetic Lagrangian}` |
| `@tags` | Adds comma-separated article tags. | `@tags{Electromagnetism, Classical Field Theory}` |
| `@button` | Adds a navigation button. | `@button{GitHub, href = https://github.com/VivekH90/blog}` |
| `@gallery` | Adds a remote image gallery. | `@gallery{source = NASA, query = black holes, count = 7}` |
| `@relatedlinks` | Adds a related link to the page sidebar. | `@relatedlinks{Python, href = https://www.python.org}` |
| `@relatedlink` | Alias for `@relatedlinks`. | `@relatedlink{Python, href = https://www.python.org}` |

Directives can span multiple lines. Braces, parentheses, brackets, commas, quotes, and escaped characters are handled by the parser when determining directive boundaries.

### Sections and subsections

Sections remain ordinary directives:

```text
@section{Lagrange's equation for a single variable, label = single-variable}

Ordinary prose goes directly here.
```

Subsections use the same form:

```text
@subsection{The 4-vector generalization, label = four-vector-generalization}

More prose.
```

Sections and subsections create the numbered headings used by the generated Contents navigation.

## Enclosed environments

Semantic environments use an explicit opening and closing pair.

The canonical form is:

```text
@begin(theorem = Fundamental Theorem, label = fundamental-theorem)

The statement of the theorem.

@end(theorem)
```

A proof has no title:

```text
@begin(proof)

The proof goes here.

@end(proof)
```

The supported semantic environments are:

```text
theorem
lemma
definition
corollary
axiom
proposition
remark
example
conjecture
notation
warning
proof
```

The title and label are optional only where the environment permits them. Proofs normally omit both:

```text
@begin(proof)
...
@end(proof)
```

### Nested environments

Environments can contain other environments:

```text
@begin(theorem = A Result, label = a-result)

Statement of the theorem.

@begin(proof)

Proof of the result.

@end(proof)

@end(theorem)
```

This is useful for keeping a theorem and its proof structurally connected in the source.

### Lists

Ordered and unordered lists can also use enclosed environments:

```text
@begin(enumerate)

@item{First item.}
@item{Second item.}

@end(enumerate)
```

and:

```text
@begin(itemize)

@item{First item.}
@item{Second item.}

@end(itemize)
```

List markers can be colored:

```text
@begin(enumerate, color = green)

@item{First item.}
@item{Second item.}

@end(enumerate)
```

List items can contain normal Mark Two content, including nested lists and semantic environments.

## Inline formatting

Inline formatting works directly inside ordinary prose and other rendered text.

### Bold

```text
This is @bold{important}.
```

### Italic

```text
This is @italic{emphasized}.
```

### Color

```text
This is @color{red, highlighted}.
```

CSS colors may also be supplied explicitly:

```text
This is @color{#315a9b, highlighted}.
```

Inline formatting can be nested:

```text
This is @bold{very @italic{important}}.

This is @color{red, @bold{extremely important}}.
```

## Images

Article images are inserted with `@image`.

A basic image:

```text
@image{
    src = figure.png,
    alt = A diagram of the construction,
    caption = The construction used in the proof,
    label = construction,
    width = 65%
}
```

`src` may be a local path or a remote image URL:

```text
@image{
    src = https://example.com/figure.png,
    alt = Example remote figure,
    caption = An externally hosted figure.
}
```

### Image properties

An image supports:

| Property | Purpose |
| --- | --- |
| `src` | Local path or remote image URL. |
| `alt` | Alternative text placed in the generated `<img>` element. |
| `caption` | Visible figure caption. |
| `label` | HTML anchor/id for the figure. |
| `width` | CSS width such as `60%`, `300px`, or `20rem`. |
| `height` | CSS height such as `240px`; `auto` leaves the height automatic. |

When a caption is present, Mark Two automatically adds the figure number:

```text
caption = The construction used in the proof.
```

becomes a caption in the form:

```text
Figure 1: The construction used in the proof.
```

Figure numbering follows document order. A multi-image group counts as one figure.

### Multiple images

Multiple images can share one figure:

```text
@image{
    image(1) = first.png,
    image(2) = second.png,
    image(3) = third.png,
    caption = Three stages of the construction.
}
```

Individual widths and heights can be supplied with indexed properties:

```text
@image{
    image(1) = wide.png,
    image(2) = middle.png,
    image(3) = narrow.png,
    width(1) = 50%,
    width(2) = 25%,
    height(1) = 240px,
    height(2) = 180px,
    caption = A custom-sized figure group.
}
```

An image without an explicit width receives the remaining space in the row.

The caption belongs to the complete multi-image figure. The label of the first image is used as the figure anchor when a label is supplied.

## References and labels

A section, subsection, or semantic environment can have a label:

```text
@section{Main Result, label = main-result}

@begin(theorem = Fundamental Theorem, label = fundamental-theorem)

The statement.

@end(theorem)
```

Reference it inline with:

```text
By @ref{fundamental-theorem}, the desired result follows.
```

Custom reference text is supported:

```text
By @ref{fundamental-theorem, text = "the theorem"}, the result follows.
```

A reference can also target a page/HTML URL:

```text
@ref{analysis.html#fundamental-theorem}
```

## Remote image galleries

The `@gallery` directive can build a document-level remote image gallery at compile time.

NASA is currently supported:

```text
@gallery{
    source = NASA,
    query = black holes,
    count = 7
}
```

An optional deterministic seed can be supplied:

```text
@gallery{
    source = NASA,
    query = gravitational waves,
    count = 6,
    seed = 42
}
```

The compiler resolves image metadata and keeps the resulting image URLs in the generated HTML. Image files are not copied into the repository.

## Generated web page

The built-in template provides:

- a rounded top navigation bar
- a remote image gallery and lightbox when `@gallery` is used
- a breadcrumb/metabar
- Home, GitHub, and light/dark theme controls
- a main article area
- a right-hand Contents panel
- a right-hand Related panel
- a mobile Contents & related panel
- responsive article, image, list, and environment styling
- MathJax for TeX mathematics

The Contents navigation is generated from the actual section and subsection headings in the rendered article and highlights the section currently in view.

## VS Code extension

The optional extension lives under `vscode-mark-two/`.

Current extension version: **0.4.0**.

It provides:

- automatic language detection for `.mt` files
- syntax highlighting for directives, environment delimiters, arguments, strings, URLs, numbers, comments, and TeX mathematics
- completion after `@`
- environment-name completion inside `@begin(...)` and `@end(...)`
- snippets for document directives
- snippets for all semantic environments
- snippets for lists, images, galleries, references, related links, and inline formatting
- automatic bracket/parenthesis closing
- indentation based on `@begin(...)` and `@end(...)`

The environment snippets generate the canonical syntax. For example, the theorem snippet produces:

```text
@begin(theorem = Theorem Title, label = theorem-label)

@end(theorem)
```

The extension does not provide `@text` as a directive because ordinary prose is written directly.

### Installing the extension

From the repository root:

```bash
cd vscode-mark-two
npx @vscode/vsce package
code --install-extension ./mark-two-language-0.4.0.vsix
```

After installation, reload VS Code and open a `.mt` file. The language indicator should show **Mark Two**.

For extension development, open the repository in VS Code and launch the Extension Development Host with `F5`.

## Project layout

```text
mark-two/
├── src/                 # Mark Two Python package source
├── test/                # Tests and example source documents
├── web/                 # HTML template and frontend assets
├── build/               # Generated example HTML bundle
├── vscode-mark-two/     # VS Code language support
├── docs/                # Supporting documentation
└── pyproject.toml       # Python package and CLI configuration
```

## Current language rules

The current canonical language follows a simple rule:

**Write normal prose normally. Use directives for document structure. Use `@begin(...)` and `@end(...)` for semantic environments.**

The old standalone environment commands such as:

```text
@theorem{...}
@definition{...}
@axiom{...}
@proof{...}
```

are no longer part of the canonical language.

Likewise, `@text` is no longer used.

Use:

```text
@begin(theorem = A Theorem, label = a-theorem)

Normal prose goes here.

@end(theorem)
```

instead.
