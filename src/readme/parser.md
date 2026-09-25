# Parser

## Helper Functions

1. `_slugify(text)`
   1. Take the supplied text.
   2. Remove whitespace from both ends.
   3. Convert it to lowercase.
   4. Replace every sequence of non-alphanumeric characters with `-`.
   5. Remove `-` from the beginning and end.
   6. If the result is empty, return `"section"`.
   7. Otherwise return the resulting slug.

2. `_split_top_level(text)`
   1. Create an empty list called `parts`.
   2. Create an empty list called `current`.
   3. Set `quote = None`.
   4. Set `depth = 0`.
   5. Set `escaped = False`.
   6. Read the text one character at a time.
   7. If the previous character was escaped:
      1. Set `escaped = False`.
      2. Add the current character to `current`.
      3. Continue to the next character.
   8. If the current character is `\`:
      1. Set `escaped = True`.
      2. Add `\` to `current`.
      3. Continue.
   9. If the current character is `"`:
      1. Open the quote if no quote is active.
      2. Close the quote if a quote is already active.
   10. If no quote is active:
       1. Increase `depth` when `{`, `[` or `(` is found.
       2. Decrease `depth` when `}`, `]` or `)` is found.
       3. If `,` is found while `depth = 0`, treat it as a separator.
   11. When a top-level comma is found:
       1. Join the characters in `current`.
       2. Remove surrounding whitespace.
       3. Add the result to `parts` if it is not empty.
       4. Clear `current`.
   12. After all characters have been processed:
       1. Join the remaining characters.
       2. Remove surrounding whitespace.
       3. Add the final part if it is not empty.
   13. Return `parts`.

3. `_strip_quotes(value)`
   1. Remove surrounding whitespace.
   2. Remove surrounding single or double quotation marks.
   3. Return the resulting value.

4. `_parse_key_values(text)`
   1. Create an empty dictionary called `values`.
   2. Split `text` using `_split_top_level()`.
   3. For every resulting part:
      1. If `=` exists:
         1. Split at the first `=`.
         2. Treat the left side as the key.
         3. Remove whitespace from the key.
         4. Convert the key to lowercase.
         5. Remove surrounding quotes from the value.
         6. Store the key/value pair.
      2. Otherwise:
         1. If `"name"` has not been assigned yet, use this part as `"name"`.
   4. Return `values`.

5. `_unique_slug(base, used)`
   1. Check whether `base` already exists in `used`.
   2. If it does not:
      1. Add it to `used`.
      2. Return it.
   3. If it already exists:
      1. Start with number `2`.
      2. Try `base-2`.
      3. Keep increasing the number until an unused slug is found.
      4. Add the new slug to `used`.
      5. Return it.

6. `_extract_directive(lines, start_index)`
   1. Check whether `lines[start_index]` starts with a Mark Two directive.
   2. If not, return `None`.
   3. Extract the command name.
   4. Find the opening `{`.
   5. Set brace `depth = 0`.
   6. Set `quote = None`.
   7. Set `escaped = False`.
   8. Create an empty list called `argument_parts`.
   9. Read from `start_index` onward.
   10. Track escaped characters and quotation marks.
   11. Increase brace depth when an unquoted `{` is found.
   12. Decrease brace depth when an unquoted `}` is found.
   13. When depth returns to `0`:
       1. The directive is complete.
       2. Check that there is no unexpected text after the closing `}`.
       3. Join the argument parts.
       4. Return the command, argument, and final line index.
   14. If the end of the file is reached first, raise an unclosed-directive error.

7. `_extract_directive_blocks(text, command)`
   1. Search for occurrences of the requested directive.
   2. For each occurrence:
      1. Find its opening `{`.
      2. Track brace depth.
      3. Track quotation marks.
      4. Track escaped characters.
      5. Find its matching closing `}`.
      6. Extract the complete block.
   3. If no matching `}` exists, raise an error.
   4. Continue searching after the block.
   5. Return all extracted blocks.

8. `_parse_image_group(argument, group_id)`
   1. Parse the argument using `_parse_key_values()`.
   2. Check for indexed image entries such as `image(1)`, `image(2)`, etc.
   3. Store indexed sources, widths and heights separately.
   4. If no indexed sources exist:
      1. Look for `src`.
      2. Otherwise look for `image`.
      3. If neither exists, raise an error.
      4. Create one `Image`.
      5. Return it in a list.
   5. If indexed sources exist:
      1. Sort their indexes.
      2. Require indexes to be `1, 2, 3, ...`.
      3. Require at least two indexed images.
      4. Otherwise raise an error.
      5. Create one `Image` for every indexed source.
      6. Give them the same `group_id`.
      7. Return the images.

9. `_parse_list_item_content(body)`
   1. Create a temporary section containing `body`.
   2. Call `parse()` on that temporary source.
   3. Extract the temporary section's content.
   4. Return that content.
   5. This allows list items to contain normal Mark Two content and nested structures.

10. `_parse_list(argument, ordered)`
    1. Set the default list color to `"black"`.
    2. Separate list-level properties from `@item` entries.
    3. Read the optional `color`.
    4. Extract every `@item{...}` block.
    5. For each item:
       1. Make sure there is no unexpected content outside `@item`.
       2. Check for an optional item title.
       3. Remove the title from the item body.
       4. Parse the remaining body using `_parse_list_item_content()`.
       5. Create a `ListItem`.
    6. Ensure at least one item exists.
    7. Create a `ListBlock`.
    8. Set its ordered/unordered state.
    9. Set its color.
    10. Return the `ListBlock`.

11. `_parse_text(argument)`
    1. Check whether `=` exists.
    2. If it does not:
       1. Use the entire argument as the text.
       2. Create a `TextBlock`.
       3. Return it.
    3. Otherwise parse the key/value pairs.
    4. Obtain the text from `text`, or from `name`.
    5. Raise an error if the text is empty.
    6. Determine whether bold is enabled.
    7. Determine whether italic is enabled.
    8. Obtain the optional color.
    9. Create the `TextBlock`.
    10. Return it.

12. `_add_content(container, line)`
    1. Remove whitespace from the line.
    2. If the resulting line is not empty:
       1. Append it to `container.content`.
    3. Otherwise do nothing.

13. `_title_and_label(argument)`
    1. Parse the argument using `_parse_key_values()`.
    2. Extract the `name`.
    3. Extract the `label`.
    4. Return both.


## Parse Function

1. Create an empty `Document` object.

2. Set `current_section = None`.

3. Set `current_subsection = None`.

4. Set `current_environment = None`.

5. Set `used_slugs = {}` as an empty set.
   This stores the slugs that have already been used.

6. Set `display_math_lines = None`.
   This means the parser is initially not inside a display-math block.

7. Split `source` into individual lines:
   
       lines = source.splitlines()

8. Set `index = 0`.
   This is the position of the current line in `lines`.

9. Set `image_group_id = 0`.

10. While `index < number of lines`:

    a. Read the current line:
       
           raw_line = lines[index]


    b. Check whether `display_math_lines` is not `None`.

       i. If `display_math_lines` is not `None`, the parser is currently
          inside a display-math block.

          1. Remove whitespace from the beginning and end of `raw_line`.

          2. Check whether the resulting line is `\]`.

             a. If the current line is `\]`:

                1. Determine the target where the completed
                   mathematical expression will be stored.

                   Priority is:

                   - `current_environment`
                   - otherwise `current_subsection`
                   - otherwise `current_section`

                2. If all three are `None`:

                       raise error:
                       "display math must appear after @section"

                3. Join all lines currently stored in
                   `display_math_lines` using newline characters.

                4. Create a `MathBlock` from the joined mathematical text.

                5. Append the new `MathBlock` to `target.content`.

                6. Set `display_math_lines = None`.

                   This means the parser has now left math mode.

             b. Otherwise, if the current line is not `\]`:

                1. Append `raw_line` to `display_math_lines`.

                2. Continue collecting mathematical lines.

          3. Increase `index` by `1`.

          4. Use `continue` to immediately start the next
             iteration of the main loop.


    c. If the parser is not currently in math mode, check whether
       the current line starts a display-math block.

       i. Remove whitespace from `raw_line`.

       ii. Check whether it is `\[ `.

       iii. If the line is `\[`:

            1. Set `display_math_lines = []`.

               This creates an empty buffer for the mathematical lines
               that will follow.

            2. This also changes the parser into math mode because
               `display_math_lines` is no longer `None`.

            3. Increase `index` by `1`.

            4. Use `continue` to start processing the next line.


    d. If the line was not the beginning of a math block,
       try to extract a Mark Two directive:

           directive = _extract_directive(lines, index)

       `directive` can contain:

       - the command name
       - the command argument
       - the final line occupied by the directive


    e. Check whether `directive` is `None`.

       i. If `directive` is `None`, the current line is not
          a Mark Two directive.

          1. Determine where this ordinary text should be stored.

             Priority is:

             - `current_environment`
             - otherwise `current_subsection`
             - otherwise `current_section`

          2. If a target exists:

                 add `raw_line` to the target's content

             using `_add_content()`.

          3. If no target exists, do nothing with the line.

          4. Increase `index` by `1`.

          5. Use `continue` to start the next iteration.


    f. If a directive was found:

       i. Extract its three returned values:

          1. `command`
          2. `argument`
          3. `end_index`

       ii. Normalize the command:

           1. Remove whitespace from the command.
           2. Convert the command to lowercase.
           3. Remove spaces from inside the command name.


    g. Check whether the command is one of:

           documenttitle
           title
           button
           section
           subsection
           image
           relatedlinks
           relatedlink

       i. If it is one of these commands:

          1. Set `current_environment = None`.

          This ends the current environment context before
          processing the new command.


    h. If `command == "documenttitle"`:

       i. Parse the argument using `_parse_key_values()`.

       ii. Set `document.document_tag` to:

           1. `values["name"]` if it exists,
           2. otherwise the complete `argument`.

       iii. Set `document.banner` to `values["banner"]`
            or an empty string.

       iv. Set `document.banner_color` to `values["color"]`
           or an empty string.


    i. Else if `command == "title"`:

       i. Set `document.article_title = argument`.


    j. Else if `command == "button"`:

       i. Parse the argument using `_parse_key_values()`.

       ii. Create a `Button` using:

           1. `name = values["name"]` or `"Button"`
           2. `href = values["href"]` or `"#"`
           3. `color = values["color"]` or `"black"`

       iii. Append the `Button` to `document.buttons`.


    k. Else if `command == "section"`:

       i. Parse the argument using `_parse_key_values()`.

       ii. Determine the section title:

           1. Use `values["name"]` if available.
           2. Otherwise use the complete `argument`.

       iii. Convert the title into a base slug using `_slugify()`.

       iv. Pass the base slug to `_unique_slug()` together with
           `used_slugs` to guarantee that the slug is unique.

       v. Create a `Section` using:

           1. the title
           2. the label
           3. the unique slug
           4. `values["label"]` or an empty string

       vi. Append the new `Section` to `document.sections`.

       vii. Set `current_section` to this new section.

       viii. Set `current_subsection = None`.

            This clears the previous subsection because a new
            section has started.


    l. Else if `command == "subsection"`:

       i. Check whether `current_section` is `None`.

          1. If it is `None`, raise:

                 "@subsection must appear after @section"

       ii. Extract the subsection title and label using
           `_title_and_label()`.

       iii. If the extracted title is empty:

            1. Use the complete `argument` as the title.

       iv. Convert the title into a slug using `_slugify()`.

       v. Make the slug unique using `_unique_slug()`.

       vi. Create a `Subsection` containing:

           1. the title
           2. the unique slug
           3. the label

       vii. Append the `Subsection` to `current_section.subsections`.

       viii. Set `current_subsection` to the new subsection.


    m. Else if `command == "image"`:

       i. Determine the target:

          Priority is:

          - `current_environment`
          - otherwise `current_subsection`
          - otherwise `current_section`

       ii. If the target is `None`, raise:

              "@image must appear after @section"

       iii. Increase `image_group_id` by `1`.

       iv. Pass the argument and new `image_group_id`
           to `_parse_image_group()`.

       v. Receive one or more `Image` objects.

       vi. Append all returned images to `target.content`.


    n. Else if `command == "text"`:

       i. Determine the target:

          Priority is:

          - `current_environment`
          - otherwise `current_subsection`
          - otherwise `current_section`

       ii. If the target is `None`, raise:

              "@text must appear after @section"

       iii. Parse the argument using `_parse_text()`.

       iv. Receive a `TextBlock`.

       v. Append the `TextBlock` to `target.content`.


    o. Else if `command == "label"`:

       i. Determine the target:

          Priority is:

          - `current_environment`
          - otherwise `current_subsection`
          - otherwise `current_section`

       ii. If the target is `None`, raise:

              "@label must appear after @section"

       iii. Remove surrounding quotes from the argument
            using `_strip_quotes()`.

       iv. Store the result as `label`.

       v. If the label is empty, raise:

              "@label requires a label name"

       vi. Create a `Label`.

       vii. Append the `Label` to `target.content`.


    p. Else if `command == "ref"`:

       i. Determine the target:

          Priority is:

          - `current_environment`
          - otherwise `current_subsection`
          - otherwise `current_section`

       ii. If the target is `None`, raise:

              "@ref must appear after @section"

       iii. Parse the argument using `_parse_key_values()`.

       iv. Create a `Reference` using:

           1. `values["name"]` as the target if available,
              otherwise the complete `argument`
           2. `values["text"]` as the visible text,
              otherwise an empty string

       v. Append the `Reference` to `target.content`.


    q. Else if `command` is one of the known environments:

       Supported environments are:

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

       i. Determine the target:

          Priority is:

          - `current_subsection`
          - otherwise `current_section`

       ii. If the target is `None`, raise:

              "@<environment> must appear after @section"

       iii. Extract the environment title and label
            using `_title_and_label()`.

       iv. Create an `Environment` containing:

           1. `kind = command`
           2. `title = extracted title`
           3. `label = extracted label`

       v. If the title is empty and the environment is not `proof`:

          1. Use the complete `argument` as the environment title.

       vi. Append the new `Environment` to `target.content`.

       vii. Set `current_environment` to the new environment.

            This means that subsequent ordinary content,
            mathematics, text, labels, references, and lists
            can be stored inside this environment.


    r. Else if `command` is `enumerate` or `itemize`:

       i. Determine the target:

          Priority is:

          - `current_environment`
          - otherwise `current_subsection`
          - otherwise `current_section`

       ii. If the target is `None`, raise:

              "@enumerate or @itemize must appear after @section"

       iii. Call `_parse_list()`.

       iv. Set `ordered` to:

           1. `True` when the command is `enumerate`
           2. `False` when the command is `itemize`

       v. Receive a `ListBlock`.

       vi. Append the `ListBlock` to `target.content`.


    s. Else if `command` is `relatedlinks` or `relatedlink`:

       i. Parse the argument using `_parse_key_values()`.

       ii. Check whether `"href"` exists.

       iii. If `"href"` does not exist, raise:

              "@relatedlinks requires href = ..."

       iv. Create a `RelatedLink` using:

           1. `values["name"]` or `"Related link"`
           2. `values["href"]`

       v. Append the `RelatedLink` to `document.related_links`.


    t. Else:

       i. The command is not recognized.

       ii. Raise:

              "Unknown Mark Two directive: @<command>"


    u. After successfully handling the directive:

       i. Set:

              index = end_index + 1

       ii. This moves the parser directly to the line
           immediately after the complete directive.

       iii. This is necessary because a directive can span
            multiple lines.


11. When the `while` loop reaches the end of the source:

    a. Check whether `display_math_lines` is still not `None`.

    b. If it is not `None`, the parser entered math mode but
       never encountered the closing `\]`.

    c. Raise:

           "Unclosed display math block: expected \]"


12. If no error occurred:

    a. Return the completed `Document`.

---

# Overall flow

1. Read one source line.

2. Check whether the parser is already in math mode.

3. If in math mode:
   
   a. If the line is `\]`, finish the `MathBlock`.
   
   b. Otherwise, add the line to the math buffer.

4. If not in math mode, check whether the line is `\[`.
   
   a. If yes, create `display_math_lines = []`.
   
   b. This enters math mode.

5. If it is not math, try to find a Mark Two directive.

6. If there is no directive:
   
   a. Find the current target.
   
   b. Add the line as ordinary content.

7. If there is a directive:
   
   a. Identify the command.
   
   b. Parse its arguments.
   
   c. Create or modify the appropriate AST object.
   
   d. Attach it to the appropriate location.

8. Move to the next unprocessed source line.

9. Repeat until the entire source has been processed.

10. Check for an unclosed math block.

11. Return the completed `Document`.