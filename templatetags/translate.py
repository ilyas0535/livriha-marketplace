from django import template
from translations import get_translation

register = template.Library()

@register.simple_tag(takes_context=True)
def t(context, text):
    """Simple translation tag"""
    request = context.get('request')
    if request:
        path_parts = request.path.strip('/').split('/')
        if path_parts and path_parts[0] in ['en', 'fr', 'ar']:
            language = path_parts[0]
        else:
            language = 'en'
    else:
        language = 'en'
    
    return get_translation(text, language)