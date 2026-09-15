# Text formatting in Mark Two

Mark Two supports normal prose and simple whole-block formatting through `@text`.

## Normal text

```text
@text{This is normal text.}
```

The longer explicit form is also supported:

```text
@text{text = "This is normal text."}
```

## Bold

```text
@text{bold = true, text = "This text is bold."}
```

## Italic

```text
@text{italic = true, text = "This text is italic."}
```

## Color

Use any CSS color value, including named colors and hex colors:

```text
@text{color = red, text = "This text is red."}
@text{color = #315a9b, text = "This text uses a custom color."}
```

## Combine formatting

```text
@text{
    bold = true,
    italic = true,
    color = #315a9b,
    text = "Bold, italic, and colored text."
}
```

`bold` and `italic` accept `true`, `false`, `yes`, `no`, `on`, and `off`.

`@text` can appear in sections, subsections, theorem-like environments, proofs, and list items.

## Nested enumerate

An `@enumerate` inside an `@item` is a nested ordered list. Top-level enumerations remain numeric, while nested enumerations use lowercase letters:

```text
@enumerate{
    @item{
        First main point.
        @enumerate{
            @item{First sub-point.}
            @item{Second sub-point.}
            @item{Third sub-point.}
        }
    }
    @item{Second main point.}
}
```

This renders as:

1. First main point.
   a. First sub-point.
   b. Second sub-point.
   c. Third sub-point.
2. Second main point.

Further nested `@enumerate` blocks continue to use the alphabetic style.
