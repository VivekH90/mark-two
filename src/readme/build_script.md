# Script

The `script.js` file provides the small interactive behaviors used by the generated Mark Two pages.

The compiler generates the HTML structure.

The JavaScript does not generate the document.

It only adds interactive behavior after the page has loaded.

---

## Main Execution

1. Register a `DOMContentLoaded` event listener.

2. Wait until the HTML document has been completely loaded.

3. When the event fires, begin initializing the Mark Two frontend behavior.

---

## Sidebar / Table of Contents Toggle

1. Find the element with the class:

       `.sidebar-toggle`

   Store it as `toggle`.

2. Find the element with the class:

       `.toc`

   Store it as `toc`.

3. Check whether both `toggle` and `toc` exist.

4. If both elements exist:

   a. Add a `click` event listener to `toggle`.

   b. When the toggle is clicked:

      i. Toggle the `collapsed` class on `toc`.

      ii. Store the result of the toggle operation in:

             collapsed

      iii. `collapsed = true` means the table of contents is now collapsed.

      iv. `collapsed = false` means the table of contents is now expanded.

      v. Convert the inverse of `collapsed` to a string.

      vi. Set the `aria-expanded` attribute of the toggle to that value.

   Therefore:

       collapsed = true
           ↓
       aria-expanded = "false"

       collapsed = false
           ↓
       aria-expanded = "true"

---

## Theme Toggle Setup

1. Find the element with the class:

       `.theme-toggle`

   Store it as `themeToggle`.

2. Search inside `themeToggle` for:

       `.theme-icon`

   Store it as `themeIcon`.

3. Search inside `themeToggle` for:

       `.theme-label`

   Store it as `themeLabel`.

4. Define a function called `applyTheme(dark)`.

   This function applies either dark mode or light mode to the document.

---

## `applyTheme(dark)` Function

1. Receive a boolean called `dark`.

2. Toggle the `dark-mode` class on the root HTML element.

   Specifically:

       document.documentElement

3. Set the `dark-mode` class according to `dark`.

   a. If `dark = true`:

          add `dark-mode`

   b. If `dark = false`:

          remove `dark-mode`

4. Set the root element's `colorScheme`.

   a. If `dark = true`:

          colorScheme = "dark"

   b. Otherwise:

          colorScheme = "light"

5. If `themeToggle` exists:

   a. Set its `aria-pressed` attribute.

   b. Use:

          "true"

      when dark mode is active.

   c. Use:

          "false"

      when dark mode is inactive.

6. If `themeToggle` exists:

   a. Set its `aria-label`.

   b. When dark mode is active, use:

          "Disable dark mode"

   c. When dark mode is inactive, use:

          "Enable dark mode"

7. If `themeIcon` exists:

   a. When dark mode is active:

          set its text to `☀`

   b. Otherwise:

          set its text to `☾`

8. If `themeLabel` exists:

   a. When dark mode is active:

          set its text to `"Light Mode"`

   b. Otherwise:

          set its text to `"Dark Mode"`

9. The page is now visually and semantically synchronized with the requested theme.

---

## Initial Theme Setup

1. Check whether `themeToggle` exists.

2. If it does:

   a. Read the saved theme from `localStorage` using the key:

          `mark-two-theme-v2`

   b. Store the returned value in:

          `savedTheme`

3. Check whether:

       savedTheme === "dark"

4. Pass this boolean to `applyTheme()`.

5. Therefore:

   a. If `localStorage` contains:

          mark-two-theme-v2 = "dark"

      then:

          applyTheme(true)

   b. For any other value, including no saved value:

          applyTheme(false)

   c. The initial default is therefore light mode.

---

## Theme Toggle Click

1. Add a `click` event listener to `themeToggle`.

2. When the theme toggle is clicked:

   a. Check whether the root HTML element currently has:

          `dark-mode`

   b. Negate that result.

   c. Store the new state in:

          `dark`

3. Pass `dark` to:

       applyTheme(dark)

4. Save the new theme state to `localStorage`.

5. Use the key:

       `mark-two-theme-v2`

6. Store:

       `"dark"`

   when `dark = true`.

7. Store:

       `"light"`

   when `dark = false`.

8. The selected theme is therefore preserved across page reloads.

---

## Table of Contents Active Entry

1. Select every link inside `.toc`.

       document.querySelectorAll(".toc a")

2. Convert the resulting collection into an array.

3. Store the array as:

       `tocLinks`

4. For every TOC link:

   a. Read its `href` attribute.

   b. Remove the first character from the `href`.

   c. This removes the `#` from fragment links.

   d. Use the resulting ID with:

          document.getElementById()

   e. Store the corresponding heading element.

5. Remove any links whose corresponding heading element does not exist.

6. Store the resulting heading elements as:

       `headings`

7. The `headings` array therefore contains the article elements referenced by the table of contents.

---

## Intersection Observer Setup

1. Check whether the browser provides:

       `IntersectionObserver`

2. Also check whether at least one heading exists.

3. Only continue with active-heading tracking when both conditions are true.

4. Create a new `IntersectionObserver`.

5. Give the observer a callback that receives:

       `entries`

6. Process every entry in `entries`.

7. For each `entry`:

   a. Check whether:

          `entry.isIntersecting`

   b. If it is `false`:

      i. Ignore this entry.

      ii. Return immediately for this iteration.

   c. If it is `true`:

      i. Remove the `active` class from every TOC link.

      ii. Read the ID of the heading currently intersecting the observer.

      iii. Escape that ID using:

             `CSS.escape()`

      iv. Construct a TOC selector of the form:

             `.toc a[href="#<heading-id>"]`

      v. Find the corresponding TOC link.

      vi. If that link exists, add:

             `active`

          to its class list.

8. Therefore, whenever a tracked heading enters the observer's active region:

       current active TOC link
               ↓
       remove `active`
               ↓
       find TOC link for current heading
               ↓
       add `active`

---

## Intersection Observer Region

1. Configure the observer with:

       rootMargin: "-15% 0px -70% 0px"

2. This modifies the observer's effective visible region.

3. The observer therefore does not simply react to an element entering the literal browser viewport.

4. Instead, it uses the configured top and bottom margins to determine when a heading counts as the currently visible section.

---

## Start Observing Headings

1. Iterate through every element in `headings`.

2. For each heading:

       observer.observe(heading)

3. The observer now monitors all headings referenced by the table of contents.

4. As the user scrolls through the article:

   a. headings enter or leave the observer region.

   b. `IntersectionObserver` produces entries.

   c. The callback determines which heading is currently intersecting.

   d. The corresponding TOC link receives the `active` class.

---

# Overall Flow

1. Wait for the HTML document to finish loading.

2. Find the sidebar toggle.

3. If the sidebar toggle and TOC exist:

   a. Attach a click handler.

   b. Toggle the TOC's `collapsed` class.

   c. Update `aria-expanded`.

4. Find the theme toggle and its icon and label.

5. Define `applyTheme()`.

6. If the theme toggle exists:

   a. Read the saved theme from `localStorage`.

   b. Apply the saved theme.

   c. Attach a click handler.

7. When the theme button is clicked:

   a. Determine the opposite of the current theme.

   b. Apply it.

   c. Save it to `localStorage`.

8. Find all TOC links.

9. Resolve each TOC link to its corresponding article heading.

10. Remove links whose target headings do not exist.

11. Check whether `IntersectionObserver` is supported.

12. If it is supported and headings exist:

   a. Create an observer.

   b. Observe every heading.

   c. When a heading becomes intersecting:

      i. Remove `active` from all TOC links.

      ii. Find the TOC link targeting that heading.

      iii. Add `active` to that link.

13. Finish initialization.

---

# Complete Frontend Flow

```text
DOMContentLoaded
       ↓
initialize sidebar toggle
       ↓
initialize theme system
       ↓
read saved theme
       ↓
apply saved theme
       ↓
initialize table of contents
       ↓
map TOC links → article headings
       ↓
create IntersectionObserver
       ↓
observe headings
       ↓
user scrolls
       ↓
heading enters observer region
       ↓
remove active from TOC links
       ↓
activate matching TOC link