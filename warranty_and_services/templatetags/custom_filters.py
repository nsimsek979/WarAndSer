from django import template
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from django.urls import reverse
import json

register = template.Library()


@register.filter
def humanize_number(value):
    """Format number with thousand separators"""
    try:
        return f"{int(value):,}".replace(',', '.')
    except (ValueError, TypeError):
        return value


@register.filter
def get_item(dictionary, key):
    """Get item from dictionary by key"""
    if dictionary and hasattr(dictionary, 'get'):
        return dictionary.get(key)
    return None


@register.filter
def multiply(value, arg):
    """Multiply value by argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def divide(value, arg):
    """Divide value by argument"""
    try:
        if float(arg) == 0:
            return 0
        return float(value) / float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def percentage(value, total):
    """Calculate percentage"""
    try:
        if float(total) == 0:
            return 0
        return round((float(value) / float(total)) * 100, 1)
    except (ValueError, TypeError):
        return 0


@register.filter
def currency(value):
    """Format value as Turkish Lira"""
    try:
        return f"{float(value):,.2f} ₺"
    except (ValueError, TypeError):
        return "0,00 ₺"


@register.filter
def status_badge(status):
    """Return Bootstrap badge HTML for status"""
    status_mapping = {
        'active': {'class': 'badge-success', 'text': 'Aktif'},
        'inactive': {'class': 'badge-secondary', 'text': 'Pasif'},
        'pending': {'class': 'badge-warning', 'text': 'Bekliyor'},
        'completed': {'class': 'badge-success', 'text': 'Tamamlandı'},
        'cancelled': {'class': 'badge-danger', 'text': 'İptal'},
        'expired': {'class': 'badge-danger', 'text': 'Süresi Doldu'},
        'expiring_soon': {'class': 'badge-warning', 'text': 'Süresi Yaklaşıyor'},
        'overdue': {'class': 'badge-danger', 'text': 'Gecikmiş'},
        'due_soon': {'class': 'badge-warning', 'text': 'Yaklaşan'},
    }
    
    config = status_mapping.get(status, {'class': 'badge-secondary', 'text': status})
    return format_html(
        '<span class="badge {}">{}</span>',
        config['class'],
        config['text']
    )


@register.filter
def warranty_status(warranty):
    """Get warranty status based on end date"""
    from datetime import datetime
    
    if not warranty or not warranty.end_of_warranty_date:
        return 'unknown'
    
    now = datetime.now()
    end_date = warranty.end_of_warranty_date.replace(tzinfo=None)
    
    if end_date < now:
        return 'expired'
    elif (end_date - now).days <= 30:
        return 'expiring_soon'
    else:
        return 'active'


@register.filter
def service_status(service):
    """Get service status based on next service date and completion"""
    from datetime import datetime
    
    if not service:
        return 'unknown'
    
    if service.is_completed:
        return 'completed'
    
    if not service.next_service_date:
        return 'pending'
    
    now = datetime.now()
    service_date = service.next_service_date.replace(tzinfo=None)
    
    if service_date < now:
        return 'overdue'
    elif (service_date - now).days <= 7:
        return 'due_soon'
    else:
        return 'pending'


@register.filter
def days_until(date_value):
    """Calculate days until a date"""
    from datetime import datetime
    
    if not date_value:
        return None
    
    now = datetime.now()
    target_date = date_value.replace(tzinfo=None) if hasattr(date_value, 'replace') else date_value
    
    delta = target_date - now
    return delta.days


@register.filter
def abs_value(value):
    """Return absolute value"""
    try:
        return abs(float(value))
    except (ValueError, TypeError):
        return 0


@register.filter
def truncate_words(value, length):
    """Truncate text to specified word count"""
    if not value:
        return ""
    
    words = str(value).split()
    if len(words) <= length:
        return value
    
    return " ".join(words[:length]) + "..."


@register.filter
def json_encode(value):
    """Convert value to JSON string"""
    try:
        return json.dumps(value)
    except (TypeError, ValueError):
        return "{}"


@register.filter
def add_class(field, css_class):
    """Add CSS class to form field"""
    if hasattr(field, 'as_widget'):
        return field.as_widget(attrs={'class': css_class})
    return field


@register.filter
def placeholder(field, placeholder_text):
    """Add placeholder to form field"""
    if hasattr(field, 'as_widget'):
        return field.as_widget(attrs={'placeholder': placeholder_text})
    return field


@register.simple_tag
def url_replace(request, field, value):
    """Replace URL parameter while keeping others"""
    dict_ = request.GET.copy()
    dict_[field] = value
    return dict_.urlencode()


@register.simple_tag
def active_link(request, url_name, css_class="active"):
    """Return CSS class if current URL matches url_name"""
    from django.urls import resolve, reverse, NoReverseMatch
    
    try:
        current_url = resolve(request.path_info).url_name
        target_url = url_name
        
        if current_url == target_url:
            return css_class
    except:
        pass
    
    return ""


@register.inclusion_tag('components/pagination.html', takes_context=True)
def paginate(context, page_obj, pagination_url=None):
    """Render pagination component"""
    return {
        'page_obj': page_obj,
        'request': context['request'],
        'pagination_url': pagination_url,
    }


@register.filter
def model_name(obj):
    """Get model name of an object"""
    return obj._meta.model_name if hasattr(obj, '_meta') else str(type(obj).__name__).lower()


@register.filter
def verbose_name(obj):
    """Get verbose name of a model"""
    return obj._meta.verbose_name if hasattr(obj, '_meta') else str(type(obj).__name__)


@register.filter
def field_verbose_name(obj, field_name):
    """Get verbose name of a model field"""
    if hasattr(obj, '_meta'):
        try:
            field = obj._meta.get_field(field_name)
            return field.verbose_name
        except:
            pass
    return field_name


@register.filter
def has_permission(user, permission):
    """Check if user has specific permission"""
    if not user or not user.is_authenticated:
        return False
    return user.has_perm(permission)


@register.filter
def company_hierarchy_level(company, user_company):
    """Get company hierarchy level relative to user company"""
    if not company or not user_company:
        return 0
    
    if company == user_company:
        return 0
    elif company.related_company == user_company:
        return 1
    elif company.related_company and company.related_company.related_company == user_company:
        return 2
    else:
        return -1


@register.filter
def bootstrap_alert_class(message_tag):
    """Convert Django message tag to Bootstrap alert class"""
    mapping = {
        'debug': 'alert-info',
        'info': 'alert-info',
        'success': 'alert-success',
        'warning': 'alert-warning',
        'error': 'alert-danger',
    }
    return mapping.get(message_tag, 'alert-info')
