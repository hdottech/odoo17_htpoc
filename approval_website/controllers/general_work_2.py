from odoo import http, fields, _
from odoo.http import request
from datetime import datetime,timedelta
import logging
from ..utils.date_utils import DateUtils
from odoo.exceptions import ValidationError
import pytz

_logger = logging.getLogger(__name__)


# 申請表菜單
class FormSelectionController2(http.Controller):
    @http.route('/form_selection_2', type='http', auth='public', website=True)
    def form_selection(self, **kw):
        return request.render('approval_website.form_selection_template2', {
        })
class TestWebsiteController(http.Controller):
    @http.route('/vendor_2', type='http', auth='public', website=True)
    def index(self, **kwargs):
        """顯示一般作業申請表單頁面"""
        values = kwargs.copy()
        approval_types = request.env['approval.type'].sudo().search([('active', '=', True)])
        return request.render('approval_website.vendor_form_template123_2', {
            'main_contractors': request.env['new.res.partner.company'].sudo().search([]),
            'sub_contractors': request.env['new.res.partner.company'].sudo().search([]),
            'approval_types': approval_types,
            'datetime': datetime, 
            'values': values
        })

    @http.route('/vendor_2/submit', type='http', auth='public', website=True, methods=['POST'])
    def vendor_submit(self, **post):
        try:
            _logger.info("開始處理一般作業申請表單提交")
            _logger.info(f"收到的原始日期 - 開始: {post.get('date_assign')}, 結束: {post.get('date_end')}")
            
            # 獲取審批主題
            approval_type = request.env['approval.type'].sudo().browse(int(post.get('approval_type_id')))
            if not approval_type:
                raise ValidationError(_("請選擇有效的審批主題"))

            approval_category = request.env['approval.category'].sudo().search([
                ('name', '=', '平行廠商：一般作業申請表單(限七日)')
            ], limit=1)

            # 獲取主承商和次承商資訊
            main_contractor = request.env['new.res.partner.company'].sudo().browse(int(post.get('main_contractor')))
            sub_contractor = request.env['new.res.partner.company'].sudo().browse(int(post.get('sub_contractor')))
            
            # 本地時區
            local_tz = pytz.timezone('Asia/Taipei')
            _logger.info(f"使用時區: {local_tz}")

            # 處理開始時間和結束時間
            start_dt = DateUtils.convert_to_utc(post.get('date_assign'), '08:00:00')
            end_dt = DateUtils.convert_to_utc(post.get('date_end'), '18:00:00')
            _logger.info(f"最終存儲的 UTC 時間 - 開始: {start_dt}, 結束: {end_dt}")

            # 移除時區資訊
            start_dt_naive = start_dt.replace(tzinfo=None)
            end_dt_naive = end_dt.replace(tzinfo=None)
            _logger.info(f"準備存儲的時間 - 開始: {start_dt_naive}, 結束: {end_dt_naive}")

            start_local = pytz.UTC.localize(start_dt).astimezone(local_tz)
            end_local = pytz.UTC.localize(end_dt).astimezone(local_tz)

            # 創建任務值
            vals = {
                'category_id': approval_category.id,
                'request_owner_id': request.env.user.id,
                'request_status': 'new',
                'name': approval_type.name,  # 使用選擇的審批主題名稱
                # 'email': 'no-email@example.com', # 提供預設值
                'approval_type_id': approval_type.id,  # 關聯審批主題
                'planned_date_begin':start_dt,
                'planned_date_end':  end_dt,
                'main_contractor_id': main_contractor.id,
                'sub_contractor_id': sub_contractor.id,
                'reason': f"""
                    <h3>一般作業申請表單詳情：</h3>
                    <table class="table table-bordered">
                        <tr><th>審批主題</th><td>{approval_type.name}</td></tr>
                        <tr><th>申請人信箱</th><td>{post.get('email')}</td></tr>
                        <tr><th>主承商</th><td>{main_contractor.name}</td></tr>
                        <tr><th>次承商</th><td>{sub_contractor.name}</td></tr>
                        <tr><th>施工內容</th><td>{post.get('work_content')}</td></tr>
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
            _logger.debug(f"原始資料：{post}")

            # 確認請求
            approval_request.sudo().action_confirm()

            return request.render('approval_website.vendor_form_success', {
                'approval_request': approval_request,
                'request_number': approval_request.name,
                'status': '等待審批',
                'planned_date_begin': start_local,
                'planned_date_end': end_local
            })

        except Exception as e:
            _logger.error(f"提交表單時發生錯誤: {str(e)}", exc_info=True)
            return request.render('approval_website.vendor_form_template123_2', {
                'error': str(e),
                'main_contractors': request.env['new.res.partner.company'].sudo().search([]),
                'sub_contractors': request.env['new.res.partner.company'].sudo().search([]),
                'approval_types': request.env['approval.type'].sudo().search([('active', '=', True)]),
                'values': post
            })