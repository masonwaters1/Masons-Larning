import markdown as md
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name="markdownify")
def markdownify(text):
    if not text:
        return ""
    html = md.markdown(
        text,
        extensions=["footnotes", "tables", "smarty", "attr_list", "sane_lists"],
        extension_configs={"footnotes": {"BACKLINK_TEXT": "&#8617;"}},
    )
    return mark_safe(html)


@register.filter(name="reading_time")
def reading_time(text):
    if not text:
        return 0
    words = len(text.split())
    return max(1, round(words / 220))
