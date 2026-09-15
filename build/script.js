"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const toggle = document.querySelector(".sidebar-toggle");
    const toc = document.querySelector(".toc");

    if (toggle && toc) {
        toggle.addEventListener("click", () => {
            const collapsed = toc.classList.toggle("collapsed");
            toggle.setAttribute("aria-expanded", String(!collapsed));
        });
    }

    const themeToggle = document.querySelector(".theme-toggle");
    const themeIcon = themeToggle?.querySelector(".theme-icon");
    const themeLabel = themeToggle?.querySelector(".theme-label");

    const applyTheme = (dark) => {
        document.documentElement.classList.toggle("dark-mode", dark);
        themeToggle?.setAttribute("aria-pressed", String(dark));
        themeToggle?.setAttribute("aria-label", dark ? "Disable dark mode" : "Enable dark mode");
        if (themeIcon) themeIcon.textContent = dark ? "☀" : "☾";
        if (themeLabel) themeLabel.textContent = dark ? "Light Mode" : "Dark Mode";
    };

    if (themeToggle) {
        const savedTheme = localStorage.getItem("mark-two-theme");
        applyTheme(savedTheme === "dark");

        themeToggle.addEventListener("click", () => {
            const dark = !document.documentElement.classList.contains("dark-mode");
            applyTheme(dark);
            localStorage.setItem("mark-two-theme", dark ? "dark" : "light");
        });
    }

    const tocLinks = [...document.querySelectorAll(".toc a")];
    const headings = tocLinks
        .map((link) => document.getElementById(link.getAttribute("href")?.slice(1)))
        .filter(Boolean);

    if ("IntersectionObserver" in window && headings.length) {
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (!entry.isIntersecting) return;
                    tocLinks.forEach((link) => link.classList.remove("active"));
                    const active = document.querySelector(
                        `.toc a[href="#${CSS.escape(entry.target.id)}"]`
                    );
                    active?.classList.add("active");
                });
            },
            { rootMargin: "-15% 0px -70% 0px" }
        );

        headings.forEach((heading) => observer.observe(heading));
    }
});
