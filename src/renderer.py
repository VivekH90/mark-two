"""Render a Mark Two Document into the HTML template."""

from html import escape
from pathlib import Path
import colorsys
import re

from .ast import Document, Environment, Image, Label, ListBlock, MathBlock, Reference, Section, TextBlock

_CSS_COLOR_NAMES = {"black":"#000000","white":"#ffffff","red":"#ff0000","green":"#008000","blue":"#0000ff","yellow":"#ffff00","orange":"#ffa500","purple":"#800080","gray":"#808080","grey":"#808080","brown":"#a52a2a","pink":"#ffc0cb","teal":"#008080","navy":"#000080","maroon":"#800000","olive":"#808000","lime":"#00ff00","cyan":"#00ffff","magenta":"#ff00ff"}

def _dark_mode_color(value):
    original=value.strip(); raw=_CSS_COLOR_NAMES.get(original.lower(),original.lower()); match=re.fullmatch(r"#([0-9a-f]{6})",raw)
    if not match:return original
    r,g,b=[int(match.group(1)[i:i+2],16)/255 for i in (0,2,4)]; luminance=.2126*r+.7152*g+.0722*b
    if luminance>=.42:return f"#{round(r*255):02x}{round(g*255):02x}{round(b*255):02x}"
    hue,lightness,saturation=colorsys.rgb_to_hls(r,g,b); r,g,b=colorsys.hls_to_rgb(hue,max(lightness,.45),saturation); return f"#{round(r*255):02x}{round(g*255):02x}{round(b*255):02x}"

def _parse_ref_argument(argument):
    parts,current,quote,depth=[],[],None,0; escaped=False
    for char in argument:
        if escaped:escaped=False;current.append(char);continue
        if char=="\\":escaped=True;current.append(char);continue
        if char=='"':quote=None if quote else char
        elif quote is None:
            if char in "{[(":depth+=1
            elif char in "})]":depth=max(0,depth-1)
            elif char=="," and depth==0:parts.append("".join(current).strip());current=[];continue
        current.append(char)
    parts.append("".join(current).strip()); target=parts[0].strip('"\'') if parts else ""; custom=""
    for part in parts[1:]:
        if "=" in part:
            key,value=part.split("=",1)
            if key.strip().lower()=="text":custom=value.strip().strip('"\'')
    return target,custom

def _looks_like_url(target):return bool(re.match(r"^(?:https?://|/|(?:\.?\.?/)?[^#]+\.html(?:#.*)?$)",target,re.I)) or "#" in target

def _extract_inline_block(text,start):
    brace=text.find("{",start)
    if brace<0:return None,start
    depth,quote,escaped=0,None,False
    for index in range(brace,len(text)):
        char=text[index]
        if escaped:escaped=False;continue
        if char=="\\":escaped=True;continue
        if char=='"':quote=None if quote else char;continue
        if quote is None and char=="{":depth+=1
        elif quote is None and char=="}":
            depth-=1
            if depth==0:return text[brace+1:index],index+1
    return None,start

def _split_inline_color(argument):
    parts=_parse_ref_argument(argument)
    if parts[1]:return parts[0],parts[1]
    if "," in argument:
        color,content=argument.split(",",1);return color.strip().strip('"\''),content.strip()
    return "",argument

def _inline_text(text,references):
    html=[];index=0
    while index<len(text):
        if text.startswith("@ref{",index):
            body,end=_extract_inline_block(text,index+4)
            if body is not None:
                target,custom=_parse_ref_argument(body.strip());entry=references.get(target)
                if entry:href,label_text=entry
                else:href=target if _looks_like_url(target) else f"#{escape(target,quote=True)}";label_text=target
                cls="cross-reference"+("" if entry else " unresolved-reference");html.append(f'<a class="{cls}" href="{escape(href,quote=True)}">{_inline_text(custom or label_text,references)}</a>');index=end;continue
        matched=False
        for command in ("bold","italic","color"):
            prefix=f"@{command}{{"
            if text.startswith(prefix,index):
                body,end=_extract_inline_block(text,index+len(prefix)-1)
                if body is None:break
                if command=="bold":html.append(f"<strong>{_inline_text(body,references)}</strong>")
                elif command=="italic":html.append(f"<em>{_inline_text(body,references)}</em>")
                else:
                    color,content=_split_inline_color(body)
                    if color:
                        dark=_dark_mode_color(color);html.append(f'<span class="inline-color" style="color: {escape(color,quote=True)}; --inline-color-dark: {escape(dark,quote=True)};">{_inline_text(content,references)}</span>')
                    else:html.append(escape(body))
                index=end;matched=True;break
        if matched:continue
        html.append(escape(text[index]));index+=1
    return "".join(html)

def _paragraphs(lines,references):
    if not lines:return ""
    paragraphs=[];current=[]
    for line in lines:
        if line.strip():current.append(line.strip())
        elif current:paragraphs.append(" ".join(current));current=[]
    if current:paragraphs.append(" ".join(current))
    return "\n".join(f"<p>{_inline_text(p,references)}</p>" for p in paragraphs)

def _text_html(text,references):
    styles=[]
    if text.bold:styles.append("font-weight: 700")
    if text.italic:styles.append("font-style: italic")
    if text.color:styles.extend([f"color: {escape(text.color,quote=True)}",f"--text-color-dark: {escape(_dark_mode_color(text.color),quote=True)}"])
    style=f' style="{"; ".join(styles)}"' if styles else "";return f'<p class="mark-text"{style}>{_inline_text(text.text,references)}</p>'

def _math_html(math):return f'<div class="math-display">\\[{math.content}\\]</div>'

def _image_tag(image,extra_style=""):
    styles=[]
    if image.width:styles.append(f"width: {escape(image.width,quote=True)}")
    if image.height and image.height.lower()!="auto":styles.append(f"height: {escape(image.height,quote=True)}")
    if extra_style:styles.append(extra_style)
    style=f' style="{"; ".join(styles)}"' if styles else "";return f'<img src="{escape(image.src,quote=True)}" alt="{escape(image.alt,quote=True)}" loading="lazy"{style}>'

def _caption_html(caption,figure_number):return f'<figcaption><strong>Figure {figure_number}:</strong> {escape(caption)}</figcaption>'

def _image_html(image,figure_number):
    identifier=f' id="{escape(image.label,quote=True)}"' if image.label else "";html=[f'<figure class="article-image"{identifier}>',_image_tag(image)]
    if image.caption:html.append(_caption_html(image.caption,figure_number))
    html.append("</figure>");return "\n".join(html)

def _multi_image_html(images,figure_number):
    identifier=f' id="{escape(images[0].label,quote=True)}"' if images[0].label else "";widths=[i.width.strip() for i in images];explicit=[i for i,w in enumerate(widths) if w]
    if not explicit:columns=" ".join("minmax(0, 1fr)" for _ in images)
    elif len(explicit)==len(images):columns=" ".join(escape(w,quote=True) for w in widths)
    else:
        total=" + ".join(escape(widths[i],quote=True) for i in explicit);remaining=len(images)-len(explicit);columns=" ".join(escape(w,quote=True) if w else f"minmax(0, calc((100% - ({total}) - {10*(len(images)-1)}px) / {remaining}))" for w in widths)
    image_html=[]
    for image in images:
        extra=f"width: 100%; height: {escape(image.height,quote=True)}; object-fit: cover; margin: 0;" if image.height and image.height.lower()!="auto" else "width: 100%; height: auto; object-fit: contain; margin: 0;";image_html.append(_image_tag(image,extra))
    row_style=f"display: grid; grid-template-columns: {columns}; gap: 10px; align-items: start;";html=[f'<figure class="article-image multi-image"{identifier}>',f'<div class="image-row" style="{row_style}">',"\n".join(image_html),"</div>"]
    if images[0].caption:html.append(_caption_html(images[0].caption,figure_number))
    html.append("</figure>");return "\n".join(html)

def _list_html(list_block,environment_counters,references,figure_counter,depth):
    tag="ol" if list_block.ordered else "ul";type_attr=' type="a"' if list_block.ordered and depth>0 else "";color=escape(list_block.color,quote=True);dark=escape(_dark_mode_color(list_block.color),quote=True);items=[]
    for item in list_block.items:
        title=f'<span class="list-item-title">{escape(item.title)}</span>' if item.title else "";cls=' class="has-list-item-title"' if item.title else "";content=_content_html(item.content,environment_counters,references,figure_counter,depth+1);items.append(f"<li{cls}>{title}{content}</li>")
    return f'<{tag} class="mark-list"{type_attr} style="--list-color: {color}; --list-color-dark: {dark};">\n'+"\n".join(items)+f"\n</{tag}>"

def _environment_html(environment,number,environment_counters,references,figure_counter):
    kind=escape(environment.kind.lower());identifier=f' id="{escape(environment.label,quote=True)}"' if environment.label else "";content=_content_html(environment.content,environment_counters,references,figure_counter,0)
    if kind=="proof":return f'<div class="proof-environment"{identifier}><div class="proof-heading">Proof</div><div class="proof-content">{content}</div><div class="proof-qed" aria-label="Q.E.D.">□</div></div>'
    label=environment.kind.capitalize();heading=f'<span class="environment-label"><span class="environment-kind">{label}</span> <span class="environment-number">{number}</span></span>'
    if environment.title:heading+=f' <span class="environment-title">({escape(environment.title)})</span>'
    return f'<div class="math-environment {kind}"{identifier}><div class="environment-heading">{heading}</div><div class="environment-content">{content}</div></div>'

def _content_html(items,environment_counters,references,figure_counter,list_depth=0):
    html=[];index=0
    while index<len(items):
        item=items[index]
        if isinstance(item,Environment):environment_counters[item.kind]=environment_counters.get(item.kind,0)+1;html.append(_environment_html(item,environment_counters[item.kind],environment_counters,references,figure_counter))
        elif isinstance(item,Image):
            group=[item];next_index=index+1
            while next_index<len(items) and isinstance(items[next_index],Image) and items[next_index].group==item.group:group.append(items[next_index]);next_index+=1
            figure_counter["number"]+=1;html.append(_image_html(group[0],figure_counter["number"]) if len(group)==1 else _multi_image_html(group,figure_counter["number"]));index=next_index-1
        elif isinstance(item,MathBlock):html.append(_math_html(item))
        elif isinstance(item,TextBlock):html.append(_text_html(item,references))
        elif isinstance(item,ListBlock):html.append(_list_html(item,environment_counters,references,figure_counter,list_depth))
        elif isinstance(item,Label):html.append(f'<span class="mark-label" id="{escape(item.name,quote=True)}"></span>')
        elif isinstance(item,Reference):
            entry=references.get(item.target);href,label_text=entry if entry else (item.target if _looks_like_url(item.target) else f"#{escape(item.target,quote=True)}",item.target);text=item.text or label_text;html.append(f'<p><a class="cross-reference" href="{escape(href,quote=True)}">{escape(text)}</a></p>')
        else:html.append(_paragraphs([item],references))
        index+=1
    return "\n".join(html)

def _build_reference_index(document):
    references,counters={},{}
    for number,section in enumerate(document.sections,1):
        if section.label:references[section.label]=(f"#{section.slug or 'section'}",f"Section {number}")
        for sub_number,subsection in enumerate(section.subsections,1):
            if subsection.label:references[subsection.label]=(f"#{subsection.slug or 'subsection'}",f"Subsection {number}.{sub_number}")
        content=list(section.content)
        for subsection in section.subsections:content.extend(subsection.content)
        for item in content:
            if isinstance(item,Environment):
                counters[item.kind]=counters.get(item.kind,0)+1
                if item.label:references[item.label]=(f"#{item.label}",f"{item.kind.capitalize()} {counters[item.kind]}")
    return references

def _section_html(section,number,environment_counters,references,figure_counter):
    color=escape(section.color,quote=True);dark=escape(_dark_mode_color(section.color),quote=True);identifier=escape(section.slug or "section",quote=True);html=[f'<section class="article-section" id="{identifier}" style="--section-color: {color}; --section-color-dark: {dark};">',f'<h2><span class="section-symbol">§</span> {number}. {escape(section.title)}</h2>',_content_html(section.content,environment_counters,references,figure_counter)]
    for sub_number,subsection in enumerate(section.subsections,1):
        sub_identifier=escape(subsection.slug or "subsection",quote=True);html.extend([f'<section class="article-subsection" id="{sub_identifier}">',f'<h3>{number}.{sub_number}. {escape(subsection.title)}</h3>',_content_html(subsection.content,environment_counters,references,figure_counter),"</section>"])
    html.append("</section>");return "\n".join(html)

def render(document,template_path):
    template=Path(template_path).read_text(encoding="utf-8");buttons=[]
    for button in document.buttons:
        color=escape(button.color,quote=True);dark=escape(_dark_mode_color(button.color),quote=True);buttons.append(f'<a class="nav-button" href="{escape(button.href,quote=True)}" style="--button-color: {color}; --button-color-dark: {dark};">{escape(button.name)}</a>')
    if document.banner:
        banner_color=escape(document.banner_color or "#ffffff",quote=True);banner_dark=escape(_dark_mode_color(document.banner_color or "#ffffff"),quote=True);banner=f'<div class="site-banner"><img src="{escape(document.banner,quote=True)}" alt="" loading="eager"><a class="banner-title" href="#" style="color: {banner_color}; --banner-title-color: {banner_color}; --banner-title-color-dark: {banner_dark};">{escape(document.document_title)}</a></div>'
    else:banner=f'<a class="document-title" href="#">{escape(document.document_title)}</a>'
    references=_build_reference_index(document);toc=[];article=[];environment_counters={};figure_counter={"number":0}
    for number,section in enumerate(document.sections,1):
        toc.append(f'<li><a href="#{escape(section.slug or "section")}"><span class="toc-section-symbol">§</span> {number}. {escape(section.title)}</a>')
        if section.subsections:
            toc.append('<ol class="toc-subsections">')
            for sub_number,subsection in enumerate(section.subsections,1):toc.append(f'<li><a href="#{escape(subsection.slug or "subsection")}">{number}.{sub_number}. {escape(subsection.title)}</a></li>')
            toc.append('</ol>')
        toc.append('</li>');article.append(_section_html(section,number,environment_counters,references,figure_counter))
    related=[f'<li><a href="{escape(link.href,quote=True)}" target="_blank" rel="noopener noreferrer">{escape(link.name)}</a></li>' for link in document.related_links]
    replacements={"{{DOCUMENT_TITLE}}":escape(document.document_title),"{{ARTICLE_TITLE}}":escape(document.article_title),"{{BANNER}}":banner,"{{BUTTONS}}":"\n".join(buttons),"{{TOC}}":"\n".join(toc),"{{ARTICLE}}":"\n".join(article),"{{RELATED_LINKS}}":"\n".join(related)}
    for key,value in replacements.items():template=template.replace(key,value)
    return template
