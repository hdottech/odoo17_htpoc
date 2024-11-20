from odoo import http, fields, _
from odoo.http import request
from odoo.exceptions import ValidationError
import pytz
from datetime import datetime, timedelta
from ..utils.date_utils import DateUtils

import logging
_logger = logging.getLogger(__name__)

class EquipmentMaterialController(http.Controller):
    @http.route(['/equipment_material'], type='http', auth="public", website=True)
    def equipment_material_form(self, **kw):
        """機具物料進場申請頁面"""
        approval_types = request.env['approval.type'].sudo().search([('active', '=', True)])
        main_contractors = request.env['new.res.partner.company'].sudo().search([])
        sub_contractors = request.env['new.res.partner.company'].sudo().search([])

        values = {
            'main_contractors': main_contractors,
            'sub_contractors': sub_contractors,
            'approval_types': approval_types,
            # 'datetime': datetime,
            'values': kw
        }

        # 直接渲染表單頁面
        return request.render("approval_website.equipment_material_entry_form", values)
    @http.route(['/equipment_material/submit'], type='http', auth="public", website=True, csrf=False, methods=['POST'])
    def submit_equipment_material(self, **post):
        try:
            _logger.info(f"接收到的表單數據: {post}")

            # 獲取審批主題
            approval_type = request.env['approval.type'].sudo().browse(int(post.get('approval_type_id')))
            if not approval_type:
                raise ValidationError(_("請選擇有效的審批主題"))

            # 獲取審批類型
            approval_category = request.env['approval.category'].sudo().search([
                ('name', '=', '機具物料進場申請表單')
            ], limit=1)

            if not approval_category:
                raise ValidationError(_("找不到對應的審批類型"))
            
            # 驗證必填字段
            required_fields = ['sub_contractor', 'main_contractor', 
                            'entry_date', 'contact_person', 'contact_phone', 'item_details']
            
            # 根據進場方式驗證相應必填字段
            entry_methods = request.httprequest.form.getlist('entry_method')
            if not entry_methods:
                raise ValidationError(_("請至少選擇一種進場方式"))
            
            # 堆高機相關驗證
            # if '堆高機' in entry_methods:
            #     forklift_qualified = post.get('forklift_qualified')
            #     if not forklift_qualified:
            #         raise ValidationError(_("請選擇堆高機工區合格標籤"))
            #     if forklift_qualified == 'no':
            #         raise ValidationError(_("堆高機必須有工區合格標籤才能進場"))

            # 吊掛相關驗證
            if '吊掛' in entry_methods:
                if not post.get('crane_model'):
                    raise ValidationError(_("請填寫吊掛型號"))
                if not post.get('crane_tonnage'):
                    raise ValidationError(_("請填寫吊掛噸數"))

            # 其他相關驗證
            if '其他' in entry_methods:
                if not post.get('other_model_1'):
                    raise ValidationError(_("請填寫其他型號-1"))
                if not post.get('other_model_2'):
                    raise ValidationError(_("請填寫其他型號-2"))
                
            # 驗證基本必填字段
            missing_fields = [field for field in required_fields if not post.get(field)]
            if missing_fields:
                raise ValidationError(_("以下必填欄位未填寫: %s") % ', '.join(missing_fields))

            # 獲取主承攬商和次承攬商
            main_contractor = request.env['new.res.partner.company'].sudo().browse(int(post.get('main_contractor')))
            sub_contractor = request.env['new.res.partner.company'].sudo().browse(int(post.get('sub_contractor')))

            # 處理日期和時間
            entry_date = post.get('entry_date')
            if not entry_date:
                raise ValidationError(_("請選擇進場日期"))
            try:
                # 將 entry_date 固定為當天的 08:00 和 18:00
                planned_date_begin = datetime.strptime(entry_date, '%Y-%m-%d') + timedelta(hours=8)
                planned_date_end = datetime.strptime(entry_date, '%Y-%m-%d') + timedelta(hours=18)

                _logger.info(f"預設時間 - 開始: {planned_date_begin}, 結束: {planned_date_end}")

            except ValueError as e:
                raise ValidationError(_(str(e)))



            # 構建描述文本
            description = f"""
            <div class="approval-description">
                <h3>機具物料進場申請表單詳情：</h3>
                <table class="table table-bordered">
                    <tr>
                        <th style="width: 150px;">案場：</th>
                        <td>{approval_type.name}</td>
                    </tr>
                    <tr>
                        <th>主承攬商：</th>
                        <td>{main_contractor.name}</td>
                    </tr>
                    <tr>
                        <th>次承攬商：</th>
                        <td>{sub_contractor.name}</td>
                    </tr>
                    <tr>
                        <th>申請人電子郵件：</th>
                        <td>{post.get('email')}</td>
                    </tr>
                    <tr>
                        <th>進場日期：</th>
                        <td>{entry_date}</td>
                    </tr>
                    <tr>
                        <th>進場時間：</th>
                        <td>早上8點至下午6點</td>
                    </tr>
                    <tr>
                        <th>進場方式：</th>
                        <td>{', '.join(entry_methods)}</td>
                    </tr>
            """

            # 根據不同進場方式添加相應資訊
            if '貨車' in entry_methods:
                description += f"""
                    <tr>
                        <th>貨車車號：</th>
                        <td>{post.get('truck_details')}</td>
                    </tr>
                """

            if '堆高機' in entry_methods:
                description += f"""
                    <tr>
                        <th>堆高機工區合格標籤：</th>
                        <td>{'有' if post.get('forklift_qualified') == 'yes' else '無'}</td>
                    </tr>
                """

            if '吊掛' in entry_methods:
                description += f"""
                    <tr>
                        <th>吊掛型號：</th>
                        <td>{post.get('crane_model')}</td>
                    </tr>
                    <tr>
                        <th>吊掛噸數：</th>
                        <td>{post.get('crane_tonnage')} 噸</td>
                    </tr>
                """

            if '其他' in entry_methods:
                description += f"""
                    <tr>
                        <th>其他型號-1：</th>
                        <td>{post.get('other_model_1')}</td>
                    </tr>
                    <tr>
                        <th>其他型號-2：</th>
                        <td>{post.get('other_model_2')}</td>
                    </tr>
                """

            description += f"""
                    <tr>
                        <th>攜貨人/聯絡人：</th>
                        <td>{post.get('contact_person')}</td>
                    </tr>
                    <tr>
                        <th>聯絡電話：</th>
                        <td>{post.get('contact_phone')}</td>
                    </tr>
                    <tr>
                        <th>物品詳情：</th>
                        <td>{post.get('item_details')}</td>
                    </tr>
                </table>
            </div>
            """

            # 構建審批記錄值
            approval_vals = {
                'approval_type_id': approval_type.id,
                'name': approval_type.name,
                'request_owner_id': request.env.user.id,
                'category_id': approval_category.id,
                'request_status': 'pending',
                'email': post.get('email'),
                'sub_contractor_id': int(post.get('sub_contractor')),
                'main_contractor_id': int(post.get('main_contractor')),
                'entry_date': entry_date,
                'planned_date_begin': planned_date_begin,
                'planned_date_end': planned_date_end,
                'entry_method': ','.join(entry_methods),
                'contact_person': post.get('contact_person'),
                'contact_phone': post.get('contact_phone'),
                'item_details': post.get('item_details'),
                'reason': description,
            }

            # 根據進場方式添加額外資訊
            if '貨車' in entry_methods:
                approval_vals['truck_details'] = post.get('truck_details')
            if '堆高機' in entry_methods:
                approval_vals['forklift_operator_qualified'] = post.get('forklift_qualified', 'no')
            # if '堆高機' in entry_methods:
            #     if post.get('forklift_qualified') == 'yes':
            #         approval_vals['forklift_operator_qualified'] = 'yes'
            #     else:
            #         raise ValidationError(_("堆高機必須有工區合格標籤才能進場"))

            if '吊掛' in entry_methods:
                approval_vals['forklift_details'] = post.get('crane_model')
                approval_vals['forklift_count'] = float(post.get('crane_tonnage', 0))
            if '其他' in entry_methods:
                approval_vals['other_details1'] = post.get('other_model_1')
                approval_vals['other_details2'] = post.get('other_model_2')

            # 創建審批請求
            approval_request = request.env['approval.request'].sudo().create(approval_vals)
            approval_request.action_confirm()

            return request.render('approval_website.vendor_form_success', {
                'approval_request': approval_request,
                'request_number': approval_request.sequence_number,
                'planned_date_begin':planned_date_begin,
                'planned_date_end':  planned_date_end,
            })

        except ValidationError as e:
            _logger.error(f"表單驗證錯誤: {str(e)}")
            return request.render("approval_website.equipment_material_entry_form", {
                'error': str(e),
                'values': post,
                'main_contractors': request.env['new.res.partner.company'].sudo().search([]),
                'sub_contractors': request.env['new.res.partner.company'].sudo().search([]),
                'approval_types': request.env['approval.type'].sudo().search([('active', '=', True)]),
            })