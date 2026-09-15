<div align="center">

# Mark Two

A lightweight mathematical document language that compiles `.mt` source files into clean HTML articles.

[![HTML](https://img.shields.io/badge/HTML-MARK%20TWO-176c5b?style=for-the-badge)](https://github.com/VivekH90/mark-two)
[![MathJax](https://img.shields.io/badge/MATHJAX-SUPPORTED-76547e?style=for-the-badge)](https://www.mathjax.org/)
[![Commits](https://img.shields.io/badge/COMMITS-141-46a800?style=for-the-badge)](https://github.com/VivekH90/mark-two/commits/master)
[![Last Commit](https://img.shields.io/badge/LAST%20COMMIT-TESTING-555555?style=for-the-badge)](https://github.com/VivekH90/mark-two/commits/master)
[![License](https://img.shields.io/badge/LICENSE-NOT%20SPECIFIED-999999?style=for-the-badge)](https://github.com/VivekH90/mark-two)

</div>

## Usage

Clone the repository and enter the project directory:

```bash
git clone https://github.com/VivekH90/mark-two.git
cd mark-two
```

Compile a Mark Two document with Python 3:

```bash
python3 -m src.main test/test.mt
```

By default this writes the generated site to `build/index.html` and copies the stylesheet and JavaScript into the same `build/` directory.

A different output file can be selected with:

```bash
python3 -m src.main test/test.mt --output build/article.html
```

The HTML template can be changed with:

```bash
python3 -m src.main test/test.mt --template web/index.html
```

Open the generated HTML directly or serve the project with a local web server such as VS Code Live Server.

## Mark Two Syntax

Mark Two uses `@` directives for document structure and semantics.

| Command | Purpose | Example |
| --- | --- | --- |
| `@documenttitle` | Sets the document/site title and optional banner. | `@documenttitle{My Notes, banner = images/banner.jpg}` |
| `@button` | Adds a navigation button. | `@button{Home, href = /, color = black}` |
| `@title` | Sets the article title. | `@title{Introduction to Analysis}` |
| `@section` | Creates a numbered section. Supports `color` and `label`. | `@section{Limits, color = #315a9b, label = limits}` |
| `@subsection` | Creates a numbered subsection. Supports `label`. | `@subsection{One-sided limits, label = one-sided}` |
| `@image` | Inserts an image with optional alt text, caption, and label. | `@image{src = figure.png, alt = Diagram, caption = Figure 1, label = fig:diagram}` |
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
├── src/                 # Parser, AST, renderer, compiler entry point
├── test/                # Example Mark Two source document
├── web/                 # HTML template and frontend assets
├── build/               # Generated HTML bundle
└── vscode-mark-two/     # VS Code language support
```
