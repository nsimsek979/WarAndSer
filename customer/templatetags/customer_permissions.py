from django import template
from customer.views import can_user_edit_customer

register = template.Library()

@register.filter
def can_edit_customer(user, company):
    """
    Template filter to check if user can edit the given customer company.
    Usage: {% if user|can_edit_customer:company %}
    """
    return can_user_edit_customer(user, company)
