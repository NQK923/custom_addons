// Corrected Room Management JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert-dismissible');
        alerts.forEach(function(alert) {
            $(alert).fadeOut(500);
        });
    }, 5000);

    // Confirm delete actions
    const deleteButtons = document.querySelectorAll('.btn-delete-confirm');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            if (!confirm('Bạn có chắc chắn muốn xóa?')) {
                e.preventDefault();
            }
        });
    });

    // Enhanced modal functionality
    const assignButtons = document.querySelectorAll('.btn-assign-patient');
    assignButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            const bedId = this.getAttribute('data-bed-id');
            console.log('Assign button clicked for bed:', bedId);

            // The modal should open automatically via Bootstrap's data-toggle
            // This is just extra debugging to ensure the data-target is correct
            const targetSelector = this.getAttribute('data-target');
            console.log('Target modal selector:', targetSelector);

            // If for some reason the modal doesn't open automatically
            try {
                $(targetSelector).modal('show');
            } catch (error) {
                console.error('Error showing modal:', error);
            }
        });
    });

    // Debug form submissions
    const assignForms = document.querySelectorAll('.assign-patient-form');
    assignForms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            // Don't prevent default - allow normal submission
            const action = this.getAttribute('action');
            const patientId = this.querySelector('select[name="patient_id"]').value;

            console.log('Form submitted:', {
                action: action,
                patientId: patientId
            });

            // Only do basic validation
            if (!patientId) {
                e.preventDefault();
                this.querySelector('select[name="patient_id"]').classList.add('is-invalid');
                return false;
            }
        });
    });

    // Additional debugging
    console.log('Room management JS loaded');
    console.log('Assign buttons found:', assignButtons.length);
    console.log('Forms found:', assignForms.length);
});