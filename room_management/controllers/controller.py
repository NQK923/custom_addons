from odoo import http
from odoo.http import request
from odoo.exceptions import ValidationError
import json


class RoomManagementController(http.Controller):
    @http.route('/clinic/rooms', type='http', auth='public', website=True)
    def clinic_rooms(self, **kwargs):
        rooms = request.env['clinic.room'].sudo().search([])

        search_room = kwargs.get('search_room')
        search_status = kwargs.get('search_status')

        domain = []
        if search_room:
            domain.append(('room_id', '=', int(search_room)))
        if search_status:
            domain.append(('status', '=', search_status))

        beds = request.env['clinic.bed'].sudo().search(domain)

        values = {
            'rooms': rooms,
            'beds': beds,
        }
        return request.render('room_management.room_list_template', values)

    @http.route('/clinic/room/create', type='http', auth='user', website=True, methods=['GET', 'POST'])
    def create_room(self, **kwargs):
        error_message = None
        success_message = None

        if request.httprequest.method == 'POST':
            try:
                name = kwargs.get('name')
                room_type = kwargs.get('room_type')
                capacity = int(kwargs.get('capacity', 0))
                note = kwargs.get('note', '')

                if not name or not room_type or capacity < 1:
                    error_message = "Vui lòng điền đầy đủ thông tin và sức chứa phải lớn hơn 0"
                else:
                    # Tạo phòng mới - giường sẽ được tạo tự động trong phương thức create của model
                    request.env['clinic.room'].sudo().create({
                        'name': name,
                        'room_type': room_type,
                        'capacity': capacity,
                        'note': note
                    })
                    success_message = "Tạo phòng thành công"
                    if not error_message:
                        return request.redirect('/clinic/rooms')
            except Exception as e:
                error_message = f"Lỗi khi tạo phòng: {str(e)}"

        values = {
            'error_message': error_message,
            'success_message': success_message,
            'room_types': [
                ('exam', 'Phòng khám'),
                ('treatment', 'Phòng điều trị'),
                ('emergency', 'Phòng cấp cứu')
            ],
            'default_values': kwargs
        }
        return request.render('room_management.room_create_template', values)

    @http.route('/clinic/room/<int:room_id>/edit', type='http', auth='user', website=True, methods=['GET', 'POST'])
    def edit_room(self, room_id=None, **kwargs):
        if not room_id:
            return request.redirect('/clinic/rooms')

        room = request.env['clinic.room'].sudo().browse(room_id)
        error_message = None
        success_message = None

        if request.httprequest.method == 'POST':
            try:
                name = kwargs.get('name')
                room_type = kwargs.get('room_type')
                capacity = int(kwargs.get('capacity', 0))
                note = kwargs.get('note', '')

                if not name or not room_type or capacity < 1:
                    error_message = "Vui lòng điền đầy đủ thông tin và sức chứa phải lớn hơn 0"
                else:
                    # Cập nhật thông tin phòng
                    room.write({
                        'name': name,
                        'room_type': room_type,
                        'capacity': capacity,
                        'note': note
                    })
                    success_message = "Cập nhật phòng thành công"
                    if not error_message:
                        return request.redirect(f'/clinic/room/{room_id}')
            except ValidationError as e:
                error_message = str(e)
            except Exception as e:
                error_message = f"Lỗi khi cập nhật phòng: {str(e)}"

        values = {
            'room': room,
            'error_message': error_message,
            'success_message': success_message,
            'room_types': [
                ('exam', 'Phòng khám'),
                ('treatment', 'Phòng điều trị'),
                ('emergency', 'Phòng cấp cứu')
            ]
        }
        return request.render('room_management.room_edit_template', values)

    @http.route('/clinic/room/<int:room_id>', type='http', auth='public', website=True)
    def clinic_room_detail(self, room_id=None, **kwargs):
        if not room_id:
            return request.redirect('/clinic/rooms')

        room = request.env['clinic.room'].sudo().browse(room_id)

        # Handle discharge action if requested
        bed_id = kwargs.get('discharge_bed')
        success_message = None
        error_message = None

        if bed_id and request.httprequest.method == 'POST':
            try:
                bed = request.env['clinic.bed'].sudo().browse(int(bed_id))
                if bed and bed.patient_id:
                    # Execute discharge action
                    bed.action_out()
                    success_message = f"Bệnh nhân {bed.patient_name} đã được xuất viện thành công"
            except Exception as e:
                error_message = f"Lỗi khi xuất viện: {str(e)}"

        # Danh sách bệnh nhân cho mục đích phân giường
        patients = request.env['clinic.patient'].sudo().search([('patient_type', '=', 'outpatient')])

        values = {
            'room': room,
            'success_message': success_message,
            'error_message': error_message,
            'patients': patients
        }
        return request.render('room_management.room_detail_template', values)

    @http.route('/clinic/room/<int:room_id>/delete', type='http', auth='user', website=True, methods=['POST'])
    def delete_room(self, room_id=None, **kwargs):
        if not room_id:
            return request.redirect('/clinic/rooms')

        try:
            room = request.env['clinic.room'].sudo().browse(int(room_id))
            # Kiểm tra xem có bệnh nhân đang sử dụng giường trong phòng không
            if any(bed.patient_id for bed in room.bed_ids):
                return request.redirect(f'/clinic/rooms?error=room_has_patients')

            room.unlink()
            return request.redirect('/clinic/rooms?success=deleted')
        except Exception as e:
            return request.redirect(f'/clinic/rooms?error={str(e)}')

    # === CRUD cho giường bệnh ===

    @http.route('/clinic/bed/create', type='http', auth='user', website=True, methods=['GET', 'POST'])
    def create_bed(self, **kwargs):
        error_message = None
        success_message = None

        # Lấy danh sách phòng để hiển thị trong dropdown
        rooms = request.env['clinic.room'].sudo().search([])

        if request.httprequest.method == 'POST':
            try:
                room_id = kwargs.get('room_id')
                if not room_id:
                    error_message = "Vui lòng chọn phòng"
                else:
                    # Tạo giường mới
                    bed = request.env['clinic.bed'].sudo().create({
                        'room_id': int(room_id)
                    })
                    success_message = "Tạo giường bệnh mới thành công"
                    if not error_message:
                        return request.redirect('/clinic/rooms?active_tab=beds')
            except Exception as e:
                error_message = f"Lỗi khi tạo giường bệnh: {str(e)}"

        values = {
            'error_message': error_message,
            'success_message': success_message,
            'rooms': rooms,
            'default_values': kwargs
        }
        return request.render('room_management.bed_create_template', values)

    @http.route('/clinic/bed/<int:bed_id>', type='http', auth='public', website=True)
    def bed_detail(self, bed_id=None, **kwargs):
        if not bed_id:
            return request.redirect('/clinic/rooms?active_tab=beds')

        bed = request.env['clinic.bed'].sudo().browse(int(bed_id))
        if not bed.exists():
            return request.redirect('/clinic/rooms?active_tab=beds')

        # Xem thông tin chi tiết giường bệnh
        values = {
            'bed': bed
        }
        return request.render('room_management.bed_detail_template', values)

    @http.route('/clinic/bed/<int:bed_id>/edit', type='http', auth='user', website=True, methods=['GET', 'POST'])
    def edit_bed(self, bed_id=None, **kwargs):
        if not bed_id:
            return request.redirect('/clinic/rooms?active_tab=beds')

        bed = request.env['clinic.bed'].sudo().browse(int(bed_id))
        if not bed.exists():
            return request.redirect('/clinic/rooms?active_tab=beds')

        # Lấy danh sách phòng để hiển thị trong dropdown
        rooms = request.env['clinic.room'].sudo().search([])

        error_message = None
        success_message = None

        if request.httprequest.method == 'POST':
            try:
                room_id = kwargs.get('room_id')
                if not room_id:
                    error_message = "Vui lòng chọn phòng"
                else:
                    # Cập nhật thông tin giường
                    bed.room_id = int(room_id)
                    success_message = "Cập nhật giường bệnh thành công"
                    if not error_message:
                        return request.redirect(f'/clinic/bed/{bed_id}')
            except Exception as e:
                error_message = f"Lỗi khi cập nhật giường bệnh: {str(e)}"

        values = {
            'bed': bed,
            'rooms': rooms,
            'error_message': error_message,
            'success_message': success_message
        }
        return request.render('room_management.bed_edit_template', values)

    @http.route('/clinic/bed/<int:bed_id>/delete', type='http', auth='user', website=True, methods=['POST'])
    def delete_bed(self, bed_id=None, **kwargs):
        if not bed_id:
            return request.redirect('/clinic/rooms?active_tab=beds')

        try:
            bed = request.env['clinic.bed'].sudo().browse(int(bed_id))

            # Kiểm tra xem có bệnh nhân đang sử dụng giường không
            if bed.patient_id:
                return request.redirect(f'/clinic/rooms?active_tab=beds&error=bed_has_patient')

            bed.unlink()
            return request.redirect('/clinic/rooms?active_tab=beds&success=deleted')
        except Exception as e:
            return request.redirect(f'/clinic/rooms?active_tab=beds&error={str(e)}')

    @http.route('/clinic/bed/<int:bed_id>/assign', type='http', auth='user', website=True, methods=['POST'])
    def assign_patient(self, bed_id=None, **kwargs):
        if not bed_id:
            return request.redirect('/clinic/rooms?active_tab=beds')

        bed = request.env['clinic.bed'].sudo().browse(int(bed_id))
        patient_id = kwargs.get('patient_id')
        room_id = bed.room_id.id

        if bed and patient_id and bed.status == 'available':
            try:
                # Phân bệnh nhân vào giường
                patient = request.env['clinic.patient'].sudo().browse(int(patient_id))
                bed.patient_id = patient.id

                # Redirect dựa vào nơi đã gọi function
                referer = request.httprequest.headers.get('Referer', '')
                if 'active_tab=beds' in referer:
                    return request.redirect(f'/clinic/rooms?active_tab=beds&success=assigned')
                elif f'/clinic/room/{room_id}' in referer:
                    return request.redirect(f'/clinic/room/{room_id}?success=assigned')
                else:
                    return request.redirect(f'/clinic/bed/{bed_id}?success=assigned')

            except Exception as e:
                return request.redirect(f'/clinic/bed/{bed_id}?error={str(e)}')

        return request.redirect(f'/clinic/bed/{bed_id}?error=invalid_operation')

    @http.route('/clinic/bed/<int:bed_id>/discharge', type='http', auth='user', website=True, methods=['POST'])
    def discharge_patient(self, bed_id=None, **kwargs):
        if not bed_id:
            return request.redirect('/clinic/rooms?active_tab=beds')

        try:
            bed = request.env['clinic.bed'].sudo().browse(int(bed_id))
            if bed and bed.patient_id:
                # Thực hiện xuất viện
                patient_name = bed.patient_name
                bed.action_out()

                # Redirect dựa vào nơi đã gọi function
                referer = request.httprequest.headers.get('Referer', '')
                if 'active_tab=beds' in referer:
                    return request.redirect(
                        f'/clinic/rooms?active_tab=beds&success=discharged&patient_name={patient_name}')
                elif f'/clinic/room/{bed.room_id.id}' in referer:
                    return request.redirect(f'/clinic/room/{bed.room_id.id}?success=discharged')
                else:
                    return request.redirect(f'/clinic/bed/{bed_id}?success=discharged&patient_name={patient_name}')

        except Exception as e:
            return request.redirect(f'/clinic/bed/{bed_id}?error={str(e)}')

        return request.redirect(f'/clinic/bed/{bed_id}?error=invalid_operation')

    @http.route('/api/patients/search', type='http', auth='user', website=True)
    def search_patients(self, **kwargs):
        search_term = kwargs.get('term', '')
        patients = request.env['clinic.patient'].sudo().search([
            '|',
            ('name', 'ilike', search_term),
            ('code', 'ilike', search_term),
            ('patient_type', '=', 'outpatient')
        ], limit=10)

        result = []
        for patient in patients:
            result.append({
                'id': patient.id,
                'name': patient.name,
                'code': patient.code
            })

        return json.dumps(result)