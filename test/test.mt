@documenttitle{Mark Two Test, banner = https://upload.wikimedia.org/wikipedia/commons/3/31/Portal_Math_Banner_Background_ka.jpg}

@button{Home, href = /, color = black}
@button{GitHub, href = https://github.com/VivekH90/mark-two, color = #4f6fd8}
@button{About, href = /about, color = #4f9d69}

@title{A Test Article for Mark Two}

@section{Introduction, color = #1f4f91, label = introduction}

This section verifies ordinary prose, labels, and cross references. Later we will refer back to @ref{introduction}.

@subsection{Goals, label = goals}

The first goal is to verify section and subsection structure. See @ref{goals} for this subsection.
The second goal is to verify that references can point to generated anchors.

@enumerate{color = green, @item{First item in a green enumeration.}, @item{title = "hehheheh", Second item in a green enumeration.}, @item{Third item in a green enumeration.}}

@itemize{color = #8a3d91, @item{First item in a colored itemize list.}, @item{Second item in a colored itemize list.}, @item{Third item in a colored itemize list.}}

@section{Images, color = #8a5a2c, label = images}

This image has a caption:

@image{src = https://placehold.co/900x500/png, alt = A placeholder diagram, caption = Figure 1. An example image with a caption., label = diagram}

You can jump directly to @ref{diagram, text = "the diagram"}.

This image has no caption:

@image{src = https://placehold.co/700x400/png, alt = A placeholder image without a caption}

@section{Mathematics, color = #6b3fa0, label = mathematics}

Inline mathematics should be processed by MathJax: \(x^2 + y^2 = z^2\).

The following display equation checks multi-line display mathematics:
\[
\int_0^1 x^2\,dx = \frac{1}{3}.
\]

@subsection{A Simple Example, label = simple-example}

Suppose \(f(x)=x^2\). This checks that mathematical expressions can appear naturally inside prose.

@axiom{A Basic Axiom, label = basic-axiom}

For every object \(x\), we assume the stated axiom holds. See @ref{basic-axiom}.

@definition{A Simple Function, label = simple-function}

A function \(f : X \to Y\) assigns to every \(x \in X\) exactly one element \(f(x) \in Y\).

@theorem{A Basic Identity, label = basic-identity}

For every real number \(x\), we have
\[
(x+1)^2 = x^2 + 2x + 1.
\]

@proof{}

We expand the left-hand side:
\[
(x+1)^2 = x^2 + 2x + 1.
\]
This is exactly the required identity.

@lemma{A Useful Observation, label = useful-observation}

If \(a=b\), then \(a+c=b+c\) for every real number \(c\).

@proof{}

Adding the same quantity \(c\) to both sides of \(a=b\) preserves equality, so \(a+c=b+c\). Therefore the lemma follows.

@proposition{A Small Proposition, label = small-proposition}

Every integer is either even or odd.

@remark{A Brief Remark, label = brief-remark}

The terminology is standard, but the convention is worth remembering.

@example{A Simple Example, label = simple-example-env}

Take the integer \(4\). It is even.

@conjecture{A Test Conjecture, label = test-conjecture}

There are infinitely many primes of the required form.

@notation{A Test Notation, label = test-notation}

We write \(\mathbb{N}\) for the natural numbers.

@warning{A Test Warning, label = test-warning}

Do not confuse a necessary condition with a sufficient one.

@corollary{Immediate Consequence, label = immediate-consequence}

Taking \(c=-b\) gives \(a-b=0\) whenever \(a=b\).

@section{Cross-Page Links, color = #39745a, label = cross-page}

A cross-page reference can use a generated page and anchor directly, for example @ref{other-article.html#main-theorem, text = "Theorem on another page"}.

A named anchor can also be created explicitly:

@label{custom-anchor}

This paragraph follows an explicit anchor. Jump back to @ref{custom-anchor}.

@section{Conclusion, color = #9a3d3d}

If this page renders correctly, Mark Two supports labels, local references, cross-page references, and the expanded semantic environment family.

@relatedlinks{Mark Two GitHub, href = https://github.com/VivekH90/mark-two}
@relatedlinks{Python, href = https://www.python.org}
