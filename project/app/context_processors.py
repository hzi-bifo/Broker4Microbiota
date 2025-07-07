from django.core.cache import cache
from .models import SiteSettings
import os
from django.conf import settings as django_settings


def site_settings(request):
    """
    Context processor to inject site settings into all templates.
    Uses caching to avoid database queries on every request.
    """
    # Try to get settings from cache first
    cached_settings = cache.get('site_settings')
    
    if cached_settings is None:
        # Get settings from database
        try:
            site_settings_obj = SiteSettings.get_settings()
            
            # Prepare settings dictionary
            cached_settings = {
                'site_name': site_settings_obj.site_name,
                'organization_name': site_settings_obj.organization_name,
                'organization_short_name': site_settings_obj.organization_short_name,
                'tagline': site_settings_obj.tagline,
                'contact_email': site_settings_obj.contact_email,
                'website_url': site_settings_obj.website_url,
                'primary_color': site_settings_obj.primary_color,
                'secondary_color': site_settings_obj.secondary_color,
                'footer_text': site_settings_obj.footer_text,
                'logo_url': site_settings_obj.logo.url if site_settings_obj.logo else None,
                'favicon_url': site_settings_obj.favicon.url if site_settings_obj.favicon else None,
            }
            
            # Add default logo fallback
            if not cached_settings['logo_url']:
                # Use the existing static logo as fallback
                cached_settings['logo_url'] = os.path.join(django_settings.STATIC_URL, 'images/logo.png')
            
            # Cache for 5 minutes
            cache.set('site_settings', cached_settings, 300)
            
        except Exception as e:
            # If something goes wrong, provide defaults
            cached_settings = {
                'site_name': 'Sequencing Order Management',
                'organization_name': 'Helmholtz Centre for Infection Research',
                'organization_short_name': 'HZI',
                'tagline': 'Streamlining sequencing requests and ensuring compliance with MIxS standards',
                'contact_email': 'sequencing@helmholtz-hzi.de',
                'website_url': 'https://www.helmholtz-hzi.de',
                'primary_color': '#3273dc',
                'secondary_color': '#2366d1',
                'footer_text': '',
                'logo_url': os.path.join(django_settings.STATIC_URL, 'images/logo.png'),
                'favicon_url': None,
            }
    
    return {'site_settings': cached_settings}


def clear_site_settings_cache():
    """
    Clear the site settings cache.
    Call this when settings are updated.
    """
    cache.delete('site_settings')