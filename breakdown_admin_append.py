
@admin.register(BreakdownReason)
class BreakdownReasonAdmin(admin.ModelAdmin):
    """Admin interface for BreakdownReason model"""
    list_display = ['name', 'category', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'description', 'category']
    list_editable = ['is_active']
    ordering = ['category', 'name']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'category', 'description')
        }),
        (_('Settings'), {
            'fields': ('is_active',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()
