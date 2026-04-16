from django import template

register = template.Library()

@register.inclusion_tag('mail/tags/logo.html')
def logo_elem():
    return { }

@register.inclusion_tag('mail/tags/title.html')
def title_elem(title: str):
    return { 'text': title }

@register.inclusion_tag('mail/tags/image.html')
def image_elem(src: str):
    return { 'image_src': src }

@register.inclusion_tag('mail/tags/paragraph.html')
def paragraph_elem(text: str):
    return { 'text': text }

@register.inclusion_tag('mail/tags/subtitle.html')
def subtitle_elem(text: str):
    return { 'text': text }

@register.inclusion_tag('mail/tags/button.html')
def button_elem(text: str, href: str):
    return { 'text': text, 'href': href }

@register.inclusion_tag('mail/tags/meta_text.html')
def meta_elem(text: str):
    return { 'text': text }

@register.inclusion_tag('mail/tags/code.html')
def code_elem(text: str):
    return { 'text': text }


