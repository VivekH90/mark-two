<div align="center">

# Mark Two

A lightweight mathematical document language that compiles `.mt` source files into clean HTML articles.

[![HTML](https://img.shields.io/badge/HTML-MARK%20TWO-176c5b?style=for-the-badge)](https://github.com/VivekH90/mark-two)
[![MathJax](https://img.shields.io/badge/MATHJAX-SUPPORTED-76547e?style=for-the-badge)](https://www.mathjax.org/)
[![Commits](https://img.shields.io/github/commit-activity/t/VivekH90/mark-two?style=for-the-badge&label=COMMITS)](https://github.com/VivekH90/mark-two/commits/master)
[![Last Commit](https://img.shields.io/github/last-commit/VivekH90/mark-two?style=for-the-badge&label=LAST%20COMMIT)](https://github.com/VivekH90/mark-two/commits/master)
[![License](https://img.shields.io/badge/LICENSE-NOT%20SPECIFIED-999999?style=for-the-badge)](https://github.com/VivekH90/mark-two)

</div>

## Installation

Mark Two can be installed as an editable local Python package. This is useful when Mark Two lives inside another project, such as a blog repository.

From the parent project:

```bash
python3 -m pip install -e resources/mark-two
```

After this one-time setup, the `mark-two` command can be used from any directory.

## Usage

Create a `.mt` file anywhere in your project:

```text
mathematics/
└── real-analysis/
    └── completeness/
        └── completeness.mt
```

Then compile it from that directory:

```bash
cd mathematics/real-analysis/completeness
mark-two completeness.mt
```

By default, Mark Two creates a complete web bundle beside the source file:

```text
completeness/
├── completeness.mt
├── index.html
├── style.css
└── script.js
```

You can also give the source file as a path from anywhere in the project:

```bash
mark-two mathematics/real-analysis/completeness/completeness.mt
```

A custom output path can be selected with:

```bash
mark-two completeness.mt --output build/article.html
```

A custom HTML template can be selected with:

```bash
mark-two completeness.mt --template path/to/index.html
```

For compatibility, Mark Two can also be run as a Python module:

```bash
python3 -m mark_two completeness.mt
```

## Updating Mark Two

If Mark Two is cloned into another repository, update it with Git instead of downloading it again:

```bash
cd resources/mark-two
git pull
```

Because Mark Two was installed with `pip install -e`, the command uses the updated source immediately. There is no need to reinstall the package after normal source-code updates.

## Mark Two Syntax

Mark Two uses `@` directives for document structure and semantics.

### Multiline Directives

**Every Mark Two directive can span multiple lines.** The parser matches the opening `{` with its corresponding closing `}`, while respecting nested braces and quoted strings. This means formatting a directive across several lines is purely a matter of readability and does not change its meaning.

For example, an ordered list can be written naturally:

```text
@enumerate{
    color = green,
    @item{
        First item in the list.
    },
    @item{
        Second item in the list.
    }
}
```

The same applies to images:

```text
@image{
    image(1) = first.png,
    image(2) = second.png,
    width(1) = 50%,
    width(2) = 35%,
    caption = Two related figures.
}
```

And to document metadata:

```text
@documenttitle{
    My Notes,
    banner = images/banner.jpg,
    color = #ffcc00
}
```

The single-line form remains valid too.

| Command | Purpose | Example |
| --- | --- | --- |
| `@documenttitle` | Sets the document/site title and optional banner. Supports `color` for the banner title text. | `@documenttitle{My Notes, banner = images/banner.jpg, color = #ffcc00}` |
| `@button` | Adds a navigation button. | `@button{Home, href = /, color = black}` |
| `@title` | Sets the article title. | `@title{Introduction to Analysis}` |
| `@section` | Creates a numbered section. Supports `color` and `label`. | `@section{Limits, color = #315a9b, label = limits}` |
| `@subsection` | Creates a numbered subsection. Supports `label`. | `@subsection{One-sided limits, label = one-sided}` |
| `@image` | Inserts a single image or a multi-image row. Single images support `image`/`src`, `width`, `height`, `alt`, `caption`, and `label`. Multiple images use `image(1)`, `image(2)`, ... and support independent `width(n)` and `height(n)` values. Unspecified widths share the remaining row space. | `@image{image(1) = first.png, image(2) = second.png, width(1) = 55%, width(2) = 35%, caption = A comparison.}` |
| `@enumerate` | Creates an ordered list. | `@enumerate{color = green, @item{First}, @item{Second}}` |
| `@itemize` | Creates an unordered list. | `@itemize{color = #8a3d91, @item{First}, @item{Second}}` |
| `@item` | Creates an item inside `@enumerate` or `@itemize`; may have a title. | `@item{An item}` or `@item{title = "Step one", Details.}` |
| `@theorem` | Creates a numbered theorem environment. | `@theorem{Fundamental Theorem, label = fundamental-theorem}` |
| `@lemma` | Creates a numbered lemma environment. | `@lemma{A Useful Lemma, label = useful-lemma}` |
| `@definition` | Creates a numbered definition environment. | `@definition{Continuity, label = continuity}` |
| `@corollary` | Creates a numbered corollary environment. | `@corollary{Immediate Consequence}` |
| `@axiom` | Creates a numbered axiom environment. | `@axiom{A Basic Axiom}` |
| `@proposition` | Creates a numbered proposition environment. | `@proposition{A Small Proposition}` |
| `@remark` | Creates a numbered remark environment. | `@remark{A Useful Remark}` |
| `@example` | Creates a numbered example environment. | `@example{A Simple Example}` |
| `@conjecture` | Creates a numbered conjecture environment. | `@conjecture{A Possible Pattern}` |
| `@notation` | Creates a numbered notation environment. | `@notation{Standard Notation}` |
| `@warning` | Creates a numbered warning environment. | `@warning{A Common Pitfall}` |
| `@proof` | Creates a proof environment with a Q.E.D. marker. | `@proof{}` |
| `@label` | Creates a named anchor at the current location. | `@label{important-point}` |
| `@ref` | Creates a clickable cross-reference to a label or page anchor. | `@ref{fundamental-theorem}` |
| `@relatedlinks` | Adds a related link to the sidebar. | `@relatedlinks{Python, href = https://www.python.org}` |
| `@relatedlink` | Alias for `@relatedlinks`. | `@relatedlink{Python, href = https://www.python.org}` |

### Images

Single-image figures can be written as:

```text
@image{
    image = figure.png,
    width = 65%,
    caption = The completeness construction.
}
```

`src = figure.png` is also accepted for single images. Width and height accept CSS size values such as `300px`, `50%`, `20rem`, or `80vw`.

For multiple images in one figure, use indexed image names:

```text
@image{
    image(1) = first.png,
    image(2) = second.png,
    image(3) = third.png,
    caption = Three stages of the construction.
}
```

All images are placed in the same row with equal widths by default. You can resize individual images with `width(n)` and individual heights with `height(n)`:

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

Here image 1 occupies 50% of the row, image 2 occupies 25%, and image 3 receives the remaining space. Heights are independent; an image without `height(n)` uses the group's default height. CSS size values such as `px`, `%`, `rem`, and `vw` are accepted.

Whenever an image or image group has a `caption`, Mark Two automatically formats it as **Figure N:** followed by the caption text, where the figure number counts image figures in document order. A multi-image row counts as one figure.

## Cross References

Give a section or environment a `label`, then reference it elsewhere:

```text
@section{Main Result, label = main-result}

@theorem{Fundamental Theorem, label = fundamental-theorem}

The statement of the theorem.

@proof{}

A proof goes here.
```

Later in the document:

```text
By @ref{fundamental-theorem}, the desired result follows from @ref{main-result}.
```

The generated references are clickable HTML links that jump to the corresponding labeled object.

Custom link text is also supported:

```text
@ref{fundamental-theorem, text = "the theorem"}
```

A cross-page target can be written directly as an HTML page and anchor:

```text
@ref{analysis.html#fundamental-theorem}
```

## Mathematics

Inline mathematics uses standard TeX delimiters:

```text
The identity is \(a^2 + b^2 = c^2\).
```

Display mathematics uses:

```text
\[
\int_0^1 x^2\,dx = \frac{1}{3}.
\]
```

MathJax processes the mathematical expressions in the generated page.

## Editor Support

Mark Two includes a VS Code language extension under `vscode-mark-two/` with syntax highlighting, directive completion, snippets, automatic bracket/parenthesis closing, and indentation support for `.mt` files.

For extension development, open the repository in VS Code and press `F5`. This launches an Extension Development Host with Mark Two support enabled.

## Project Layout

```text
mark-two/
├── src/                 # Mark Two Python package source
├── test/                # Example Mark Two source document
├── web/                 # HTML template and frontend assets
├── build/               # Generated example HTML bundle
├── vscode-mark-two/     # VS Code language support
└── pyproject.toml       # Python package and CLI configuration
```
