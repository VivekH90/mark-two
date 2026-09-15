@documenttitle{Mark Two Test}

@button{Home, href = /, color = black}
@button{GitHub, href = https://github.com/VivekH90/mark-two, color = #4f6fd8}
@button{About, href = /about, color = #4f9d69}

@title{A Test Article for Mark Two}

@section{Introduction, color = #1f4f91}

This is the first test document for Mark Two. It is written using the custom document syntax rather than HTML.

The purpose of this file is to check that the basic document structure is parsed and rendered correctly.

@subsection{Goals}

The first goal is to test sections and subsections.
The second goal is to test navigation buttons and the automatically generated table of contents.

@section{Mathematics, color = #6b3fa0}

Here is some inline mathematics: $x^2 + y^2 = z^2$.

Here is a displayed equation:
$$
\int_0^1 x^2\,dx = \frac{1}{3}.
$$

@subsection{A Simple Example}

Suppose we have a function $f(x)=x^2$. MathJax should typeset this expression instead of leaving it as plain text.

@definition{A Simple Function}

A function $f : X \to Y$ assigns to every $x \in X$ exactly one element $f(x) \in Y$.

@theorem{A Basic Identity}

For every real number $x$, we have
$$
(x+1)^2 = x^2 + 2x + 1.
$$

@lemma{A Useful Observation}

If $a=b$, then $a+c=b+c$ for every real number $c$.

@corollary{Immediate Consequence}

Taking $c=-b$ gives $a-b=0$ whenever $a=b$.

@section{Conclusion, color = #9a3d3d}

If this page renders correctly, the first stage of the Mark Two mathematical article pipeline is working.

@relatedlinks{Mark Two GitHub, href = https://github.com/VivekH90/mark-two}
@relatedlinks{Python, href = https://www.python.org}
