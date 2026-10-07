# Mark Two

Mark Two is a lightweight mathematical document language that compiles `.mt` source files into clean HTML articles.

It is designed for mathematical notes, physics articles, proofs, and technical writing where normal prose, TeX mathematics, semantic environments, figures, references, and document metadata should live together in a readable source file.

The central idea is deliberately simple:

> **Write the mathematics and prose naturally. Use Mark Two syntax only where structure or formatting is needed.**

## Installation

From the root of the Mark Two repository:

```bash
python3 -m pip install -e .
```

This installs the `mark-two` command in editable mode, so source-code changes are picked up immediately.

Mark Two requires Python 3.10 or newer.

## Usage

A document can live anywhere inside a project:

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

By default, the compiler writes the generated article beside the source file:

```text
completeness/
├── completeness.mt
└── index.html
```

A custom output path can be selected with:

```bash
mark-two completeness.mt --output build/article.html
```

A custom article template can be supplied with:

```bash
mark-two completeness.mt --template path/to/index.html
```

Mark Two can also be invoked as a Python module:

```bash
python3 -m mark_two completeness.mt
```

### Site commands

Mark Two also provides commands for site-level configuration and generated pages.

Initialize a site:

```bash
mark-two init
```

Read or change configuration:

```bash
mark-two config get
mark-two config get author
mark-two config set title "Notes on Mathematics and Physics"
```

Build the homepage and archive:

```bash
mark-two build homepage
mark-two build archive
```

The site configuration is stored in `site.json`.

## Article metadata

An article begins with document-level directives.

A typical header looks like:

```text
@documenttitle{Physics, banner = images/banner.jpg}
@folder{Electromagnetism}
@author{Vivek Kalita}
@date{2 October 2026}
@title{Quantizing the Electromagnetic Field}
@description{A semi-classical method of quantising the electromagnetic field.}
@tags{Electromagnetism, Quantum Field Theory, Classical Field Theory}
```

The available document directives are:

| Directive | Purpose | Example |
| --- | --- | --- |
| `@documenttitle` | Sets the document subject/classification and can specify a banner image or color. | `@documenttitle{Physics, banner = images/banner.jpg}` |
| `@folder` | Sets the article's folder/category metadata. | `@folder{Electromagnetism}` |
| `@author` | Sets the author. | `@author{Vivek Kalita}` |
| `@date` | Sets the article date. | `@date{2 October 2026}` |
| `@title` | Sets the article title. | `@title{The Electromagnetic Lagrangian}` |
| `@description` | Sets the short article description used by the site catalog and homepage. | `@description{A derivation of the field equations.}` |
| `@tags` | Adds comma-separated article tags. | `@tags{Electromagnetism, Classical Field Theory}` |
| `@button` | Adds a navigation button to the article header. | `@button{GitHub, href = https://github.com/VivekH90/mark-two}` |
| `@relatedlinks` | Adds a related link to the article sidebar. | `@relatedlinks{Lagrangian Mechanics, href = /physics/classical-mechanics/lagrangian}` |
| `@relatedlink` | Alias for `@relatedlinks`. | `@relatedlink{Python, href = https://www.python.org}` |

Arguments may span multiple lines. Mark Two's parser handles nested braces, brackets, parentheses, quoted strings, commas, and escaped characters while determining where a directive ends.

## Writing prose

Normal prose is written directly.

There is **no `@text` directive in the canonical language**.

For example:

```text
The electromagnetic field is a field defined throughout spacetime. In
classical physics it is represented by the electric and magnetic fields.
```

Blank lines separate paragraphs.

This is intentional: an article source should read like an article, not like a sequence of HTML commands.

## Mathematics

Mark Two uses TeX mathematics directly.

### Inline mathematics

Use `\\(...\\)` for inline mathematics:

```text
The wave has angular frequency \(\omega=ck\).
```

### Display mathematics

Use `\\[ ... \\]` for display mathematics:

```text
The dispersion relation is

\[
\omega=ck.
\]
```

Display mathematics is stored as a mathematical block and passed through MathJax in the generated page.

## Sections and subsections

Sections and subsections are structural directives:

```text
@section{The Classical Electromagnetic Field, label = classical-electromagnetic-field}

Some introductory prose.

@subsection{Free Electromagnetic Field, label = free-electromagnetic-field}

More prose.
```

Sections and subsections create the numbered headings used by the generated Contents navigation.

Labels are optional, but labels are useful when a section or subsection needs to be referenced later.

## Semantic environments

Mathematical statements use enclosed semantic environments.

The canonical form is:

```text
@begin(theorem = Fundamental Theorem, label = fundamental-theorem)

The statement of the theorem.

@end(theorem)
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

A proof normally has no title:

```text
@begin(proof)

Proof of the result.

@end(proof)
```

The title and label are optional for theorem-like environments where appropriate. Proofs are the special case and normally omit both.

### Numbering

The renderer numbers theorem-like environments within each section.

For example:

```text
Section 1
    Theorem 1.1
    Proposition 1.2

Section 2
    Definition 2.1
```

Proof environments do not consume a theorem number.

### Colourbox

For short pieces of emphasis that do not need a semantic title, use the titleless `colourbox` environment:

```text
@begin(colourbox)

The key idea is that a box can emphasize a paragraph without
turning it into a theorem-like statement.

@end(colourbox)
```

`colourbox` is deliberately unnumbered and has no generated title. It is a visual emphasis surface rather than a semantic mathematical environment. It may contain normal Mark Two content, including prose, mathematics, lists, images, and nested environments.

An optional label may be supplied when a stable HTML anchor is useful:

```text
@begin(colourbox, label = important-note)

This is an emphasized note.

@end(colourbox)
```

The generated box uses rounded corners, a contrasting border, and separate light/dark theme colors.

### Interactive animations

Use the titleless `animation` environment when an article needs an interactive figure, animation, simulation, or other browser-based visualization.

The contents of the environment are treated as **raw trusted web content**. Mark Two does not parse or escape the body, so HTML, CSS, and JavaScript can be written directly. This is intentional: CSS constructs such as `@media` and `@keyframes`, JavaScript braces, and arbitrary HTML should pass through unchanged.

```text
@begin(animation)

<canvas id="oscillator" width="700" height="360"></canvas>

<style>
#oscillator {
    width: 100%;
    height: 360px;
}
</style>

<script>
const canvas = document.getElementById("oscillator");
const ctx = canvas.getContext("2d");

function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    // draw the interactive visualization here
    requestAnimationFrame(draw);
}

draw();
</script>

@end(animation)
```

Mark Two supplies the outer `.mt-animation` shell. It constrains the component to the article width, hides accidental overflow, applies the site's typography and theme colors by inheritance, and keeps the animation visually separate from surrounding prose.

An animation may optionally have a label:

```text
@begin(animation, label = harmonic-oscillator)
...
@end(animation)
```

Animation bodies are intentionally opaque to the Mark Two parser. The closing delimiter is a line containing `@end(animation)`, so that delimiter should not be placed verbatim on its own line inside the embedded code.

Because animation bodies can execute arbitrary JavaScript, this feature is intended for trusted `.mt` authors rather than untrusted user-submitted documents.

### Nested environments

Environments can contain other environments:

```text
@begin(theorem = A Result, label = a-result)

Statement of the result.

@begin(proof)

Proof of the result.

@end(proof)

@end(theorem)
```

This keeps the theorem and its proof structurally connected in the source.

Structural headings such as `@section` and `@subsection` should remain outside open semantic environments.

## Lists

Ordered and unordered lists use enclosed environments.

### Ordered lists

```text
@begin(enumerate)

@item{First item.}
@item{Second item.}
@item{Third item.}

@end(enumerate)
```

### Unordered lists

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

List items can contain ordinary Mark Two content, including mathematics, inline formatting, nested lists, images, and semantic environments.

Nested ordered lists are rendered with alphabetic markers:

```text
@begin(enumerate)

@item{
First main point.

@begin(enumerate)
@item{First sub-point.}
@item{Second sub-point.}
@end(enumerate)
}

@item{Second main point.}

@end(enumerate)
```

which renders conceptually as:

```text
1. First main point.
   a. First sub-point.
   b. Second sub-point.
2. Second main point.
```

## Inline formatting

Inline formatting is used directly inside ordinary prose and other rendered text.

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

CSS colors may also be given explicitly:

```text
This is @color{#315a9b, highlighted}.
```

The key-value form is also supported:

```text
@color{color = #315a9b, text = "blue text"}
```

### Nesting

Inline commands can be nested:

```text
This is @bold{very @italic{important}}.

This is @color{red, @bold{extremely important}}.
```

The currently supported inline commands are:

```text
@bold{...}
@italic{...}
@color{...}
@ref{...}
```

These are **inline formatting/reference commands**, not semantic environments.

## References and labels

Sections, subsections, semantic environments, and explicit label nodes can be given labels.

For example:

```text
@section{Main Result, label = main-result}

@begin(theorem = Fundamental Theorem, label = fundamental-theorem)

The statement.

@end(theorem)
```

Reference a label inline with:

```text
By @ref{fundamental-theorem}, the desired result follows.
```

Custom reference text is supported:

```text
By @ref{fundamental-theorem, text = "the theorem"}, the result follows.
```

A standalone label can also be inserted:

```text
@label{important-point}
```

References may also target an HTML page or fragment:

```text
@ref{analysis.html#fundamental-theorem}
```

Mark Two resolves known local labels to their generated anchors. Unknown references are left as unresolved links rather than silently discarded.

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

| Property | Purpose |
| --- | --- |
| `src` | Local path or remote image URL. |
| `alt` | Alternative text for the generated image. |
| `caption` | Visible figure caption. |
| `label` | HTML anchor/id for the figure. |
| `width` | CSS width such as `60%`, `300px`, or `20rem`. |
| `height` | CSS height such as `240px`; `auto` leaves the height automatic. |

When a caption is supplied, Mark Two automatically adds the figure number:

```text
Figure 1: The construction used in the proof.
```

Figure numbering follows document order. A multi-image group counts as one figure.

### Multiple images

Several images can belong to a single figure:

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

The caption belongs to the complete multi-image figure, and the label of the first image is used as the figure anchor when a label is supplied.

## A complete article

A small article can therefore look like this:

```text
@documenttitle{Mathematics}
@folder{Real Analysis}
@author{Vivek Kalita}
@date{6 October 2026}
@title{Density of Rational Numbers}
@description{A proof that the rational numbers are dense in the real numbers.}
@tags{Real Analysis, Rational Numbers, Archimedean Property}

@section{Density of Rational Numbers, label = density-of-rational-numbers}

The rational numbers \(\mathbb Q\) are everywhere inside the real numbers. No matter how small an interval we take, as long as it has positive length, there is always a rational number inside it.

The proof is a direct application of the Archimedean property.

@begin(theorem = Density of the Rational Numbers, label = density-q-in-r)

For every \(a,b\in\mathbb R\) with

\[
a<b,
\]

there exists \(r\in\mathbb Q\) such that

\[
a<r<b.
\]

@end(theorem)

@begin(proof)

Let \(a<b\). Then

\[
b-a>0.
\]

By the Archimedean property, choose \(n\in\mathbb N\) such that

\[
n>\frac{1}{b-a}.
\]

Hence

\[
n(b-a)>1,
\]

so

\[
na+1<nb.
\]

Choose the least \(m\in\mathbb N\) satisfying

\[
m>na.
\]

By minimality,

\[
m\le na+1.
\]

Therefore,

\[
na<m\le na+1<nb.
\]

Dividing by \(n>0\),

\[
a<\frac{m}{n}<b.
\]

Since \(m/n\in\mathbb Q\), the required rational number has been found.

@end(proof)
```

The important stylistic rule is that the source should remain readable as mathematical writing. Mark Two supplies structure around the mathematics rather than forcing every sentence into markup.

## Article catalog

Each compilation updates a generated `articles.json` catalog.

The catalog is intended for the homepage, archive, tag filtering, and search. It is generated from the metadata already present in the `.mt` source, so the source document remains the source of truth.

A record contains fields such as:

```json
{
  "id": "physics/electromagnetism/field_equations",
  "title": "Field Equations",
  "description": "A derivation of the electromagnetic field equations from the Lagrangian formulation.",
  "subject": "Physics",
  "folder": "Electromagnetism",
  "author": "Vivek Kalita",
  "date": "27 September 2026",
  "tags": ["Electromagnetism", "Classical Field Theory"],
  "url": "/physics/electromagnetism/field_equations/",
  "source": "physics/electromagnetism/field_equations.mt",
  "sections": ["Maxwell's Equations"]
}
```

By default, Mark Two places the catalog at `articles.json` in the nearest project root, detected from `.git` or `pyproject.toml`.

A different catalog path can be selected with:

```bash
mark-two completeness.mt --index path/to/articles.json
```

When an article is compiled, only its logical record is replaced. Existing records keep their order and contents, while a new article is appended. If the record has not changed, the catalog is left untouched.

The catalog is written atomically so an interrupted compile cannot leave a half-written JSON file.

The build model is therefore:

```text
.mt source
   |
   +--> HTML article
   |
   +--> articles.json metadata index
```

## Generated site

Mark Two can build a small static site around the generated articles.

The built-in templates provide:

- a restrained site header
- article metadata
- Home, GitHub, and theme controls
- responsive article styling
- a Contents navigation generated from real section/subsection headings
- related links
- MathJax mathematics
- responsive image and list styling
- homepage search and tag filtering
- an archive page with search and tag filtering
- light and dark themes

The article compiler inlines the local stylesheet and JavaScript into the generated article. External assets, such as the MathJax CDN script, remain external.

The result is a self-contained article HTML file, which is convenient for static hosting and platforms with a page/file limit.

## Site configuration

A Mark Two site uses `site.json` for site-wide settings.

The default configuration contains fields for:

```text
author
bio
title
description
email
instagram
github
about
archive
featured
copyright
```

Initialize it with:

```bash
mark-two init
```

Set a value with:

```bash
mark-two config set github https://github.com/VivekH90/blog
```

Read values with:

```bash
mark-two config get
mark-two config get github
```

The homepage reads `articles.json` and `site.json` and renders featured, recent, topic-filtered, and archived article entries.

## VS Code extension

The optional extension lives under `vscode-mark-two/`.

Current extension version: **0.4.0**.

It provides:

- automatic language detection for `.mt` files
- syntax highlighting for directives, environment delimiters, arguments, strings, URLs, numbers, comments, and TeX mathematics
- completion after `@`
- environment-name completion inside `@begin(...)` and `@end(...)`
- snippets for document directives
- snippets for semantic environments
- snippets for lists, images, references, related links, and inline formatting
- automatic bracket and parenthesis closing
- indentation based on `@begin(...)` and `@end(...)`

The environment snippets generate the canonical syntax. For example:

```text
@begin(theorem = Theorem Title, label = theorem-label)

@end(theorem)
```

The extension does not provide `@text` because ordinary prose is written directly.

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
├── web/                 # HTML templates and frontend assets
├── build/               # Generated example HTML bundle
├── vscode-mark-two/     # VS Code language support
├── docs/                # Supporting documentation
└── pyproject.toml       # Python package and CLI configuration
```

## Canonical language rules

The current language follows a small set of principles:

1. **Write normal prose normally.**
2. **Use directives for document structure and metadata.**
3. **Use `@begin(...)` and `@end(...)` for semantic environments.**
4. **Use `@bold`, `@italic`, `@color`, and `@ref` inline when formatting or referencing prose.**
5. **Use TeX directly for mathematics.**

The canonical theorem form is:

```text
@begin(theorem = A Theorem, label = a-theorem)

Normal prose goes here.

@end(theorem)
```

The older standalone forms such as:

```text
@theorem{...}
@definition{...}
@axiom{...}
@proof{...}
```

are not part of the canonical language.

Likewise, `@text` is not part of the canonical language.

The parser retains an older `@begin(kind){...}` compatibility form, but new documents should use the canonical header form:

```text
@begin(theorem = A Theorem, label = a-theorem)
...
@end(theorem)
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

## Design philosophy

Mark Two is deliberately smaller than a full markup language.

The source should remain comfortable to read while writing mathematics. A reader looking at a `.mt` file should be able to follow the mathematical argument without mentally reconstructing a forest of HTML tags.

The language therefore separates three layers:

```text
Mathematical prose
       ↓
Mark Two structure
       ↓
HTML presentation
```

The source expresses the mathematical structure. The renderer decides how that structure should look on the page.

That separation is what allows a document such as a proof, lecture note, or physics derivation to be written once and presented consistently across the site.


## Document types

Every Mark Two document can declare whether it is an **article** or **notes** document:

```text
@doctype(article)
```

or:

```text
@doctype(notes)
```

The document type is metadata, not a normal user tag. It is stored in the generated `articles.json` catalog as `doctype`, and the homepage and archive use it to let readers browse **All**, **Articles**, or **Notes** independently.

Documents that do not declare a type remain valid and are treated as `notes`. Use `@doctype(article)` explicitly when a document is intended to be an article.

Only `article` and `notes` are currently accepted:

```text
@doctype(article)
@doctype(notes)
```
