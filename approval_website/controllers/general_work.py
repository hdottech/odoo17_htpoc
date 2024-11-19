from odoo import http, fields, _
from odoo.http import request
from datetime import datetime
import logging
from ..utils.date_utils import DateUtils
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


# 申請表菜單
class FormSelectionController(http.Controller):
    @http.route('/form_selection', type='http', auth='public', website=True)
    def form_selection(self, **kw):
        return request.render('approval_website.form_selection_template', {
        }) 
class TestWebsiteController(http.Controller):
    @http.route('/vendor', type='http', auth='public', website=True)
    def index(self, **kwargs):
        """顯示一般作業申請表單頁面"""
        values = kwargs.copy()
        approval_types = request.env['approval.type'].sudo().search([('active', '=', True)])
        return request.render('approval_website.vendor_form_template123', {
            'main_contractors': request.env['new.res.partner.company'].sudo().search([]),
            'sub_contractors': request.env['new.res.partner.company'].sudo().search([]),
            'approval_types': approval_types,
            'datetime': datetime, 
            'values': values
        })

    @http.route('/vendor/submit', type='http', auth='public', website=True, methods=['POST'])
    def vendor_submit(self, **post):
        try:
            _logger.info("開始處理一般作業申請表單提交")
            
            # 獲取審批主題
            approval_type = request.env['approval.type'].sudo().browse(int(post.get('approval_type_id')))
            if not approval_type:
                raise ValidationError(_("請選擇有效的審批主題"))

            approval_category = request.env['approval.category'].sudo().search([
                ('name', '=', '一般作業申請表單(限七日)')
            ], limit=1)

            # 獲取主承商和次承商資訊
            main_contractor = request.env['new.res.partner.company'].sudo().browse(int(post.get('main_contractor')))
            sub_contractor = request.env['new.res.partner.company'].sudo().browse(int(post.get('sub_contractor')))
            
            # 修改時間格式，將結束時間設為 18:00:00
            start_datetime = f"{post.get('date_assign')} 00:00:00"
            end_datetime = DateUtils.set_end_time(post.get('date_end'))  # 使用 DateUtils

            # 日期驗證
            start_date = datetime.strptime(post.get('date_assign'), '%Y-%m-%d')
            end_date = datetime.strptime(post.get('date_end'), '%Y-%m-%d')
            delta = end_date - start_date
            if delta.days + 1 > 7:
                raise ValidationError(_("日期範圍不能超過7天"))

            # 創建任務值
            vals = {
                'category_id': approval_category.id,
                'request_owner_id': request.env.user.id,
                'request_status': 'new',
                'name': approval_type.name,  # 使用選擇的審批主題名稱
                'email': 'no-email@example.com', # 提供預設值
                'approval_type_id': approval_type.id,  # 關聯審批主題
                'planned_date_begin': start_datetime,
                'planned_date_end': end_datetime,
                'main_contractor_id': main_contractor.id,
                'sub_contractor_id': sub_contractor.id,
                'reason': f"""
                    <h3>一般作業申請表單詳情：</h3>
                    <table class="table table-bordered">
                        <tr><th>審批主題</th><td>{approval_type.name}</td></tr>
                        <tr><th>主承商</th><td>{main_contractor.name}</td></tr>
                        <tr><th>次承商</th><td>{sub_contractor.name}</td></tr>
                        <tr><th>施工區位置</th><td>{post.get('work_location')}</td></tr>
                        <tr><th>施工人數</th><td>{post.get('worker_count')}</td></tr>
                        <tr><th>監工人員</th><td>{post.get('supervisor_name')}</td></tr>
                        <tr><th>監工電話</th><td>{post.get('supervisor_phone')}</td></tr>
                        <tr><th>工安人員</th><td>{post.get('safety_staff_name')}</td></tr>
                        <tr><th>工安電話</th><td>{post.get('safety_staff_phone')}</td></tr>
                    </table>
                """
            }

            # 創建審批請求
            approval_request = request.env['approval.request'].sudo().create(vals)

            # 確認請求
            approval_request.sudo().action_confirm()

            return request.render('approval_website.vendor_form_success', {
                'approval_request': approval_request,
                'request_number': approval_request.name,
                'status': '等待審批',
                'planned_date_begin': start_datetime,
                'planned_date_end': end_datetime
            })

        except Exception as e:
            _logger.error(f"提交表單時發生錯誤: {str(e)}", exc_info=True)
            return request.render('approval_website.vendor_form_template123', {
                'error': str(e),
                'main_contractors': request.env['new.res.partner.company'].sudo().search([]),
                'sub_contractors': request.env['new.res.partner.company'].sudo().search([]),
                'approval_types': request.env['approval.type'].sudo().search([('active', '=', True)]),
                'values': post
            })