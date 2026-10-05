"""Archive page generation for Mark Two projects."""
from __future__ import annotations
from html import escape
from pathlib import Path
from .homepage import _load_articles, _sort_key, _display_date, _description, _article_url, _slug
from .site_config import find_project_root, load_config
DEFAULT_TEMPLATE=Path(__file__).resolve().parent.parent/"web"/"archive.html"
def _render_rows(articles):
    groups={}
    for article in articles:
        date,year=_display_date(article.get("date")); year=year or "Other"
        subject=str(article.get("subject") or article.get("folder") or "Article")
        tags=article.get("tags",[]); tags=tags if isinstance(tags,list) else []
        search=escape(" ".join([str(article.get("title","")),_description(article),subject,str(article.get("folder",""))," ".join(map(str,tags))]),quote=True)
        tag_data="|".join(escape(_slug(str(t)),quote=True) for t in tags)
        row=(f'<div class="archive-row" data-tags="{tag_data}" data-search="{search}"><time>{escape(date)}</time>'
             f'<a href="{escape(_article_url(article),quote=True)}">{escape(str(article.get("title") or "Untitled"))}</a>'
             f'<span class="description">{escape(_description(article))}</span><span class="category">{escape(subject)}</span></div>')
        groups.setdefault(year,[]).append(row)
    out=[]
    for year in sorted(groups,reverse=True):
        out.append(f'<h2 class="year">{escape(year)}</h2>'); out.extend(groups[year])
    return "\n".join(out) or '<p class="empty">No articles found.</p>'
def build_archive(root=".",output=None,template=None):
    root=find_project_root(root); config=load_config(root); articles=sorted(_load_articles(root),key=_sort_key,reverse=True)
    template_path=Path(template).resolve() if template else DEFAULT_TEMPLATE.resolve()
    output_path=Path(output).resolve() if output else root/"archive"/"index.html"
    repl={"SITE_TITLE":escape(str(config.get("title") or "Notes")),"AUTHOR":escape(str(config.get("author") or "Author")),
          "GITHUB_URL":escape(str(config.get("github") or "#"),quote=True),"ABOUT_URL":escape(str(config.get("about") or "#"),quote=True),
          "HOME_URL":"/","ARCHIVE_URL":escape(str(config.get("archive") or "/archive/"),quote=True),"ARCHIVE_ROWS":_render_rows(articles)}
    html=template_path.read_text(encoding="utf-8")
    for k,v in repl.items(): html=html.replace("{{"+k+"}}",v)
    output_path.parent.mkdir(parents=True,exist_ok=True); output_path.write_text(html,encoding="utf-8"); return output_path
