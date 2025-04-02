// JavaScript cho Healthcare Management

odoo.define('healthcare_management.website_js', function(require) {
    'use strict';

    var ajax = require('web.ajax');
    var core = require('web.core');
    var _t = core._t;

    // Khởi tạo khi tài liệu đã sẵn sàng
    $(document).ready(function() {
        // Xử lý các thao tác với phản hồi
        $('button[data-feedback-id]').on('click', function() {
            var feedbackId = $(this).data('feedback-id');
            var action = $(this).data('action');

            if (!feedbackId || !action) return;

            // Hiển thị dialog xác nhận
            if (confirm(_t('Bạn có chắc chắn muốn thực hiện thao tác này?'))) {
                // Gửi yêu cầu AJAX để thực hiện thao tác
                ajax.jsonRpc('/healthcare/patient_feedback/action', 'call', {
                    'feedback_id': feedbackId,
                    'action': action
                }).then(function(result) {
                    if (result.success) {
                        // Hiển thị thông báo thành công
                        var message = '';
                        if (action === 'note') {
                            message = _t('Phản hồi đã được ghi nhận.');
                        } else if (action === 'cancel') {
                            message = _t('Phản hồi đã được hủy.');
                        } else if (action === 'new') {
                            message = _t('Phản hồi đã được thiết lập thành Mới.');
                        }

                        // Hiển thị thông báo và làm mới trang
                        alert(message);
                        location.reload();
                    } else {
                        // Hiển thị thông báo lỗi
                        alert(_t('Đã xảy ra lỗi: ') + (result.error || _t('Không xác định')));
                    }
                }).guardedCatch(function(error) {
                    console.error('Error:', error);
                    alert(_t('Đã xảy ra lỗi khi xử lý yêu cầu.'));
                });
            }
        });

        // Xử lý các thao tác với khiếu nại
        $('button[data-complaint-id]').on('click', function() {
            var complaintId = $(this).data('complaint-id');
            var action = $(this).data('action');

            if (!complaintId || !action) return;

            // Hiển thị dialog xác nhận
            if (confirm(_t('Bạn có chắc chắn muốn thực hiện thao tác này?'))) {
                // Gửi yêu cầu AJAX để thực hiện thao tác
                ajax.jsonRpc('/healthcare/patient_complaint/action', 'call', {
                    'complaint_id': complaintId,
                    'action': action
                }).then(function(result) {
                    if (result.success) {
                        // Hiển thị thông báo thành công
                        var message = '';
                        if (action === 'open') {
                            message = _t('Khiếu nại đã được chuyển sang trạng thái Đang xử lý.');
                        } else if (action === 'resolve') {
                            message = _t('Khiếu nại đã được giải quyết.');
                        } else if (action === 'cancel') {
                            message = _t('Khiếu nại đã được hủy.');
                        }

                        // Hiển thị thông báo và làm mới trang
                        alert(message);
                        location.reload();
                    } else {
                        // Hiển thị thông báo lỗi
                        alert(_t('Đã xảy ra lỗi: ') + (result.error || _t('Không xác định')));
                    }
                }).guardedCatch(function(error) {
                    console.error('Error:', error);
                    alert(_t('Đã xảy ra lỗi khi xử lý yêu cầu.'));
                });
            }
        });

        // Khởi tạo DataTables nếu thư viện được tải
        if ($.fn.DataTable) {
            $('.datatable').DataTable({
                responsive: true,
                language: {
                    url: '//cdn.datatables.net/plug-ins/1.10.22/i18n/Vietnamese.json'
                },
                pageLength: 10
            });
        }

        // Xử lý lọc và tìm kiếm nâng cao
        $('#advancedFilterBtn').on('click', function() {
            $('#advancedFilterForm').toggleClass('d-none');
        });

        // Xử lý toggle hiển thị các section
        $('.section-toggle').on('click', function() {
            var targetId = $(this).data('target');
            $(targetId).toggleClass('d-none');

            var icon = $(this).find('i');
            if (icon.hasClass('fa-chevron-down')) {
                icon.removeClass('fa-chevron-down').addClass('fa-chevron-up');
            } else {
                icon.removeClass('fa-chevron-up').addClass('fa-chevron-down');
            }
        });

        // Xử lý hiển thị tooltip
        $('[data-toggle="tooltip"]').tooltip();

        // Xử lý form tạo khiếu nại từ phản hồi
        $('#createComplaintFromFeedback').on('submit', function(e) {
            e.preventDefault();

            var formData = $(this).serialize();

            ajax.jsonRpc('/healthcare/patient_complaint/create_from_feedback', 'call', formData)
                .then(function(result) {
                    if (result.success) {
                        window.location = '/healthcare/patient_complaint/' + result.complaint_id;
                    } else {
                        alert(_t('Đã xảy ra lỗi: ') + (result.error || _t('Không xác định')));
                    }
                }).guardedCatch(function(error) {
                    console.error('Error:', error);
                    alert(_t('Đã xảy ra lỗi khi xử lý yêu cầu.'));
                });
        });
    });
});