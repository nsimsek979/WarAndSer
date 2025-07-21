document.addEventListener('DOMContentLoaded', function() {
    // Handle attribute type change for dynamic unit filtering
    function setupAttributeTypeChange() {
        const attributeTypeSelects = document.querySelectorAll('.attribute-type-select');
        
        attributeTypeSelects.forEach(function(select) {
            select.addEventListener('change', function() {
                const unitSelect = this.closest('tr, .form-row').querySelector('.attribute-unit-select');
                if (!unitSelect) return;
                
                const attributeTypeId = this.value;
                
                // Clear existing options
                unitSelect.innerHTML = '<option value="">---------</option>';
                
                if (!attributeTypeId) {
                    return;
                }
                
                // Make AJAX request to get units
                fetch(`/item-master/ajax/get-attribute-units/?attribute_type_id=${attributeTypeId}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.units) {
                            data.units.forEach(function(unit) {
                                const option = document.createElement('option');
                                option.value = unit.id;
                                option.textContent = unit.display;
                                unitSelect.appendChild(option);
                            });
                        }
                    })
                    .catch(error => {
                        console.error('Error fetching units:', error);
                    });
            });
        });
    }
    
    // Setup for existing forms
    setupAttributeTypeChange();
    
    // Setup for dynamically added inline forms (for TabularInline)
    document.addEventListener('DOMNodeInserted', function(e) {
        if (e.target.nodeType === 1 && e.target.classList && e.target.classList.contains('dynamic-inventoryitemattribute_set')) {
            setTimeout(setupAttributeTypeChange, 100);
        }
    });
    
    // Also handle the "Add another" button clicks
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('add-row')) {
            setTimeout(setupAttributeTypeChange, 100);
        }
    });
});
