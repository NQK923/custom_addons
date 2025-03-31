// Room Management JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Select2 for patient selection
    if (document.querySelectorAll('.patient-select').length) {
        $('.patient-select').select2({
            placeholder: 'Tìm kiếm bệnh nhân...',
            minimumInputLength: 2,
            ajax: {
                url: '/api/patients/search',
                dataType: 'json',
                delay: 250,
                data: function (params) {
                    return {
                        term: params.term
                    };
                },
                processResults: function (data) {
                    return {
                        results: $.map(data, function (item) {
                            return {
                                text: item.code + ' - ' + item.name,
                                id: item.id
                            }
                        })
                    };
                },
                cache: true
            }
        });
    }

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
});