/* File JS đơn giản cho website medical management */
document.addEventListener('DOMContentLoaded', function() {
    // Xử lý hiển thị tên file khi chọn file
    const fileInputs = document.querySelectorAll('.custom-file-input');
    if (fileInputs) {
        fileInputs.forEach(input => {
            input.addEventListener('change', function() {
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
                        reader.onload = function(e) {
                            previewElement.innerHTML = `<img src="${e.target.result}" class="img-fluid" />`;
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
        searchQueryEl.addEventListener('keyup', function() {
            clearTimeout(debounceTimeout);
            debounceTimeout = setTimeout(filterTable, 300);
        });
    }
});