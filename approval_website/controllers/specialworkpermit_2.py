from odoo import http, fields, _
from odoo.http import request
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
import logging
import base64
import pytz
_logger = logging.getLogger(__name__)

class SpecialWorkPermitController(http.Controller):
    @http.route(['/special_work_permit/form_2'], type='http', auth="public", website=True)
    def special_work_permit_form(self, **kw):
        try:
            """平行廠商：特殊作業許可單申請頁面"""
            approval_types = request.env['approval.type'].sudo().search([('active', '=', True)])
            main_contractors = request.env['new.res.partner.company'].sudo().search([])
            sub_contractors = request.env['new.res.partner.company'].sudo().search([])

            values = {
                'main_contractors': main_contractors,
                'sub_contractors': sub_contractors,
                'approval_types': approval_types,
                'datetime': datetime,
                'values': kw
            }
            return request.render('approval_website.special_work_permit_form2', values)
        except Exception as e:
            _logger.error(f"Error rendering special work permit form: {str(e)}")
            return request.render('approval_website.error', {
                'error': "系統錯誤，請稍後再試或聯繫管理員。"
            })

    @http.route(['/special_work_permit_2/submit'], type='http', auth="public", website=True, csrf=False, methods=['POST'])
    def submit_special_work_permit(self, **post):
        try:
            _logger.info(f"接收到的表單數據: {post}")

            # 1. 基本驗證
            # 獲取審批主題
            approval_type = request.env['approval.type'].sudo().browse(int(post.get('approval_type_id')))
            if not approval_type:
                raise ValidationError(_("請選擇有效的審批主題"))

            # 獲取審批類型
            approval_category = request.env['approval.category'].sudo().search([
                ('name', '=', '平行廠商：特殊作業許可單')
            ], limit=1)
            if not approval_category:
                raise ValidationError(_("找不到對應的審批類型"))

            # 驗證必填字段
            required_fields = [
                'apply_date', 'entry_work_time', 
                'planned_date_begin', 'planned_date_end', 'work_area',
                'safety_supervisor', 'safety_supervisor_phone',
                'work_supervisor', 'work_supervisor_phone'
            ]
            for field in required_fields:
                if not post.get(field):
                    raise ValidationError(_(f"必填欄位 {field} 缺失"))
                
             # 驗證至少選擇一種特殊作業
            special_work_types = [
                'high_work', 'confined_space', 'hypoxia', 
                'hot_work', 'open_flame', 'electric_work',
                'hanging_work', 'eExcavation_work', 'organic_solvent'
            ]
            if not any(post.get(work_type) == 'on' for work_type in special_work_types):
                raise ValidationError(_("請至少選擇一種特殊作業類型"))

            # 3. 子類型驗證
            # 高架作業驗證
            if post.get('high_work') == 'on':
                high_work_types = ['aerial_platform', 'ceiling_work', 'scaffolding', 'other_high_work']
                if not any(post.get(type) == 'on' for type in high_work_types):
                    raise ValidationError(_("請至少選擇一種高架作業種類"))
                if post.get('other_high_work') == 'on' and not post.get('other_high_work_desc'):
                    raise ValidationError(_("請填寫其他高架作業說明"))

            # 明火作業驗證
            if post.get('open_flame') == 'on':
                flame_work_types = ['cutting_machine', 'acetylene', 'grinder', 'welding', 
                                'spray', 'other_flame_work']
                if not any(post.get(type) == 'on' for type in flame_work_types):
                    raise ValidationError(_("請至少選擇一種明火作業種類"))
                if post.get('other_flame_work') == 'on' and not post.get('other_flame_work_desc'):
                    raise ValidationError(_("請填寫其他明火作業說明"))

            # 熱作業驗證
            if post.get('hot_work') == 'on':
                heat_work_types = ['heat_gun', 'gas_stove', 'oven', 'iron_plate', 'other_heat_work']
                if not any(post.get(type) == 'on' for type in heat_work_types):
                    raise ValidationError(_("請至少選擇一種熱作業種類"))
                if post.get('other_heat_work') == 'on' and not post.get('other_heat_work_desc'):
                    raise ValidationError(_("請填寫其他熱作業說明"))

            # 4. 化學品相關驗證
            if post.get('has_chemicals') == '是' and not request.httprequest.files.get('sds_file'):
                raise ValidationError(_("請上傳 SDS 文件"))

            # 5. 處理文件上傳 - SDS文件
            document_ids = []
            if post.get('has_chemicals') == '是':
                sds_file = request.httprequest.files.get('sds_file')
                if sds_file:
                    # 查找文件資料夾
                    folder = request.env['documents.folder'].sudo().search([
                        ('name', '=', '平行廠商：特殊作業文件')
                    ], limit=1)
                    if not folder:
                        folder = request.env['documents.folder'].sudo().search([], limit=1)

                    file_content = sds_file.read()
                    if file_content:
                        # 創建附件
                        attachment = request.env['ir.attachment'].sudo().create({
                            'name': f"SDS文件 - {sds_file.filename}",
                            'datas': base64.b64encode(file_content),
                            'res_model': 'approval.request',
                            'type': 'binary',
                        })

                        # 創建文件記錄
                        document = request.env['documents.document'].sudo().create({
                            'name': f"SDS文件 - {sds_file.filename}",
                            'folder_id': folder.id,
                            'attachment_id': attachment.id,
                            'res_model': 'approval.request',
                            'owner_id': request.env.user.id,
                            'partner_id': request.env.user.partner_id.id,
                        })
                        document_ids.append(document.id)

            # 6. 獲取承包商資訊
            main_contractor = request.env['new.res.partner.company'].sudo().browse(int(post.get('main_contractor')))
            sub_contractor = request.env['new.res.partner.company'].sudo().browse(int(post.get('sub_contractor')))

            # 7. 時間處理
            local_tz = pytz.timezone('Asia/Taipei')
            if post.get('entry_work_time') == '常日 08:00~18:00':
                # 設置開始時間
                start_naive = datetime.strptime(f"{post.get('planned_date_begin')} 08:00:00", '%Y-%m-%d %H:%M:%S')
                start_local = local_tz.localize(start_naive)
                start_datetime = start_local.astimezone(pytz.UTC).replace(tzinfo=None)
                
                # 設置結束時間
                end_naive = datetime.strptime(f"{post.get('planned_date_end')} 18:00:00", '%Y-%m-%d %H:%M:%S')
                end_local = local_tz.localize(end_naive)
                end_datetime = end_local.astimezone(pytz.UTC).replace(tzinfo=None)
            else:  # 夜間 18:00~07:00
                # 設置開始時間
                start_naive = datetime.strptime(f"{post.get('planned_date_begin')} 18:00:00", '%Y-%m-%d %H:%M:%S')
                start_local = local_tz.localize(start_naive)
                start_datetime = start_local.astimezone(pytz.UTC).replace(tzinfo=None)
                
                # 設置結束時間（隔天）
                end_date = datetime.strptime(post.get('planned_date_end'), '%Y-%m-%d') + timedelta(days=1)
                end_naive = datetime.strptime(f"{end_date.strftime('%Y-%m-%d')} 07:00:00", '%Y-%m-%d %H:%M:%S')
                end_local = local_tz.localize(end_naive)
                end_datetime = end_local.astimezone(pytz.UTC).replace(tzinfo=None)

            # 8. 構建描述文本
            description = f"""
            <div class="approval-description">
                <h3>特殊作業許可申請表單詳情：</h3>
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
                        <th>作業時段：</th>
                        <td>{post.get('entry_work_time')}</td>
                    </tr>
                    <tr>
                        <th>作業開始日期：</th>
                        <td>{post.get('planned_date_begin')}</td>
                    </tr>
                    <tr>
                        <th>作業結束日期：</th>
                        <td>{post.get('planned_date_end')}</td>
                    </tr>
                    <tr>
                        <th>施工區域：</th>
                        <td>{post.get('work_area')}</td>
                    </tr>
                    <tr>
                        <th>是否攜帶化學品：</th>
                        <td>{post.get('has_chemicals')}</td>
                    </tr>
                    <tr>
                        <th>廠商工安：</th>
                        <td>{post.get('safety_supervisor')}</td>
                    </tr>
                    <tr>
                        <th>廠商工安電話：</th>
                        <td>{post.get('safety_supervisor_phone')}</td>
                    </tr>
                    <tr>
                        <th>廠商監工：</th>
                        <td>{post.get('work_supervisor')}</td>
                    </tr>
                    <tr>
                        <th>廠商監工電話：</th>
                        <td>{post.get('work_supervisor_phone')}</td>
                    </tr>
                    <tr>
                        <th>特殊作業類型：</th>
                        <td>
                            {' '.join([
                                '高架作業' if post.get('high_work') == 'on' else '',
                                '局限作業' if post.get('confined_space') == 'on' else '',
                                '缺氧作業' if post.get('hypoxia') == 'on' else '',
                                '熱作業' if post.get('hot_work') == 'on' else '',
                                '明火作業' if post.get('open_flame') == 'on' else '',
                                '電力作業' if post.get('electric_work') == 'on' else '',
                                '吊掛作業' if post.get('hanging_work') == 'on' else '',
                                '開挖作業' if post.get('eExcavation_work') == 'on' else '',
                                '有機溶劑' if post.get('organic_solvent') == 'on' else ''
                            ]).strip()}
                        </td>
                    </tr>"""

            # 添加高架作業種類及說明
            if post.get('high_work') == 'on':
                description += f"""
                    <tr>
                        <th>高架作業種類：</th>
                        <td>
                            {' '.join([
                                '高空工作車' if post.get('aerial_platform') == 'on' else '',
                                '天花板' if post.get('ceiling_work') == 'on' else '',
                                '施工架' if post.get('scaffolding') == 'on' else '',
                                '其他' if post.get('other_high_work') == 'on' else ''
                            ]).strip()}
                        </td>
                    </tr>"""
                if post.get('other_high_work') == 'on':
                    description += f"""
                        <tr>
                            <th>高架作業其他說明：</th>
                            <td>{post.get('other_high_work_desc')}</td>
                        </tr>"""

            # 添加明火作業種類及說明
            if post.get('open_flame') == 'on':
                description += f"""
                    <tr>
                        <th>明火作業種類：</th>
                        <td>
                            {' '.join([
                                '切割機' if post.get('cutting_machine') == 'on' else '',
                                '乙炔' if post.get('acetylene') == 'on' else '',
                                '砂輪機' if post.get('grinder') == 'on' else '',
                                '焊接' if post.get('welding') == 'on' else '',
                                '噴塗' if post.get('spray') == 'on' else ''
                            ]).strip()}
                        </td>
                    </tr>"""
                if post.get('other_flame_work') == 'on':
                    description += f"""
                        <tr>
                            <th>明火作業其他說明：</th>
                            <td>{post.get('other_flame_work_desc')}</td>
                        </tr>"""

            # 添加熱作業種類及說明
            if post.get('hot_work') == 'on':
                description += f"""
                    <tr>
                        <th>熱作業種類：</th>
                        <td>
                            {' '.join([
                                '熱風槍' if post.get('heat_gun') == 'on' else '',
                                '氣爐' if post.get('gas_stove') == 'on' else '',
                                '烤箱' if post.get('oven') == 'on' else '',
                                '鐵板燒' if post.get('iron_plate') == 'on' else ''
                            ]).strip()}
                        </td>
                    </tr>"""
                if post.get('other_heat_work') == 'on':
                    description += f"""
                        <tr>
                            <th>熱作業其他說明：</th>
                            <td>{post.get('other_heat_work_desc')}</td>
                        </tr>"""

            # 關閉表格和div標籤
            description += """
                </table>
            </div>
            """

            # 9. 構建審批請求數據
            approval_vals = {
                'name': f"{approval_type.name} - 特殊作業許可申請",
                'request_owner_id': request.env.user.id,
                'category_id': approval_category.id,
                'approval_type_id': approval_type.id,
                'request_status': 'pending',
                'email': post.get('email'),
                'main_contractor_id': main_contractor.id,
                'sub_contractor_id': sub_contractor.id,
                'work_area': post.get('work_area'),
                'planned_date_begin': start_datetime,
                'planned_date_end': end_datetime,
                'has_chemicals': post.get('has_chemicals'),
                'document_ids': [(6, 0, document_ids)] if document_ids else False,
                'reason': description,
                
                # 特殊作業許可
                'high_work': post.get('high_work') == 'on',
                'confined_space': post.get('confined_space') == 'on',
                'hypoxia': post.get('hypoxia') == 'on',
                'hot_work': post.get('hot_work') == 'on',
                'open_flame': post.get('open_flame') == 'on',
                'electric_work': post.get('electric_work') == 'on',
                'hanging_work': post.get('hanging_work') == 'on',
                'eExcavation_work': post.get('eExcavation_work') == 'on',
                'organic_solvent': post.get('organic_solvent') == 'on',
                
                # 高架作業種類
                'aerial_platform': post.get('aerial_platform') == 'on',
                'ceiling_work': post.get('ceiling_work') == 'on',
                'scaffolding': post.get('scaffolding') == 'on',
                'other_high_work': post.get('other_high_work') == 'on',
                'other_high_work_desc': post.get('other_high_work_desc'),
                
                # 明火作業種類
                'cutting_machine': post.get('cutting_machine') == 'on',
                'acetylene': post.get('acetylene') == 'on',
                'grinder': post.get('grinder') == 'on',
                'welding': post.get('welding') == 'on',
                'spray': post.get('spray') == 'on',
                'other_flame_work': post.get('other_flame_work'),
                
                # 熱作業種類
                'heat_gun': post.get('heat_gun') == 'on',
                'gas_stove': post.get('gas_stove') == 'on',
                'oven': post.get('oven') == 'on',
                'iron_plate': post.get('iron_plate') == 'on',
                'drying_box': post.get('drying_box') == 'on',
                'other_heat_work': post.get('other_heat_work'),
                
                # 人員資訊
                'safety_supervisor': post.get('safety_supervisor'),
                'safety_supervisor_phone': post.get('safety_supervisor_phone'),
                'work_supervisor': post.get('work_supervisor'),
                'work_supervisor_phone': post.get('work_supervisor_phone'),
            }

            # 10. 創建審批請求
            approval_request = request.env['approval.request'].sudo().create(approval_vals)

            # 11. 更新文件關聯
            if document_ids:
                # 更新 documents.document 記錄
                request.env['documents.document'].sudo().browse(document_ids).write({
                    'res_id': approval_request.id,
                    'name': f"{approval_request.sequence_number} - SDS文件 - {sds_file.filename}"
                })

                # 更新附件關聯
                for doc in request.env['documents.document'].sudo().browse(document_ids):
                    if doc.attachment_id:
                        doc.attachment_id.write({
                            'res_id': approval_request.id,
                            'name': f"{approval_request.sequence_number} - SDS文件 - {sds_file.filename}"
                        })

                # 添加消息記錄
                approval_request.sudo().message_post(
                    body=f'已上傳 {approval_request.sequence_number} - SDS文件',
                    attachment_ids=[doc.attachment_id.id for doc in request.env['documents.document'].sudo().browse(document_ids) if doc.attachment_id]
                )

            # 12. 確認審批請求
            approval_request.action_confirm()

            # 13. 返回成功頁面
            return request.render('approval_website.vendor_form_success', {
                'approval_request': approval_request,
                'request_number': approval_request.sequence_number,
            })

        except ValidationError as e:
            _logger.error(f"表單驗證錯誤: {str(e)}")
            return request.render("approval_website.special_work_permit_form2", {
                'error': str(e),
                'values': post,
                'main_contractors': request.env['new.res.partner.company'].sudo().search([]),
                'sub_contractors': request.env['new.res.partner.company'].sudo().search([]),
                'approval_types': request.env['approval.type'].sudo().search([('active', '=', True)]),
            })
        except Exception as e:
            _logger.error(f"處理表單提交時發生錯誤: {str(e)}", exc_info=True)
            return request.render('approval_website.vendor_form_error', {
                'error': _("系統錯誤，請稍後再試或聯繫管理員。")
            })