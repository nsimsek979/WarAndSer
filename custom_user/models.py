from django.contrib.auth.models import AbstractUser
from django.db import models
from customer.models import Company


class CustomUser(AbstractUser):
    class Meta(AbstractUser.Meta):
        permissions = [
            ("can_assign_manager", "Can assign manager to company"),
        ]
    ROLE_CHOICES = [
        ("manager_main", "Main Company Manager"),
        ("salesmanager_main", "Main Company Sales Manager"),
        ("service_main", "Main Company Service Personnel"),
        ("manager_distributor", "Distributor Manager"),
        ("salesmanager_distributor", "Distributor Sales Manager"),
        ("service_distributor", "Distributor Service Personnel"),
    ]
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True)
    role = models.CharField(max_length=32, choices=ROLE_CHOICES, null=True, blank=True)
