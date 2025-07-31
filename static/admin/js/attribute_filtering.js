django.jQuery(document).ready(function($) {
    console.log('Attribute filtering script loaded');
    
    // Function to update unit options based on selected attribute type
    function updateUnitOptions(attributeTypeSelect) {
        var attributeTypeId = $(attributeTypeSelect).val();
        console.log('Updating units for attribute type:', attributeTypeId);
        
        // Find the corresponding unit select in the same row
        var $row = $(attributeTypeSelect).closest('.form-row, tr, .dynamic-form');
        var unitSelect = $row.find('select[name*="unit"]').not('[name*="attribute_type"]').first();
        
        // If not found, try different selectors
        if (unitSelect.length === 0) {
            unitSelect = $row.find('#id_unit');
        }
        if (unitSelect.length === 0) {
            // For inline forms, try finding by id pattern
            var attributeSelectName = $(attributeTypeSelect).attr('name');
            if (attributeSelectName && attributeSelectName.includes('-')) {
                var prefix = attributeSelectName.replace('attribute_type', 'unit');
                unitSelect = $('[name="' + prefix + '"]');
            }
        }
        
        console.log('Found unit select:', unitSelect.length > 0 ? unitSelect.attr('name') : 'none');
        
        if (unitSelect.length === 0) {
            console.log('No unit select found for attribute type select');
            return;
        }
        
        if (attributeTypeId) {
            $.ajax({
                url: '/item-master/ajax/get-attribute-units/',
                data: {
                    'attribute_type_id': attributeTypeId
                },
                success: function(data) {
                    console.log('Units received:', data.units);
                    unitSelect.empty();
                    unitSelect.append('<option value="">---------</option>');
                    
                    $.each(data.units, function(i, unit) {
                        var selected = unit.is_default ? 'selected' : '';
                        unitSelect.append('<option value="' + unit.id + '" ' + selected + '>' + unit.name + '</option>');
                    });
                },
                error: function(xhr, status, error) {
                    console.log('Error loading units:', error);
                }
            });
        } else {
            unitSelect.empty();
            unitSelect.append('<option value="">---------</option>');
        }
    }
    
    // Function to bind events to attribute type selects
    function bindAttributeTypeEvents() {
        $('select[name*="attribute_type"]').off('change.attribute-filter').on('change.attribute-filter', function() {
            console.log('Attribute type changed:', this.name, this.value);
            updateUnitOptions(this);
        });
    }
    
    // Initial binding
    bindAttributeTypeEvents();
    
    // Initialize existing selects on page load
    $('select[name*="attribute_type"]').each(function() {
        if ($(this).val()) {
            updateUnitOptions(this);
        }
    });
    
    // For Django admin inline forms - detect when new forms are added
    $(document).on('click', '.add-row a, .addlink', function() {
        console.log('Add row clicked');
        setTimeout(function() {
            bindAttributeTypeEvents();
        }, 100);
    });
    
    // Alternative method: observe DOM changes
    if (window.MutationObserver) {
        var observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList') {
                    mutation.addedNodes.forEach(function(node) {
                        if (node.nodeType === 1) { // Element node
                            var $node = $(node);
                            if ($node.find('select[name*="attribute_type"]').length > 0 || 
                                $node.is('select[name*="attribute_type"]')) {
                                console.log('New attribute_type select detected');
                                bindAttributeTypeEvents();
                            }
                        }
                    });
                }
            });
        });
        
        // Start observing
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
    
    console.log('Attribute filtering script initialization complete');
});
