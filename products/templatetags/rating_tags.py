from django import template

register = template.Library()

@register.filter
def stars_range(rating):
    """Return range for displaying stars based on rating"""
    rating = float(rating) if rating else 0
    full_stars = int(rating)
    return range(1, 6), full_stars

@register.inclusion_tag('partials/stars.html')
def show_stars(rating, count=None):
    """Display star rating"""
    rating = float(rating) if rating else 0
    full_stars = int(round(rating))
    return {
        'full_stars': full_stars,
        'rating': rating,
        'count': count
    }