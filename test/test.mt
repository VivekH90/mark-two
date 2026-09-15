@documenttitle{Mark Two Test, banner = https://upload.wikimedia.org/wikipedia/commons/3/31/Portal_Math_Banner_Background_ka.jpg}

@button{Home, href = /, color = black}
@button{GitHub, href = https://github.com/VivekH90/mark-two, color = #4f6fd8}
@button{About, href = /about, color = #4f9d69}

@title{A Test Article for Mark Two}

@section{Introduction, color = #1f4f91}

This section verifies that ordinary prose is parsed correctly and that the generated section numbering is not duplicated.

@subsection{Goals}

The first goal is to verify section and subsection structure.
The second goal is to verify that the table of contents points to the generated anchors.

@enumerate{color = green, @item{First item in a green enumeration.}, @item{title = "hehheheh",
Second item in a green enumeration.}, @item{Third item in a green enumeration.}}

@itemize{color = #8a3d91, @item{First item in a colored itemize list.}, @item{Second item in a colored itemize list.}, @item{Third item in a colored itemize list.}}

@itemize{color = #8a3d91,
    @item{
        This list item contains an image:
        @image{src = https://placehold.co/500x280/png, alt = An image inside a list item, caption = Figure 2. An image contained inside a list item.}
    },
    @item{This item contains text and inline mathematics \(x^2 + y^2 = 1\).}
}

@section{Images, color = #8a5a2c}

This image has a caption:

@image{src = https://placehold.co/900x500/png, alt = A placeholder diagram, caption = Figure 1. An example image with a caption.}

This image has no caption:

@image{src = https://placehold.co/700x400/png, alt = A placeholder image without a caption}

@section{Mathematics, color = #6b3fa0}

Inline mathematics should be processed by MathJax: \(x^2 + y^2 = z^2\).

The following display equation checks multi-line display mathematics:
\[
\int_0^1 x^2\,dx = \frac{1}{3}.
\]

@subsection{A Simple Example}

Suppose \(f(x)=x^2\). This checks that mathematical expressions can appear naturally inside prose.

@definition{A Simple Function}

A function \(f : X \to Y\) assigns to every \(x \in X\) exactly one element \(f(x) \in Y\).

@theorem{A Basic Identity}

For every real number \(x\), we have
\[
(x+1)^2 = x^2 + 2x + 1.
\]

@lemma{A Useful Observation}

If \(a=b\), then \(a+c=b+c\) for every real number \(c\).

@corollary{Immediate Consequence}

Taking \(c=-b\) gives \(a-b=0\) whenever \(a=b\).

@section{Conclusion, color = #9a3d3d}

If this page renders correctly, the first stage of the Mark Two article pipeline is working.

@relatedlinks{Mark Two GitHub, href = https://github.com/VivekH90/mark-two}
@relatedlinks{Python, href = https://www.python.org}
