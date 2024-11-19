# -*- coding: utf-8 -*-
from odoo import http, fields, _
from odoo.http import request
import base64
import logging
from datetime import datetime,timedelta
from odoo.exceptions import ValidationError
from ..utils.date_utils import DateUtils

_logger = logging.getLogger(__name__)

class SafetyOperationController(http.Controller):
    @http.route(['/safety_operation'], type='http', auth="public", website=True)
    def safety_operation_form(self, **kw):
        try:
            approval_types = request.env['approval.type'].sudo().search([('active', '=', True)])
            approval_category = request.env['approval.category'].sudo().search([
                ('name', '=', '安全設施拆除作業申請表單')
            ], limit=1)
            # 計算日期範圍
            today = datetime.now().strftime('%Y-%m-%d')
            max_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')

            if not approval_category:
                return request.render('approval_website.vendor_form_error', {
                    'error': _("找不到對應的審批類型")
                })

            values = {
                'main_contractors': request.env['new.res.partner.company'].sudo().search([]),
                'sub_contractors': request.env['new.res.partner.company'].sudo().search([]),
                'approval_types': approval_types,
                'approval_category': approval_category,
                'min_date': today,
                'max_date': max_date,
                'values': kw or {}
            }

            return request.render('approval_website.safety_form_template', values)
            
        except Exception as e:
            _logger.error(f'載入表單時發生錯誤: {str(e)}', exc_info=True)
            _logger.error(f'Request params: {kw}')
            _logger.error(f'User: {request.env.user}')
            return request.render('approval_website.vendor_form_error', {
                'error': '載入表單時發生錯誤，請稍後再試'
            })

    @http.route(['/safety_operation/submit'], type='http', auth="public", website=True, csrf=False, methods=['POST'])
    def safety_operation_submit(self, **post):
        try:
            # 獲取審批主題
            approval_type = request.env['approval.type'].sudo().browse(int(post.get('approval_type_id')))
            if not approval_type:
                raise ValidationError(_("請選擇有效的審批主題"))

            approval_category = request.env['approval.category'].sudo().search([
                ('name', '=', '安全設施拆除作業申請表單')
            ], limit=1)

            # 時間轉換
            construction_date = post.get('construction_date')
            if not construction_date:
                raise ValidationError(_("請選擇施工日期"))
            # 驗證日期是否在七天內
            today = datetime.now().date()
            selected_date = datetime.strptime(construction_date, '%Y-%m-%d').date()
            date_diff = (selected_date - today).days

            if date_diff < 0:
                raise ValidationError(_("不能選擇過去的日期"))
            if date_diff > 7:
                raise ValidationError(_("施工日期必須在七天內"))
            # 繼續處理時間轉換
            try:
                start_datetime, end_datetime = DateUtils.set_time_range(construction_date)
                _logger.info(f"設置時間範圍 - 開始: {start_datetime}, 結束: {end_datetime}")
            except Exception as e:
                _logger.error(f"時間轉換錯誤: {str(e)}")
                raise ValidationError(_("時間設置錯誤"))
            

            # 處理文件上傳
            document_ids = []
            attachment_ids = []
            files = request.httprequest.files.getlist('attachment[]')
            
            if files:
                # 先找到 Approvals 資料夾
                approval_folder = request.env['documents.folder'].sudo().search([
                    ('name', '=', '審批')
                ], limit=1)

                if not approval_folder:
                    _logger.error("找不到 審批 資料夾")
                    raise ValidationError(_("系統文件夾配置錯誤，請聯繫管理員"))

                # 在 Approvals 資料夾下尋找或創建安全設施拆除文件資料夾
                folder = request.env['documents.folder'].sudo().search([
                    ('name', '=', '安全設施拆除文件'),
                    ('parent_folder_id', '=', approval_folder.id)
                ], limit=1)

                if not folder:
                    # 如果不存在，創建資料夾
                    try:
                        folder = request.env['documents.folder'].sudo().create({
                            'name': '安全設施拆除文件',
                            'parent_folder_id': approval_folder.id,
                            'description': '安全設施拆除作業申請的相關文件'
                        })
                        _logger.info(f"成功創建資料夾: {folder.name}, 父資料夾: {folder.parent_folder_id.name}")
                    except Exception as e:
                        _logger.error(f"創建資料夾失敗: {str(e)}")
                        raise ValidationError(_("無法創建文件資料夾，請聯繫管理員"))

                # 文件處理邏輯
                for upload in files:
                    file_content = upload.read()
                    if file_content:
                        try:
                            # 創建附件
                            attachment = request.env['ir.attachment'].sudo().create({
                                'name': upload.filename,
                                'datas': base64.b64encode(file_content),
                                'res_model': 'approval.request',
                                'type': 'binary',
                            })
                            attachment_ids.append(attachment.id)

                            # 創建文件記錄
                            document = request.env['documents.document'].sudo().create({
                                'name': upload.filename,
                                'folder_id': folder.id,
                                'attachment_id': attachment.id,
                                'res_model': 'approval.request',
                                'owner_id': request.env.user.id,
                                'partner_id': request.env.user.partner_id.id,
                            })
                            document_ids.append(document.id)
                            _logger.info(f"文件 {upload.filename} 上傳成功")
                        except Exception as e:
                            _logger.error(f"文件上傳失敗: {str(e)}")
                            raise ValidationError(_("文件上傳失敗，請聯繫管理員"))


            # 創建審批請求值
            vals = {
                'category_id': approval_category.id,
                'name': approval_type.name,
                'approval_type_id': approval_type.id,
                'request_owner_id': request.env.user.id,
                'request_status': 'new',
                'planned_date_begin': start_datetime,
                'planned_date_end': end_datetime,
                'main_contractor_id': int(post.get('main_contractor')),
                'sub_contractor_id': int(post.get('sub_contractor')),
                'document_ids': [(6, 0, document_ids)] if document_ids else False,  # 關聯文件
                'reason': f"""
                    <h3>安全設施施工拆除作業申請表單詳情：</h3>
                    <table class="table table-bordered">
                        <tr><th>申請人信箱</th><td>{post.get('email')}</td></tr>
                        <tr><th>拆除項目</th><td>{post.get('removal_items')}</td></tr>
                        <tr><th>樓別/樓層/柱位</th><td>{post.get('location')}</td></tr>
                        <tr><th>拆除原因</th><td>{post.get('removal_reason')}</td></tr>
                        <tr><th>替代防護措施</th><td>{post.get('alternative_measures')}</td></tr>
                    </table>
                """
            }

            # 處理文件上傳
            # attachment_ids = []
            # files = request.httprequest.files.getlist('attachment[]')
            
            # if files:
            #     for upload in files:
            #         file_content = upload.read()
            #         if file_content:
            #             attachment = request.env['ir.attachment'].sudo().create({
            #                 'name': upload.filename,
            #                 'datas': base64.b64encode(file_content),
            #                 'res_model': 'approval.request',  # 關聯到審批模型
            #                 'type': 'binary',
            #                 'res_id': False,
            #             })
            #             attachment_ids.append(attachment.id)

            # 如果有附件，添加到審批請求中
            # if attachment_ids:
            #      vals['message_attachment_ids'] = [(6, 0, attachment_ids)]
            # if attachment_ids:
            #     vals.update({
            #         'message_attachment_ids': [(4, attachment_id) for attachment_id in attachment_ids]
            #     })

            # 創建審批請求
            approval_request = request.env['approval.request'].sudo().create(vals)

            # 更新文件和附件的關聯
            if document_ids:
                # 更新文件關聯
                request.env['documents.document'].sudo().browse(document_ids).write({
                    'res_id': approval_request.id,
                    # 'approval_type_id': approval_type.id,
                    'name': f"{approval_request.sequence_number} - {approval_type.name}"
                })
                
                # 更新附件關聯
                request.env['ir.attachment'].sudo().browse(attachment_ids).write({
                    'res_id': approval_request.id,
                    # 'approval_type_id': approval_type.id,
                    'name': f"{approval_request.sequence_number} - {approval_type.name}"
                })

                # 添加消息記錄
                approval_request.sudo().message_post(
                    body='已上傳相關文件',
                    attachment_ids=attachment_ids
                )
            

            # 確認請求
            approval_request.sudo().action_confirm()

            return request.render('approval_website.vendor_form_success', {
                'approval_request': approval_request,
                'request_number': approval_request.sequence_number,
            })

        except Exception as e:
            _logger.error(f'處理時發生錯誤: {str(e)}', exc_info=True)
            values = {
                'error': _('發生錯誤，請稍後再試'),
                'main_contractors': request.env['new.res.partner.company'].sudo().search([]),
                'sub_contractors': request.env['new.res.partner.company'].sudo().search([]),
                'approval_types': request.env['approval.type'].sudo().search([('active', '=', True)]),
                'values': post
            }
            return request.render('approval_website.safety_form_template', values)