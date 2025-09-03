from translations import TRANSLATIONS, get_translation

def translations(request):
    """Add translation function to template context"""
    current_language = request.LANGUAGE_CODE if hasattr(request, 'LANGUAGE_CODE') else 'en'
    
    # Extract language from URL path
    path_parts = request.path.strip('/').split('/')
    if path_parts and path_parts[0] in ['en', 'fr', 'ar']:
        current_language = path_parts[0]
    else:
        current_language = 'en'
    
    def trans(text):
        return get_translation(text, current_language)
    
    return {
        'trans': trans,
        'current_language': current_language,
        'LANGUAGE_CODE': current_language,
    }