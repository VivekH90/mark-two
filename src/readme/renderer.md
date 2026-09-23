# Renderer

## Renderer Function

1. The renderer receives:
   
       document
       template_path

2. Read the HTML template file from `template_path` using UTF-8 encoding.

3. Create an empty list called `buttons`.

4. Iterate through every button stored in `document.buttons`.

   a. Read the button color.

   b. Escape the button color so it is safe to place inside HTML.

   c. Convert the button color into a suitable dark-mode color
      using `_dark_mode_color()`.

   d. Escape the button destination URL.

   e. Escape the button's displayed name.

   f. Create an HTML `<a>` element with:

          class = "nav-button"
          href  = button.href

      and store the light-mode and dark-mode colors as CSS variables:

          --button-color
          --button-color-dark

   g. Add the generated button HTML to `buttons`.


5. Check whether `document.banner` exists.

   a. If a banner exists:

      i. Read `document.banner_color`.

      ii. If no banner color exists, use `#ffffff`.

      iii. Escape the banner color.

      iv. Calculate the dark-mode version of the banner color
          using `_dark_mode_color()`.

      v. Escape the banner image path.

      vi. Escape the document title.

      vii. Create a banner containing:

           1. the banner image
           2. the document title as a link
           3. the light-mode banner color
           4. the dark-mode banner color

   b. Otherwise:

      i. Create a simple `document-title` link.

      ii. Use the escaped document title as its text.


6. Build the reference index by calling:

       `_build_reference_index(document)`

7. Create:

       `toc = []`

   This stores the generated table of contents HTML.

8. Create:

       `article = []`

   This stores the generated article HTML.

9. Create:

       `environment_counters = {}`

   This stores numbering information for theorem-like environments.

10. Create:

        `figure_counter = {"number": 0}`

    This stores the global figure number.


11. Iterate through every section in `document.sections`.

    a. Number sections starting from `1`.

    b. Obtain the section slug.

    c. Create a table-of-contents entry linking to the
       section's slug.

    d. Display the section number and section title.

    e. Check whether the section has subsections.

       i. If subsections exist:

          1. Start a nested ordered list for the subsections.

          2. Iterate through every subsection.

          3. Number each subsection starting from `1`.

          4. Obtain its slug.

          5. Create a link to the subsection.

          6. Display the section number and subsection number.

          7. Close the subsection list.

    f. Close the current table-of-contents entry.

    g. Render the complete section by calling:

           `_section_html(
               section,
               number,
               environment_counters,
               references,
               figure_counter
           )`

    h. Add the resulting HTML to `article`.


12. Iterate through every related link in `document.related_links`.

    a. Escape the link URL.

    b. Escape the link name.

    c. Create an `<a>` element.

    d. Set:

           target = "_blank"
           rel = "noopener noreferrer"

    e. Wrap the link inside an `<li>`.

    f. Store the generated HTML.


13. Create a replacement dictionary containing:

       `{{DOCUMENT_TITLE}}`
       `{{ARTICLE_TITLE}}`
       `{{BANNER}}`
       `{{BUTTONS}}`
       `{{TOC}}`
       `{{ARTICLE}}`
       `{{RELATED_LINKS}}`

14. Escape the document title.

15. Escape the article title.

16. Join all rendered buttons together.

17. Join all table-of-contents entries together.

18. Join all article sections together.

19. Join all related links together.

20. Iterate through every placeholder in the replacement dictionary.

    a. Replace the placeholder in the HTML template
       with its generated content.

21. Return the final HTML template.


# Helper Functions

## 1. `_dark_mode_color(value)`

1. Receive a color value.

2. Remove surrounding whitespace.

3. Check whether the color is one of the predefined CSS color names.

4. If it is:
   
   a. Replace the color name with its hexadecimal equivalent.

5. Check whether the resulting value matches a six-digit hexadecimal color.

6. If it does not:

   a. Return the original color unchanged.

7. If it does:

   a. Extract the red, green and blue components.

   b. Convert each component from `0-255` into a value between `0` and `1`.

   c. Calculate the color's luminance using:

          0.2126R + 0.7152G + 0.0722B

8. Check whether the luminance is at least `0.42`.

9. If it is:

   a. Keep the original RGB values.

10. Otherwise:

    a. Convert the color from RGB into HLS.

    b. Increase its lightness to at least `0.45`.

    c. Convert the modified HLS color back into RGB.

11. Convert the resulting RGB values back into hexadecimal form.

12. Return the resulting color.


## 2. `_parse_ref_argument(argument)`

1. Receive the argument of an inline `@ref{...}`.

2. Create:

       `parts = []`
       `current = []`

3. Set:

       `quote = None`
       `depth = 0`
       `escaped = False`

4. Read the argument one character at a time.

5. If the previous character escaped the current character:

   a. Set `escaped = False`.

   b. Append the current character to `current`.

   c. Continue to the next character.

6. If the current character is `\`:

   a. Set `escaped = True`.

   b. Append the backslash to `current`.

   c. Continue.

7. If the current character is a quote:

   a. Open the quote if no quote is active.

   b. Close the quote if the same quote is active.

8. If no quote is active:

   a. Increase `depth` for `{`, `[` and `(`.

   b. Decrease `depth` for `}`, `]` and `)`.

   c. If the current character is a comma and `depth = 0`:

      1. Finish the current part.

      2. Add it to `parts`.

      3. Clear `current`.

9. Append normal characters to `current`.

10. After the entire argument has been processed:

    a. Append the final part to `parts`.

11. Treat the first part as the reference target.

12. Search all remaining parts for:

        `text = ...`

13. Store the supplied text as the custom reference text.

14. Return:

        target
        custom text


## 3. `_split_top_level(argument)`

1. Receive an argument string.

2. Create:

       `parts = []`
       `current = []`

3. Set:

       `quote = None`
       `depth = 0`
       `escaped = False`

4. Process the argument one character at a time.

5. Handle escaped characters.

6. Track quotation marks.

7. When outside quotes:

   a. Increase `depth` for `{`, `[` and `(`.

   b. Decrease `depth` for `}`, `]` and `)`.

   c. Treat a comma as a separator only when `depth = 0`.

8. Store each top-level part.

9. Store the final part.

10. Return the list of parts.


## 4. `_strip_quotes(value)`

1. Remove whitespace from the beginning and end of `value`.

2. Check whether the value has at least two characters.

3. Check whether its first and last characters are the same quote type.

4. If they are:

   a. Remove the first and last characters.

5. Return the resulting value.


## 5. `_parse_key_value_fields(argument)`

1. Split the argument using `_split_top_level()`.

2. Create an empty dictionary called `fields`.

3. For every resulting part:

   a. Check whether `=` exists.

   b. If `=` exists:

      1. Split at the first `=`.

      2. Remove whitespace from the key.

      3. Convert the key to lowercase.

      4. Remove surrounding quotes from the value.

      5. Store the key/value pair in `fields`.

4. Return `fields`.


## 6. `_extract_inline_block(text, start)`

1. Search for the first `{` at or after `start`.

2. If no `{` exists:

   a. Return `None`.

3. Set:

       `depth = 0`
       `quote = None`
       `escaped = False`

4. Scan the text from the opening brace onward.

5. If a character is escaped:

   a. Clear the escaped state.

   b. Continue.

6. If the current character is `\`:

   a. Set `escaped = True`.

   b. Continue.

7. If the current character is a quote:

   a. Open or close the quote.

   b. Continue.

8. If a quote is active:

   a. Ignore braces because they are inside quoted text.

9. When `{` is found:

   a. Increase `depth`.

10. When `}` is found:

    a. Decrease `depth`.

    b. If `depth = 0`:

       1. The inline block is complete.

       2. Return the text inside the braces.

       3. Return the position immediately after the closing brace.

11. If no matching closing brace is found:

    a. Return `None`.


## 7. `_looks_like_url(target)`

1. Receive a reference target.

2. Check whether it matches an HTTP or HTTPS URL.

3. Check whether it is a root-relative path.

4. Check whether it looks like a relative `.html` file.

5. Check whether it contains `#`.

6. Return `True` when one of these conditions matches.

7. Otherwise return `False`.


## 8. `_split_inline_color(argument)`

1. Parse the argument using `_parse_key_value_fields()`.

2. Search for:

       `color`
       `colour`

3. Search for content under:

       `text`
       `content`

4. If both a color and content are found:

   a. Return them.

5. Otherwise split the argument using `_split_top_level()`.

6. If at least two parts exist:

   a. Treat the first part as the color.

   b. Join the remaining parts as the content.

   c. Return both.

7. Otherwise:

   a. Return an empty color.

   b. Return the entire argument as content.


## 9. `_safe_color(value)`

1. Remove surrounding whitespace.

2. Check whether the value is a hexadecimal color.

3. Check whether it is an `rgb`, `rgba`, `hsl`, or `hsla` expression.

4. Check whether it is an alphabetic CSS color name.

5. Return `True` if any accepted format matches.

6. Otherwise return `False`.


# Inline Text Rendering

## 10. `_inline_text(text, references)`

1. Create an empty list called `output`.

2. Set:

       `i = 0`

3. Define the supported inline commands:

       `ref`
       `bold`
       `italic`
       `color`

4. While `i < length of text`:

   a. Check whether one of the supported commands begins at
      position `i`.

   b. If a command is found:

      i. Extract its complete `{...}` block using
         `_extract_inline_block()`.

      ii. If extraction succeeds, obtain:

          1. the argument
          2. the position immediately after the block

      iii. If the command is `bold`:

           1. Recursively call `_inline_text()` on its argument.

           2. Wrap the result in `<strong>...</strong>`.

      iv. If the command is `italic`:

           1. Recursively call `_inline_text()`.

           2. Wrap the result in `<em>...</em>`.

      v. If the command is `color`:

           1. Split the color argument using `_split_inline_color()`.

           2. Check whether the color is valid using `_safe_color()`.

           3. If valid:

              a. Calculate its dark-mode color.

              b. Create a `<span>`.

              c. Store both colors as CSS variables.

              d. Recursively render the colored content.

           4. If invalid:

              a. Escape the original inline command instead.

      vi. If the command is `ref`:

           1. Parse the reference target and optional custom text.

           2. Search the `references` dictionary.

           3. If the target exists:

              a. Use the stored href.

              b. Use the custom text if supplied.

              c. Otherwise use the stored reference label.

              d. Create a normal cross-reference link.

           4. If the target does not exist:

              a. Determine whether it looks like a URL.

              b. If it does, use it directly.

              c. Otherwise create an internal `#target` link.

              d. Mark the link as an unresolved reference.

           5. Add the generated link to `output`.

      vii. Set `i` to the end of the inline command.

      viii. Continue to the next iteration.

   c. If no inline command begins at `i`:

      i. Find the next `@` symbol.

      ii. If no `@` exists, use the rest of the text.

      iii. Take the ordinary text between `i` and the next inline command.

      iv. Escape it for HTML.

      v. Add it to `output`.

      vi. Move `i` to the next inline command.

5. Join all elements of `output`.

6. Return the resulting HTML.


# Text Rendering

## 11. `_paragraphs(lines, references)`

1. Check whether `lines` is empty.

2. If it is empty, return an empty string.

3. Create:

       `paragraphs = []`
       `current = []`

4. Process every line.

5. If the current line contains text:

   a. Strip its surrounding whitespace.

   b. Add it to `current`.

6. If the current line is empty and `current` contains text:

   a. Join the lines in `current` with spaces.

   b. Add the resulting paragraph to `paragraphs`.

   c. Clear `current`.

7. After all lines have been processed:

   a. If `current` still contains text, create the final paragraph.

8. For every paragraph:

   a. Pass it through `_inline_text()`.

   b. Wrap it in `<p>...</p>`.

9. Join all generated paragraphs with newlines.

10. Return the HTML.


## 12. `_text_html(text, references)`

1. Create an empty list called `styles`.

2. If `text.bold` is true:

   a. Add:

          `font-weight: 700`

3. If `text.italic` is true:

   a. Add:

          `font-style: italic`

4. If `text.color` exists and `_safe_color()` accepts it:

   a. Store the light-mode color as `--text-color`.

   b. Calculate its dark-mode color.

   c. Store it as `--text-color-dark`.

5. If styles exist:

   a. Join them into a CSS style string.

6. Render the actual text using `_inline_text()`.

7. Wrap the result in:

       `<p class="mark-text">...</p>`

8. Return the generated HTML.


## 13. `_math_html(math)`

1. Receive a `MathBlock`.

2. Read its mathematical content.

3. Wrap the content in:

       `<div class="math-display">`

4. Place the expression between:

       `\[`
       `\]`

5. Close the div.

6. Return the generated HTML.


# Image Rendering

## 14. `_image_tag(image, extra_style)`

1. Create an empty list of styles.

2. If the image has a width:

   a. Add a width style.

3. If the image has a height and the height is not `"auto"`:

   a. Add a height style.

4. If `extra_style` exists:

   a. Add it to the style list.

5. If styles exist:

   a. Join them into a single CSS style attribute.

6. Escape the image source.

7. Escape the image alternative text.

8. Create an `<img>` element.

9. Add:

       `loading="lazy"`

10. Add the generated style attribute when necessary.

11. Return the image tag.


## 15. `_caption_html(caption, figure_number)`

1. Receive a caption and figure number.

2. Escape the caption.

3. Create:

       `<figcaption>`

4. Add:

       `Figure <number>:`

   in bold.

5. Add the caption.

6. Close the `figcaption`.

7. Return the result.


## 16. `_image_html(image, figure_number)`

1. Check whether the image has a label.

2. If it does, create an HTML `id` from the label.

3. Create a `<figure>` with class `article-image`.

4. Add the image using `_image_tag()`.

5. Check whether the image has a caption.

6. If it does:

   a. Create the caption using `_caption_html()`.

   b. Add the caption to the figure.

7. Close the figure.

8. Return the complete figure HTML.


## 17. `_multi_image_html(images, figure_number)`

1. Receive multiple images belonging to the same image group.

2. Use the label of the first image as the figure ID when available.

3. Collect all image widths.

4. Determine which images have explicit widths.

5. If no image has an explicit width:

   a. Give every image an equal grid column.

6. If every image has an explicit width:

   a. Use those widths directly as the grid columns.

7. If only some images have explicit widths:

   a. Keep the explicit widths.

   b. Calculate the remaining column widths from the
      remaining available space.

8. Create an empty list called `image_html`.

9. Process every image:

   a. If the image has a fixed height that is not `"auto"`:

      1. Make the image width `100%`.

      2. Use the specified height.

      3. Set `object-fit = cover`.

   b. Otherwise:

      1. Make the image width `100%`.

      2. Use automatic height.

      3. Set `object-fit = contain`.

   c. Render the image using `_image_tag()`.

   d. Add it to `image_html`.

10. Create a CSS grid containing all rendered images.

11. Use a `10px` gap between grid columns.

12. Create a `<figure>` with class `multi-image`.

13. Add the grid containing the images.

14. If the first image has a caption:

    a. Render the caption.

    b. Add it to the figure.

15. Close the figure.

16. Return the complete HTML.


# List Rendering

## 18. `_list_html(list_block, environment_counters, references, figure_counter, depth)`

1. Check whether the list is ordered.

2. If ordered:

   a. Use `<ol>`.

3. Otherwise:

   a. Use `<ul>`.

4. If the list is ordered and `depth > 0`:

   a. Add:

          `type="a"`

   so nested ordered lists use letters.

5. Escape the list color.

6. Calculate its dark-mode color.

7. Create an empty list called `items`.

8. Iterate through every `ListItem`.

   a. If the item has a title:

      1. Create a `list-item-title` span.

      2. Give the `<li>` a `has-list-item-title` class.

   b. Otherwise:

      1. Do not create the title span.

      2. Do not add the extra class.

   c. Recursively render the item's content using
      `_content_html()`.

   d. Increase the list depth for the recursive call.

   e. Create the `<li>` containing the item's title and content.

   f. Add it to `items`.

9. Create the `<ol>` or `<ul>`.

10. Add the list color variables:

       `--list-color`
       `--list-color-dark`

11. Add all rendered list items.

12. Close the list.

13. Return the resulting HTML.


# Environment Rendering

## 19. `_environment_html(environment, number, environment_counters, references, figure_counter)`

1. Convert the environment type to lowercase.

2. Create an HTML ID from the environment label if one exists.

3. Render the environment's content recursively using `_content_html()`.

4. Check whether the environment type is `proof`.

5. If it is a proof:

   a. Create a `proof-environment`.

   b. Add a `Proof` heading.

   c. Add the rendered proof content.

   d. Add the Q.E.D. square.

   e. Return the generated proof HTML.

6. Otherwise:

   a. Capitalize the environment type.

   b. Create the environment label.

   c. Add the environment number.

   d. If a title exists:

      1. Add the title in parentheses.

   e. Create a `math-environment` div.

   f. Add the environment heading.

   g. Add the rendered environment content.

   h. Return the generated HTML.


# Content Traversal

## 20. `_content_html(items, environment_counters, references, figure_counter, list_depth)`

This function walks through the AST content and chooses how each AST node should be rendered.

1. Create an empty list called `html`.

2. Set:

       `index = 0`

3. While `index < number of items`:

   a. Read:

          `item = items[index]`

   b. Check the type of `item`.


4. If `item` is an `Environment`:

   a. Increase the counter for its environment type.

   b. Use that counter as its environment number.

   c. Call `_environment_html()`.

   d. Add the generated HTML to `html`.


5. Else if `item` is an `Image`:

   a. Start a temporary image group containing the current image.

   b. Set `next_index = index + 1`.

   c. Look at subsequent items.

   d. Continue collecting images while:

      1. The next item is also an `Image`.

      2. Its group ID matches the current image's group ID.

   e. Stop when the next item is not part of the group.

   f. Increase the global figure counter.

   g. If the group contains exactly one image:

      1. Render it using `_image_html()`.

   h. Otherwise:

      1. Render the entire group using `_multi_image_html()`.

   i. Add the resulting figure HTML to `html`.

   j. Move `index` to the end of the image group.


6. Else if `item` is a `MathBlock`:

   a. Render it using `_math_html()`.

   b. Add the result to `html`.


7. Else if `item` is a `TextBlock`:

   a. Render it using `_text_html()`.

   b. Add the result to `html`.


8. Else if `item` is a `ListBlock`:

   a. Render it using `_list_html()`.

   b. Pass the current list depth.

   c. Add the result to `html`.


9. Else if `item` is a `Label`:

   a. Create an empty `<span>`.

   b. Give it the class `mark-label`.

   c. Set its HTML ID to the label name.

   d. Add it to `html`.


10. Else if `item` is a `Reference`:

    a. Search for the reference target in `references`.

    b. If the target exists:

       1. Get its href.

       2. Get its generated label text.

       3. Use the custom reference text if supplied.

       4. Otherwise use the generated label text.

    c. If the target does not exist:

       1. Check whether the target looks like a URL.

       2. If it does, use it directly.

       3. Otherwise create a `#target` link.

       4. Use the target itself as fallback visible text.

    d. Create a cross-reference link.

    e. Add it to `html`.


11. Otherwise:

    a. The item is treated as ordinary string content.

    b. Pass it to `_paragraphs()`.

    c. Add the result to `html`.


12. Increase `index` by `1`.

13. Repeat until every content item has been processed.

14. Join all generated HTML with newlines.

15. Return the result.


# Reference Index

## 21. `_build_reference_index(document)`

1. Create:

       `references = {}`
       `counters = {}`

2. Iterate through every section in `document.sections`.

3. Number the sections starting from `1`.

4. If a section has a label:

   a. Map that label to the section's slug.

   b. Store generated text such as:

          `Section 1`

5. Iterate through every subsection in that section.

6. Number subsections starting from `1`.

7. If a subsection has a label:

   a. Map the label to its slug.

   b. Store generated text such as:

          `Subsection 1.2`

8. Create a temporary list containing:

   a. the section's direct content

   b. the content of all its subsections

9. Iterate through this combined content.

10. If an item is an `Environment`:

    a. Increase the counter for its environment type.

    b. If the environment has a label:

       1. Map the label to the environment's ID.

       2. Generate reference text such as:

              `Theorem 1`
              `Definition 2`

11. Return the completed `references` dictionary.


# Section Rendering

## 22. `_section_html(section, number, environment_counters, references, figure_counter)`

1. Escape the section color.

2. Calculate its dark-mode color.

3. Obtain the section slug.

4. Create a `<section>` element.

5. Use the section slug as its HTML ID.

6. Add the section heading.

7. Display:

       §
       section number
       section title

8. Render the section's direct content using `_content_html()`.

9. Iterate through every subsection.

10. Number each subsection starting from `1`.

11. For every subsection:

    a. Obtain its slug.

    b. Create an `article-subsection`.

    c. Add its HTML ID.

    d. Add the subsection number and title.

    e. Render its content using `_content_html()`.

    f. Close the subsection.

12. Close the main section.

13. Join all generated pieces with newlines.

14. Return the complete section HTML.


# Main Rendering Pipeline

## 23. Complete flow

1. Receive the parsed `Document`.

2. Read the HTML template.

3. Render all document buttons.

4. Render the document banner or document title.

5. Build the reference index.

6. Initialize:

       table of contents
       article HTML
       environment counters
       figure counter

7. Walk through every section.

8. For every section:

   a. Add it to the table of contents.

   b. Add its subsections to the table of contents.

   c. Render the section.

9. Render all related links.

10. Build the placeholder replacement dictionary.

11. Replace:

       `{{DOCUMENT_TITLE}}`
       `{{ARTICLE_TITLE}}`
       `{{BANNER}}`
       `{{BUTTONS}}`
       `{{TOC}}`
       `{{ARTICLE}}`
       `{{RELATED_LINKS}}`

    inside the HTML template.

12. Return the fully rendered HTML document.


# Core Renderer Idea

The renderer can therefore be understood as:

1. Receive the AST.

2. Build information that is needed globally, especially the reference index.

3. Walk through the AST.

4. For every AST node:

   a. Determine its type.

   b. Call the corresponding rendering function.

5. Recursively render nested content.

6. Keep global numbering consistent for figures and environments.

7. Insert all generated HTML into the template.

8. Return the final HTML.

In condensed form:

~~~text
AST
 │
 ├── Document
 │     │
 │     ├── Buttons
 │     ├── Banner
 │     ├── Sections
 │     │     │
 │     │     ├── TextBlock
 │     │     ├── MathBlock
 │     │     ├── Image
 │     │     ├── ListBlock
 │     │     ├── Label
 │     │     ├── Reference
 │     │     └── Environment
 │     │              └── nested content
 │     │
 │     └── RelatedLinks
 │
 ▼
HTML fragments
 │
 ▼
Template placeholders replaced
 │
 ▼
Final HTML
~~~