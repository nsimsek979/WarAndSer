from django.db.models import Q


def get_user_accessible_companies(user):
    """
    Kullanıcının erişebileceği şirketleri döndürür:
    - Kendi şirketi
    - Alt şirketler (kendisinin related_company'si olanlar)
    """
    if not hasattr(user, 'company') or not user.company:
        return []
    
    from customer.models import Company
    
    user_company = user.company
    accessible_companies = [user_company.id]
    
    # Bu şirketin alt şirketlerini ekle (related_company olarak bu şirketi seçenler)
    child_companies = Company.objects.filter(related_company=user_company)
    for child in child_companies:
        accessible_companies.append(child.id)
        
        # Alt şirketlerin de alt şirketleri varsa (2 seviye aşağı)
        grandchild_companies = Company.objects.filter(related_company=child)
        for grandchild in grandchild_companies:
            accessible_companies.append(grandchild.id)
    
    # Tekrarları kaldır
    accessible_companies = list(set(accessible_companies))
    
    return accessible_companies


def get_user_accessible_companies_filter(user, model_type='installation'):
    """
    Django ORM için kullanılabilir Q objesi döndürür
    model_type: 'installation', 'warranty', 'service'
    """
    accessible_company_ids = get_user_accessible_companies(user)
    
    if not accessible_company_ids:
        # Hiçbir şirkete erişimi yoksa hiçbir sonuç döndürmesin
        if model_type == 'installation':
            return Q(customer__id__in=[])
        else:  # warranty, service
            return Q(installation__customer__id__in=[])
    
    if model_type == 'installation':
        return Q(customer__id__in=accessible_company_ids)
    else:  # warranty, service
        return Q(installation__customer__id__in=accessible_company_ids)
