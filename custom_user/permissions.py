from django.db import models

def get_company_queryset_for_user(user, base_queryset=None):
    """
    Returns a queryset of companies the user is allowed to see.
    """
    if base_queryset is None:
        from customer.models import Company
        base_queryset = Company.objects.all()

    if not user.is_authenticated:
        return base_queryset.none()

    role = getattr(user, 'role', None)
    if role == 'manager_main':
        # Main company manager: see all
        return base_queryset
    elif role == 'salesmanager_main':
        # Main company sales manager: see companies assigned as related_manager and their related companies
        assigned = base_queryset.filter(related_manager=user)
        related = base_queryset.filter(related_company__in=assigned)
        return assigned | related
    elif role == 'service_main':
        # Main company service: see all
        return base_queryset
    elif role in ('manager_distributor', 'salesmanager_distributor', 'service_distributor') and user.company:
        # Distributor roles: see their distributor and related companies
        return base_queryset.filter(
            models.Q(id=user.company.id) |
            models.Q(related_company=user.company)
        )
    # Default: see nothing
    return base_queryset.none()
