# Main

## `compile_document()` Function

1. Receive three paths:

   - `source_path`
   - `output_path`
   - `template_path`

2. Convert `source_path` into a `Path` object.

3. Resolve `source_path` into an absolute path.

4. Convert `output_path` into a `Path` object.

5. Resolve `output_path` into an absolute path.

6. Convert `template_path` into a `Path` object.

7. Resolve `template_path` into an absolute path.

8. Parse the Mark Two source file:

       document = parse_file(source_path)

   This reads the source file and converts it into the Mark Two `Document`
   structure.

9. Ensure that the directory containing the output file exists.

       output_path.parent.mkdir(
           parents=True,
           exist_ok=True
       )

   a. Create all missing parent directories.

   b. If the directory already exists, do nothing.

10. Render the parsed document using the selected HTML template:

        output = render(document, template_path)

    This converts the `Document` AST into the final HTML string.

11. Write the generated HTML to `output_path`.

        output_path.write_text(
            output,
            encoding="utf-8"
        )

12. Determine the directory containing the template:

        asset_dir = template_path.parent

13. Create the list of required web assets:

        style.css
        script.js

14. Process each required asset one at a time.

    For each `asset_name`:

    a. Construct the source asset path:

           source_asset = asset_dir / asset_name

    b. Check whether `source_asset` is actually a file.

    c. If it is not a file:

       i. Raise:

              "Required template asset not found: <source_asset>"

       ii. Stop compilation.

    d. If the file exists:

       i. Copy it into the same directory as the generated HTML.

       ii. Use `shutil.copy2()` so that the file is copied together
           with its metadata.

15. After the HTML and both assets have been successfully written:

    a. Return `output_path`.

---

## `main()` Function

1. Determine the root directory of the Mark Two repository.

       mark_two_root = Path(__file__).resolve().parent.parent

   a. `__file__` refers to `src/main.py`.

   b. `Path(__file__).resolve()` gives the absolute path to `main.py`.

   c. `.parent` moves to the `src` directory.

   d. `.parent.parent` moves to the root directory of the Mark Two repository.

2. Construct the path to Mark Two's built-in HTML template:

       default_template = mark_two_root / "web" / "index.html"

3. Create an `ArgumentParser`.

       parser = argparse.ArgumentParser(...)

4. Set the parser description to:

       "Compile a Mark Two article to a self-contained HTML bundle."

5. Add the required positional argument:

       source

   Its purpose is:

       "Path to the Mark Two source file"

6. Add the optional output argument:

       -o
       --output

   Its purpose is to specify the output HTML path.

7. The help text for `--output` states that the default is:

       index.html beside the source file

8. Add the optional template argument:

       --template

9. Set the default value of `--template` to `default_template`.

10. The help text for `--template` states that the default is
    Mark Two's built-in template.

11. Parse the command-line arguments:

        args = parser.parse_args()

12. Convert the supplied source path into an absolute path:

        source_path = Path(args.source).resolve()

13. Determine the output path.

    a. Check whether `args.output` was supplied.

    b. If `args.output` exists:

       i. Convert it to a `Path`.

       ii. Resolve it into an absolute path.

    c. If `args.output` was not supplied:

       i. Use the source file's parent directory.

       ii. Set the output filename to:

              index.html

    Therefore:

        output_path =
            resolved user output path

        or

        source_path.parent / "index.html"

14. Call `compile_document()` using:

        source_path
        output_path
        args.template

15. Store the returned output path:

        output_path = compile_document(...)

16. Print a message telling the user where the generated HTML was written:

        "Mark Two: wrote <output_path>"

17. Print another message telling the user where the assets were copied:

        "Mark Two: assets copied to <output_path.parent>"

---

## Module Entry Point

1. Check whether `main.py` is being executed directly:

       if __name__ == "__main__":

2. If it is being executed directly:

    a. Call:

           main()

3. If `main.py` is imported by another Python module:

    a. Do not call `main()` automatically.

---

# Overall Flow

1. The user runs the Mark Two command from the terminal.

2. `main()` starts.

3. Determine the root directory of the Mark Two installation.

4. Determine the default HTML template:

       web/index.html

5. Create the command-line argument parser.

6. Define:

   - the required Mark Two source file
   - the optional output HTML path
   - the optional HTML template path

7. Read the command-line arguments.

8. Convert the source path into an absolute path.

9. Determine the output path.

10. If the user did not specify an output path:

        use:
        <source directory>/index.html

11. Pass the source, output, and template paths to
    `compile_document()`.

12. `compile_document()` resolves all three paths.

13. Parse the `.mt` source file using:

        parse_file()

14. This produces a `Document` AST.

15. Render the `Document` using:

        render()

16. This produces the final HTML document.

17. Create the output directory when necessary.

18. Write the generated HTML to the output file.

19. Locate `style.css` and `script.js` beside the selected template.

20. Check that `style.css` exists.

21. Check that `script.js` exists.

22. If either required asset is missing:

        raise FileNotFoundError

23. Otherwise copy both assets into the output directory.

24. Return the final output path.

25. `main()` prints:

        Mark Two: wrote <output_path>

26. `main()` prints:

        Mark Two: assets copied to <output_directory>

27. Compilation is complete.

---

# Complete Pipeline

```text
Mark Two source file (.mt)
        ↓
main()
        ↓
read command-line arguments
        ↓
determine source/output/template paths
        ↓
compile_document()
        ↓
parse_file()
        ↓
Document AST
        ↓
render()
        ↓
generated HTML
        ↓
write index.html
        ↓
copy style.css
        ↓
copy script.js
        ↓
self-contained web bundle