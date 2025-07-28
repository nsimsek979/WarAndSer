/**
 * Auto-assign related_manager when company_type is enduser and related_company is selected
 */
(function($) {
    $(document).ready(function() {
        var $companyType = $('#id_company_type');
        var $relatedCompany = $('#id_related_company');
        var $relatedManager = $('#id_related_manager');
        
        function updateRelatedManager() {
            var companyType = $companyType.val();
            var relatedCompanyId = $relatedCompany.val();
            
            // Only auto-assign if company is end user and related company is selected
            if (companyType === 'enduser' && relatedCompanyId) {
                // Make AJAX request to get related company's manager
                $.ajax({
                    url: '/admin/customer/company/' + relatedCompanyId + '/change/',
                    type: 'GET',
                    success: function(data) {
                        // Extract related_manager value from the response
                        var $tempDiv = $('<div>').html(data);
                        var relatedManagerValue = $tempDiv.find('#id_related_manager').val();
                        
                        if (relatedManagerValue && !$relatedManager.val()) {
                            // Only set if related_manager is currently empty
                            $relatedManager.val(relatedManagerValue).trigger('change');
                            
                            // Show a notification
                            if (typeof window.showNotification === 'function') {
                                window.showNotification('Related manager has been automatically assigned from the related company.', 'success');
                            }
                        }
                    },
                    error: function() {
                        console.log('Could not fetch related company data');
                    }
                });
            }
        }
        
        // Alternative approach using select2 if autocomplete is used
        function updateRelatedManagerViaAPI() {
            var companyType = $companyType.val();
            var relatedCompanyId = $relatedCompany.val();
            
            if (companyType === 'enduser' && relatedCompanyId && !$relatedManager.val()) {
                // Use the correct API endpoint
                fetch('/customer/api/companies/' + relatedCompanyId + '/manager/')
                    .then(response => response.json())
                    .then(data => {
                        if (data.related_manager_id) {
                            $relatedManager.val(data.related_manager_id).trigger('change');
                            
                            // Create and show notification
                            var notification = $('<div class="alert alert-success" style="position: fixed; top: 20px; right: 20px; z-index: 9999; padding: 10px; border-radius: 4px; background: #d4edda; border: 1px solid #c3e6cb; color: #155724;">').text('Related manager automatically assigned from related company');
                            $('body').append(notification);
                            setTimeout(function() {
                                notification.fadeOut();
                            }, 3000);
                        }
                    })
                    .catch(error => {
                        console.log('API request failed:', error);
                        // Fallback to simple approach
                        updateRelatedManagerFallback();
                    });
            }
        }
        
        // Simplified fallback approach
        function updateRelatedManagerFallback() {
            var companyType = $companyType.val();
            var relatedCompanyId = $relatedCompany.val();
            
            if (companyType === 'enduser' && relatedCompanyId && !$relatedManager.val()) {
                // Show a message to user
                var message = 'Note: If this is an end user company, you may want to assign the related manager from the related company.';
                
                // Create notification element
                var $notification = $('<div>', {
                    'class': 'help-block',
                    'style': 'color: #856404; background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 8px; border-radius: 4px; margin-top: 5px;',
                    'text': message
                });
                
                // Remove existing notifications
                $relatedManager.closest('.form-row').find('.help-block').remove();
                
                // Add notification after related_manager field
                $relatedManager.closest('.form-row').append($notification);
                
                // Auto-remove after 10 seconds
                setTimeout(function() {
                    $notification.fadeOut();
                }, 10000);
            }
        }
        
        // Bind events - use API version first, fallback if needed
        $companyType.on('change', function() {
            updateRelatedManagerViaAPI();
        });
        
        $relatedCompany.on('change', function() {
            updateRelatedManagerViaAPI();
        });
        
        // Also trigger on page load if values are already set
        if ($companyType.val() && $relatedCompany.val()) {
            updateRelatedManagerViaAPI();
        }
    });
})(django.jQuery);
