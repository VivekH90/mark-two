# Parser

## slug

~~~text

FUNCTION PARSE(source):

    # create a root
    document = new Document

    # initialisation
    current_section = NONE
    current_subsection = NONE
    current_environment = NONE
    used_slugs = EMPTY SET
    math_buffer = NONE
    image_group_id = 0
    lines = SPLIT source INTO lines
    index = 0



    # Continue until every line of the source has been processed.
    WHILE index < number_of(lines):

        # Get the current line.
        line = lines[index]

        # math mode

        # "\[" starts a display-math block.
        IF STRIP(line) == "\[":

            math_buffer = EMPTY LIST

            index = index + 1
            CONTINUE

        IF math_buffer IS NOT NONE:

            # "\]" marks the end of the display-math block.
            IF STRIP(line) == "\]":

                # puts the math_buffer[] into the environment, subsection or section.
                target = current_environment OR current_subsection OR current_section

                # Display mathematics cannot exist before
                # a section/subsection/environment exists.
                IF target == NONE:

                    ERROR "display math must appear after @section"


                # Convert all collected math lines into one MathBlock.
                math = new MathBlock(
                    JOIN math_buffer WITH newline
                )

                # Store the MathBlock in the current AST container.
                APPEND math TO target.content

                # We have reached the end of the math block,
                # so leave math mode.
                math_buffer = NONE

            ELSE:

                # This line is part of the current mathematical expression.
                # Keep collecting it until "\]" appears.
                APPEND line TO math_buffer

            # Move to the next line.
            index = index + 1

            # The current line has already been handled,
            # so restart the main loop.
            CONTINUE

        # ------------------------------------------------
        # DIRECTIVE DETECTION
        # ------------------------------------------------

        # Try to determine whether the current line begins
        # a Mark Two directive such as:
        #
        # @section{...}
        # @text{...}
        # @image{...}
        # @theorem{...}
        #
        # EXTRACT_DIRECTIVE also handles directives spanning
        # multiple lines and balanced braces.
        directive = EXTRACT_DIRECTIVE(lines, index)



        # ------------------------------------------------
        # NORMAL TEXT
        # ------------------------------------------------

        # If no Mark Two directive was found,
        # the line is treated as ordinary article text.
        IF directive == NONE:

            # Again choose the deepest active container.
            target =
                current_environment
                OR current_subsection
                OR current_section


            # Text can only be stored if we are inside
            # a section/subsection/environment.
            IF target IS NOT NONE:

                # Add the line to the current content.
                # Empty lines are ignored.
                ADD_NONEMPTY_LINE(target, line)


            # Move forward one line.
            index = index + 1
            CONTINUE



        # ------------------------------------------------
        # DIRECTIVE FOUND
        # ------------------------------------------------

        # Extract the information returned by EXTRACT_DIRECTIVE.
        #
        # command    = directive name
        # argument   = everything inside {...}
        # end_index  = final source line occupied by the directive
        command = directive.command
        argument = directive.argument
        end_index = directive.end_index


        # Normalize the command name.
        #
        # Lowercase:
        #     @Section -> @section
        #
        # Remove spaces:
        #     @document title -> @documenttitle
        command = LOWERCASE(command)
        REMOVE SPACES FROM command



        # ------------------------------------------------
        # SOME DIRECTIVES CLOSE CURRENT ENVIRONMENT STATE
        # ------------------------------------------------

        # These commands indicate that we are starting
        # a new structural element or document-level element.
        #
        # Therefore the parser stops treating later content
        # as belonging to the previous environment.
        IF command is one of:

            documenttitle
            title
            button
            section
            subsection
            image
            relatedlinks
            relatedlink

        THEN:

            current_environment = NONE



        # ------------------------------------------------
        # DOCUMENT TITLE
        # ------------------------------------------------

        IF command == documenttitle:

            # Convert the argument into key/value pairs.
            #
            # For example:
            #
            # name = "Mathematics",
            # banner = "background.png",
            # color = "#FFD3AC"
            #
            # becomes a dictionary of values.
            values = PARSE_KEY_VALUES(argument)


            # Store the document title.
            #
            # It can either be written explicitly as:
            #
            # name = "Mathematics"
            #
            # or simply as:
            #
            # @documenttitle{Mathematics}
            document.document_title =
                values["name"] OR argument


            # Optional banner image/path.
            document.banner =
                values["banner"] OR ""


            # Optional banner color.
            document.banner_color =
                values["color"] OR ""



        # ------------------------------------------------
        # ARTICLE TITLE
        # ------------------------------------------------

        ELSE IF command == title:

            # Store the title of the article.
            document.article_title = argument



        # ------------------------------------------------
        # BUTTON
        # ------------------------------------------------

        ELSE IF command == button:

            # Parse button properties.
            values = PARSE_KEY_VALUES(argument)


            # Construct a Button AST node.
            button = new Button(

                # Use "Button" if no name was supplied.
                name = values["name"] OR "Button",

                # Use "#" if no destination was supplied.
                href = values["href"] OR "#",

                # Use black as the default color.
                color = values["color"] OR "black"

            )


            # Buttons belong directly to the Document.
            APPEND button TO document.buttons



        # ------------------------------------------------
        # SECTION
        # ------------------------------------------------

        ELSE IF command == section:

            # Parse section properties such as:
            #
            # name
            # color
            # label
            values = PARSE_KEY_VALUES(argument)


            # If no explicit name= was given,
            # use the whole argument as the title.
            title =
                values["name"] OR argument


            # Turn the human-readable title into a URL-friendly slug.
            #
            # Example:
            #
            # "Real Analysis"
            #
            # becomes:
            #
            # "real-analysis"
            base_slug = SLUGIFY(title)


            # Make sure this slug has not already been used.
            #
            # If "real-analysis" already exists,
            # this might produce "real-analysis-2".
            slug = UNIQUE_SLUG(
                base_slug,
                used_slugs
            )


            # Create the Section AST node.
            section = new Section(

                # Human-readable section title.
                title = title,

                # Optional section color.
                # Default = "#111111".
                color = values["color"] OR "#111111",

                # URL-friendly identifier.
                slug = slug,

                # Optional reference label.
                label = values["label"] OR ""

            )


            # Add the new section to the Document.
            APPEND section TO document.sections


            # This newly created section becomes
            # the current section.
            current_section = section


            # A new section means we are no longer
            # inside the previous subsection.
            current_subsection = NONE



        # ------------------------------------------------
        # SUBSECTION
        # ------------------------------------------------

        ELSE IF command == subsection:

            # A subsection must belong to some section.
            IF current_section == NONE:

                ERROR "@subsection must appear after @section"


            # Extract the subsection title and optional label.
            title, label =
                PARSE_TITLE_AND_LABEL(argument)


            # If no explicit title was found,
            # use the complete argument as the title.
            IF title is empty:

                title = argument


            # Generate a unique URL slug.
            slug = UNIQUE_SLUG(

                SLUGIFY(title),

                used_slugs

            )


            # Create the Subsection AST node.
            subsection = new Subsection(

                title = title,

                slug = slug,

                label = label

            )


            # Attach the subsection to the current section.
            APPEND subsection
            TO current_section.subsections


            # This subsection becomes the current content location.
            current_subsection = subsection



        # ------------------------------------------------
        # IMAGE
        # ------------------------------------------------

        ELSE IF command == image:

            # Images can appear inside:
            #
            # 1. an environment
            # 2. a subsection
            # 3. a section
            #
            # Choose the deepest active one.
            target =
                current_environment
                OR current_subsection
                OR current_section


            # An image cannot exist outside the document structure.
            IF target == NONE:

                ERROR "@image must appear after @section"


            # Every @image directive gets a new group id.
            image_group_id += 1


            # Parse the image arguments.
            #
            # This may produce one Image node,
            # or several Image nodes for a multi-image group.
            images =
                PARSE_IMAGE_GROUP(
                    argument,
                    image_group_id
                )


            # Add all resulting Image nodes to the current content.
            APPEND all images TO target.content



        # ------------------------------------------------
        # TEXT
        # ------------------------------------------------

        ELSE IF command == text:

            # Determine where the text belongs.
            target =
                current_environment
                OR current_subsection
                OR current_section


            # Text must appear inside a section/subsection/environment.
            IF target == NONE:

                ERROR "@text must appear after @section"


            # Parse the @text arguments.
            #
            # This converts things like:
            #
            # bold = true
            # italic = true
            # color = red
            #
            # into a TextBlock AST node.
            text_block =
                PARSE_TEXT(argument)


            # Add it to the current content.
            APPEND text_block
            TO target.content



        # ------------------------------------------------
        # LABEL
        # ------------------------------------------------

        ELSE IF command == label:

            # Find the deepest active container.
            target =
                current_environment
                OR current_subsection
                OR current_section


            # A label needs somewhere to attach.
            IF target == NONE:

                ERROR "@label must appear after @section"


            # Remove surrounding quotes.
            label_name =
                STRIP_QUOTES(argument)


            # Empty labels are invalid.
            IF label_name is empty:

                ERROR "@label requires a label name"


            # Create and store the Label AST node.
            APPEND new Label(label_name)
            TO target.content



        # ------------------------------------------------
        # REFERENCE
        # ------------------------------------------------

        ELSE IF command == ref:

            # Choose the deepest active content container.
            target =
                current_environment
                OR current_subsection
                OR current_section


            IF target == NONE:

                ERROR "@ref must appear after @section"


            # Parse the target and optional visible text.
            values =
                PARSE_KEY_VALUES(argument)


            # Construct the Reference AST node.
            reference = new Reference(

                # Which label are we referencing?
                target = values["name"] OR argument,

                # What should the reader see?
                text = values["text"] OR ""

            )


            # Store the reference.
            APPEND reference
            TO target.content



        # ------------------------------------------------
        # ENVIRONMENT
        # ------------------------------------------------

        # Check whether the command is one of the
        # supported semantic environments:
        #
        # theorem
        # lemma
        # definition
        # proof
        # example
        # etc.
        ELSE IF command IS A KNOWN ENVIRONMENT:

            # Environments themselves live inside
            # sections or subsections.
            target =
                current_subsection
                OR current_section


            IF target == NONE:

                ERROR "environment must appear after @section"


            # Extract optional title and label.
            title, label =
                PARSE_TITLE_AND_LABEL(argument)


            # Create the semantic Environment node.
            environment = new Environment(

                # Store what kind of environment this is.
                kind = command,

                # Optional title.
                title = title,

                # Optional cross-reference label.
                label = label

            )


            # If no explicit title was given,
            # use the raw argument as the title.
            #
            # Proof is treated specially and does not
            # automatically receive the argument as a title.
            IF title is empty AND command != proof:

                environment.title = argument


            # Attach the environment to the section/subsection.
            APPEND environment
            TO target.content


            # From this point onward, new content is considered
            # part of this environment.
            current_environment = environment



        # ------------------------------------------------
        # LIST
        # ------------------------------------------------

        ELSE IF command == enumerate
             OR command == itemize:

            # Lists can be placed inside:
            #
            # environment
            # subsection
            # section
            target =
                current_environment
                OR current_subsection
                OR current_section


            IF target == NONE:

                ERROR "list must appear after @section"


            # Parse the list.
            #
            # enumerate = ordered list
            # itemize   = unordered list
            list = PARSE_LIST(

                argument,

                ordered = (command == enumerate)

            )


            # Add the ListBlock to the current content.
            APPEND list
            TO target.content



        # ------------------------------------------------
        # RELATED LINKS
        # ------------------------------------------------

        ELSE IF command == relatedlinks
             OR command == relatedlink:

            # Parse link properties.
            values =
                PARSE_KEY_VALUES(argument)


            # Every related link must have a destination.
            IF "href" NOT IN values:

                ERROR "@relatedlinks requires href"


            # Create the RelatedLink AST node.
            link = new RelatedLink(

                # Use a default name when necessary.
                name = values["name"] OR "Related link",

                # Destination URL.
                href = values["href"]

            )


            # Related links belong directly to the Document.
            APPEND link
            TO document.related_links



        # ------------------------------------------------
        # UNKNOWN COMMAND
        # ------------------------------------------------

        ELSE:

            # Anything that reached this point
            # was not recognized by the parser.
            ERROR "Unknown Mark Two directive"



        # Move to the first line after the complete directive.
        #
        # This matters because a directive may span many lines.
        # We do not want to process those lines again.
        index = end_index + 1



    # ------------------------------------------------
    # END OF SOURCE
    # ------------------------------------------------

    # If math_buffer still contains something,
    # the file ended before "\]" appeared.
    IF math_buffer IS NOT NONE:

        ERROR "Unclosed display math block"


    # The entire source has now been converted
    # into one complete Document AST.
    RETURN document
~~~