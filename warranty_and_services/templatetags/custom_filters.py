from django import template
from django.utils.translation import gettext as _
import re

register = template.Library()

@register.filter
def humanize_number(value):
    """
    Sayıları noktalarla gruplar (örn: 3000 -> 3.000)
    """
    if value is None:
        return value
    
    try:
        # Sayıyı string'e çevir
        num_str = str(int(value))
        
        # Üç hanede bir nokta ekle (sağdan sola)
        # 1234567 -> 1.234.567
        result = ""
        for i, digit in enumerate(reversed(num_str)):
            if i > 0 and i % 3 == 0:
                result = "." + result
            result = digit + result
        
        return result
    except (ValueError, TypeError):
        return value

@register.filter
def remove_time_from_text(value):
    """
    Virgülden sonra gelen saat bilgilerini kaldırır
    Örn: "Pazartesi, 14:30" -> "Pazartesi"
    """
    if not value:
        return value
    
    # Virgül varsa, virgülden sonrasını kes
    if ',' in str(value):
        return str(value).split(',')[0]
    
    return value

@register.filter
def date_no_time(value):
    """
    Tarih formatından saat bilgisini kaldırır
    """
    if not value:
        return value
    
    try:
        # Eğer datetime objesi ise, sadece tarihi döndür
        if hasattr(value, 'date'):
            return value.date()
        return value
    except:
        return value

@register.filter
def format_hour_display(value, unit_type):
    """
    Saat değerlerini formatlar (3000 saat -> 3.000 saat)
    """
    if not value:
        return value
        
    try:
        # Sadece saat türündeki değerleri formatla
        if unit_type == 'hour_term' or 'saat' in str(value).lower():
            # Sayısal değeri çıkar
            import re
            numbers = re.findall(r'\d+', str(value))
            if numbers:
                number = int(numbers[0])
                formatted_number = humanize_number(number)
                # "saat" kelimesini koru
                if 'saat' in str(value).lower():
                    return f"{formatted_number} saat"
                else:
                    return formatted_number
        
        return value
    except:
        return value
