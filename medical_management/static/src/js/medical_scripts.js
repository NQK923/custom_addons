/* Enhanced JS for medical management */
document.addEventListener('DOMContentLoaded', function () {
    // Xử lý hiển thị tên file khi chọn file
    const fileInputs = document.querySelectorAll('.custom-file-input');
    if (fileInputs) {
        fileInputs.forEach(input => {
            input.addEventListener('change', function () {
                const fileName = this.value.split('\\').pop();
                const label = this.nextElementSibling;
                if (label) {
                    label.textContent = fileName || 'Chọn file...';
                }

                // Hiển thị xem trước hình ảnh
                if (this.files && this.files[0]) {
                    const reader = new FileReader();
                    const previewElement = document.querySelector('.image-preview');

                    if (previewElement) {
                        reader.onload = function (e) {
                            previewElement.innerHTML = `
                                <div class="card p-2 border">
                                    <p class="mb-1"><strong>Xem trước:</strong></p>
                                    <img src="${e.target.result}" class="img-fluid" style="max-height: 200px; width: auto;"/>
                                </div>
                            `;
                        };
                        reader.readAsDataURL(this.files[0]);
                    }
                }
            });
        });
    }

    // Xử lý lọc và tìm kiếm
    const filterStatusEl = document.getElementById('filter_status');
    const filterTypeEl = document.getElementById('filter_test_type');
    const searchQueryEl = document.getElementById('search_query');

    function filterTable() {
        const rows = document.querySelectorAll('.medical-test-table tbody tr');
        const statusFilter = filterStatusEl ? filterStatusEl.value : '';
        const typeFilter = filterTypeEl ? filterTypeEl.value : '';
        const searchQuery = searchQueryEl ? searchQueryEl.value.toLowerCase() : '';

        rows.forEach(row => {
            const statusCell = row.querySelector('td.test-status');
            const typeCell = row.querySelector('td.test-type');

            const status = statusCell ? statusCell.dataset.status : '';
            const type = typeCell ? typeCell.dataset.type : '';
            const text = row.textContent.toLowerCase();

            const statusMatch = !statusFilter || status === statusFilter;
            const typeMatch = !typeFilter || type === typeFilter;
            const searchMatch = !searchQuery || text.includes(searchQuery);

            if (statusMatch && typeMatch && searchMatch) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }

    // Thêm event listeners cho bộ lọc
    if (filterStatusEl) {
        filterStatusEl.addEventListener('change', filterTable);
    }

    if (filterTypeEl) {
        filterTypeEl.addEventListener('change', filterTable);
    }

    if (searchQueryEl) {
        let debounceTimeout;
        searchQueryEl.addEventListener('keyup', function () {
            clearTimeout(debounceTimeout);
            debounceTimeout = setTimeout(filterTable, 300);
        });
    }

    // Xử lý xác nhận xóa
    const deleteLinks = document.querySelectorAll('.delete-confirm');
    deleteLinks.forEach(link => {
        link.addEventListener('click', function (e) {
            e.preventDefault();
            const url = this.getAttribute('href');
            const itemName = this.getAttribute('data-name') || 'mục này';

            if (confirm(`Bạn có chắc chắn muốn xóa ${itemName}? Hành động này không thể hoàn tác.`)) {
                window.location.href = url;
            }
        });
    });

    // Đổi trạng thái nhanh (Quick Status Change)
    const quickStatusChanges = document.querySelectorAll('.quick-status-change');
    quickStatusChanges.forEach(select => {
        select.addEventListener('change', function () {
            const testId = this.getAttribute('data-test-id');
            const status = this.value;
            const formData = new FormData();

            formData.append('test_id', testId);
            formData.append('status', status);

            // Sử dụng fetch API để cập nhật trạng thái
            fetch('/medical/test/update_status', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin'
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Hiển thị thông báo thành công
                        const statusCell = document.querySelector(`.status-cell-${testId}`);
                        if (statusCell) {
                            const statusText = {
                                'request': 'Yêu cầu',
                                'processing': 'Đang xử lý',
                                'completed': 'Hoàn tất'
                            }[status];

                            const statusClass = {
                                'request': 'badge-warning',
                                'processing': 'badge-info',
                                'completed': 'badge-success'
                            }[status];

                            statusCell.innerHTML = `<span class="badge ${statusClass}">${statusText}</span>`;
                        }

                        // Hiển thị thông báo nhỏ
                        showToast('Cập nhật trạng thái thành công!');
                    } else {
                        // Hiển thị thông báo lỗi
                        showToast('Có lỗi xảy ra. Vui lòng thử lại!', 'error');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    showToast('Có lỗi xảy ra. Vui lòng thử lại!', 'error');
                });
        });
    });

    // Function hiển thị thông báo
    function showToast(message, type = 'success') {
        const toast = document.createElement('div');
        toast.className = `toast ${type === 'success' ? 'bg-success' : 'bg-danger'} text-white`;
        toast.style.position = 'fixed';
        toast.style.bottom = '20px';
        toast.style.right = '20px';
        toast.style.padding = '10px 20px';
        toast.style.borderRadius = '4px';
        toast.style.zIndex = '9999';
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s ease';
        toast.textContent = message;

        document.body.appendChild(toast);

        // Hiển thị toast
        setTimeout(() => {
            toast.style.opacity = '1';
        }, 10);

        // Xóa toast sau 3 giây
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => {
                document.body.removeChild(toast);
            }, 300);
        }, 3000);
    }

    // Xử lý responsive tables
    makeTableResponsive();

    function makeTableResponsive() {
        const tables = document.querySelectorAll('.medical-table');
        if (window.innerWidth < 768) {
            tables.forEach(table => {
                table.classList.add('table-responsive');
            });
        } else {
            tables.forEach(table => {
                table.classList.remove('table-responsive');
            });
        }
    }

    // Sự kiện resize window
    window.addEventListener('resize', makeTableResponsive);

    // Hiệu ứng cho các card
    const cards = document.querySelectorAll('.medical-card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function () {
            this.style.transform = 'translateY(-5px)';
            this.style.boxShadow = '0 8px 15px rgba(0, 0, 0, 0.1)';
        });

        card.addEventListener('mouseleave', function () {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '0 4px 6px rgba(0, 0, 0, 0.1)';
        });
    });
});