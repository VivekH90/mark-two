"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const headings = document.querySelectorAll("#article h2, #article h3");
    const lists = [
        document.getElementById("toc-desktop"),
        document.getElementById("toc-mobile")
    ].filter(Boolean);

    const links = [];

    lists.forEach((root) => {
        const ul = document.createElement("ul");

        headings.forEach((heading) => {
            const li = document.createElement("li");
            if (heading.tagName === "H3") li.className = "sub";

            const a = document.createElement("a");
            a.href = "#" + heading.id;
            a.textContent = heading.textContent
                .replace(/^§\s*\d+\s*/, "")
                .replace(/^\d+(?:\.\d+)?\.?\s*/, "")
                .trim();

            li.appendChild(a);
            ul.appendChild(li);
            links.push(a);
        });

        root.replaceChildren(ul);
    });

    const byId = {};
    links.forEach((link) => {
        const id = link.getAttribute("href").slice(1);
        (byId[id] ??= []).push(link);
    });

    if ("IntersectionObserver" in window) {
        const observer = new IntersectionObserver(
            (entries) => {
                entries.forEach((entry) => {
                    if (!entry.isIntersecting) return;
                    links.forEach((link) => link.classList.remove("active"));
                    (byId[entry.target.id] || []).forEach((link) => {
                        link.classList.add("active");
                    });
                });
            },
            { rootMargin: "-15% 0px -70% 0px" }
        );

        headings.forEach((heading) => observer.observe(heading));
    }

    const mobileDetails = document.querySelector(".side-mobile");
    if (mobileDetails) {
        mobileDetails.addEventListener("toggle", () => {
            if (!mobileDetails.open) return;
            mobileDetails.scrollIntoView({ block: "nearest", behavior: "smooth" });
        });
    }
});