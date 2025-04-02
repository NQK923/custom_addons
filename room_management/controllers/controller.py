from odoo import http
from odoo.http import request
from odoo.exceptions import ValidationError


class RoomManagementController(http.Controller):
    @http.route('/clinic/rooms', type='http', auth='user', website=True)
    def room_list(self, **kwargs):
        """Hiển thị danh sách phòng khám"""
        rooms = request.env['clinic.room'].sudo().search([])
        values = {
            'rooms': rooms,
        }
        return request.render('room_management.room_list_template', values)

    @http.route('/clinic/room/<model("clinic.room"):room>', type='http', auth='user', website=True)
    def room_detail(self, room, **kwargs):
        """Hiển thị chi tiết phòng khám và danh sách giường bệnh"""
        values = {
            'room': room,
        }
        return request.render('room_management.room_detail_template', values)

    @http.route('/clinic/rooms/create', type='http', auth='user', website=True, methods=['GET', 'POST'])
    def create_room(self, **kwargs):
        """Tạo phòng mới"""
        error = None
        success = None

        if request.httprequest.method == 'POST':
            try:
                name = kwargs.get('name')
                room_type = kwargs.get('room_type')
                capacity = int(kwargs.get('capacity', 0))
                note = kwargs.get('note', '')

                if not name or not room_type:
                    error = "Vui lòng nhập đầy đủ thông tin bắt buộc"
                elif capacity < 1:
                    error = "Sức chứa phải lớn hơn 0"
                else:
                    # Tạo phòng mới
                    room_vals = {
                        'name': name,
                        'room_type': room_type,
                        'capacity': capacity,
                        'note': note
                    }

                    new_room = request.env['clinic.room'].sudo().create(room_vals)
                    if new_room:
                        success = "Tạo phòng thành công!"
                        return request.redirect('/clinic/room/' + str(new_room.id))
                    else:
                        error = "Không thể tạo phòng, vui lòng thử lại"
            except Exception as e:
                error = str(e)

        values = {
            'error': error,
            'success': success,
            'default': kwargs,
        }
        return request.render('room_management.room_form_template', values)

    @http.route('/clinic/room/<model("clinic.room"):room>/edit', type='http', auth='user', website=True,
                methods=['GET', 'POST'])
    def edit_room(self, room, **kwargs):
        """Chỉnh sửa thông tin phòng"""
        error = None
        success = None

        if request.httprequest.method == 'POST':
            try:
                name = kwargs.get('name')
                room_type = kwargs.get('room_type')
                capacity = int(kwargs.get('capacity', 0))
                note = kwargs.get('note', '')

                if not name or not room_type:
                    error = "Vui lòng nhập đầy đủ thông tin bắt buộc"
                elif capacity < 1:
                    error = "Sức chứa phải lớn hơn 0"
                else:
                    # Cập nhật thông tin phòng
                    room_vals = {
                        'name': name,
                        'room_type': room_type,
                        'capacity': capacity,
                        'note': note
                    }

                    try:
                        room.sudo().write(room_vals)
                        success = "Cập nhật phòng thành công!"
                        return request.redirect('/clinic/room/' + str(room.id))
                    except ValidationError as ve:
                        error = str(ve)
                    except Exception as e:
                        error = "Có lỗi xảy ra: " + str(e)
            except Exception as e:
                error = str(e)

        values = {
            'room': room,
            'error': error,
            'success': success,
            'default': kwargs if kwargs else {
                'name': room.name,
                'room_type': room.room_type,
                'capacity': room.capacity,
                'note': room.note or '',
            },
        }
        return request.render('room_management.room_form_template', values)

    @http.route('/clinic/room/<model("clinic.room"):room>/delete', type='http', auth='user', website=True)
    def delete_room(self, room, **kwargs):
        """Xóa phòng"""
        try:
            # Kiểm tra xem phòng có giường đang có bệnh nhân không
            occupied_beds = room.bed_ids.filtered(lambda b: b.patient_id)
            if occupied_beds:
                # Nếu có bệnh nhân, chuyển hướng về trang chi tiết với thông báo lỗi
                return request.redirect('/clinic/room/%s?error=%s' % (room.id, "Không thể xóa phòng có bệnh nhân"))

            # Xóa phòng
            room.sudo().unlink()
            return request.redirect('/clinic/rooms?success=Xóa phòng thành công')
        except Exception as e:
            return request.redirect('/clinic/rooms?error=%s' % str(e))

    @http.route('/clinic/bed/<model("clinic.bed"):bed>/assign', type='http', auth='user', website=True,
                methods=['GET', 'POST'])
    def assign_patient(self, bed, **kwargs):
        """Xếp bệnh nhân vào giường"""
        # Xử lý khi form được submit
        if request.httprequest.method == 'POST':
            patient_id = kwargs.get('patient_id')
            if patient_id:
                bed.sudo().write({'patient_id': int(patient_id)})
                return request.redirect('/clinic/room/' + str(bed.room_id.id))

        # Hiển thị form chọn bệnh nhân
        patients = request.env['clinic.patient'].sudo().search([('patient_type', '=', 'outpatient')])
        values = {
            'bed': bed,
            'patients': patients,
        }
        return request.render('room_management.assign_patient_template', values)

    @http.route('/clinic/bed/<model("clinic.bed"):bed>/discharge', type='http', auth='user', website=True)
    def discharge_patient(self, bed, **kwargs):
        """Xuất viện cho bệnh nhân"""
        if bed.patient_id:
            bed.sudo().action_out()
        return request.redirect('/clinic/room/' + str(bed.room_id.id))