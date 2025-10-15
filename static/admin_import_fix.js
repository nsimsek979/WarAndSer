/* Import Export File Input Fix */
document.addEventListener('DOMContentLoaded', function() {
    // Fix for file input in import-export
    var fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(function(input) {
        // Remove any potential event conflicts
        input.style.opacity = '1';
        input.style.position = 'relative';
        input.style.zIndex = '10';
        
        // Add change event
        input.addEventListener('change', function(e) {
            if (e.target.files.length > 0) {
                console.log('File selected:', e.target.files[0].name);
                
                // Show file name somewhere
                var fileName = e.target.files[0].name;
                var helpText = input.parentNode.querySelector('.help');
                if (helpText) {
                    helpText.textContent = 'Selected: ' + fileName;
                    helpText.style.color = 'green';
                }
            }
        });
    });
    
    // Fix for any overlay issues
    var submitRows = document.querySelectorAll('.submit-row');
    submitRows.forEach(function(row) {
        row.style.position = 'relative';
        row.style.zIndex = '1';
    });
});
