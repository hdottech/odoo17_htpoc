from odoo import http,_
from odoo.http import request
import logging
from odoo import fields
from datetime import timedelta, datetime, date

_logger = logging.getLogger(__name__)

class WebsiteController(http.Controller):
    @http.route(['/approvals'], type='http', auth="user", website=True)
    def approval_type_list(self, **kw):
        # 獲取當前website
        website = request.website
        
        # 檢查當前用戶權限
        current_user = request.env.user
        is_manager = current_user.has_group('approvals.group_approval_manager')
        # 添加日誌輸出來檢查用戶組
        _logger.info(f"當前用戶: {current_user.name}")
        # _logger.info(f"用戶組: {current_user.groups_id.mapped('name')}")
        _logger.info(f"是否為管理員: {is_manager}")
        requests = request.env['approval.request'].search([])
        # for req in requests:
        #     _logger.info(f"Request {req.id} fields: {req._fields.keys()}")
        #     _logger.info(f"Request {req.id} refuse_reason: {hasattr(req, 'refuse_reason')}")
        
        # 獲取所有審批類型
        categories = request.env['approval.category'].search([])
        
        
        values = {
            'categories': categories,
            'is_manager': is_manager,
            'current_user': current_user,
            'website': website,
            'title': '審批類型列表'
        }
        
        return request.render("approval_website.approval_website_template", values)
    @http.route(['/approval/<model("approval.category"):category>'], type='http', auth="user", website=True)
    def approval_type_detail(self, category, **kw):
        current_user = request.env.user
        is_manager = current_user.has_group('approvals.group_approval_manager')
        
        _logger.info(f"當前用戶: {current_user.id}, 用戶名: {current_user.name}")
        _logger.info(f"是否為管理員: {is_manager}")

        # 基礎域過濾條件
        domain = [('category_id', '=', category.id)]

        # 處理日期篩選
        date_from = kw.get('date_from')
        date_to = kw.get('date_to')
        if date_from and date_to:
            domain += [
                '|',
                '&',
                ('date_start', '>=', date_from),
                ('date_start', '<=', date_to),
                '&',
                ('date_end', '>=', date_from),
                ('date_end', '<=', date_to)
            ]
        
        if not is_manager:
            # 非管理員只能看到自己的審批請求
            domain += [
                '|',
                ('request_owner_id', '=', current_user.id),  # 審批請求的擁有者
                ('create_uid', '=', current_user.id)  # 審批請求的創建者
            ]
            _logger.info(f"非管理員用戶，應用權限過濾")
        else:
            _logger.info(f"管理員用戶，可查看所有審批請求")

        # 處理篩選條件
        filter_type = kw.get('filter')
        if filter_type:
            if filter_type == 'my':
                domain += ['|', ('request_owner_id', '=', current_user.id), ('create_uid', '=', current_user.id)]
            elif filter_type == 'today':
                today = fields.Date.today()
                domain += ['|', ('date_start', '=', today), ('date_end', '=', today)]
            elif filter_type == 'week':
                today = fields.Date.today()
                week_start = today - timedelta(days=today.weekday())
                week_end = week_start + timedelta(days=6)
                domain += [
                    '|',
                    '&', ('date_start', '>=', week_start), ('date_start', '<=', week_end),
                    '&', ('date_end', '>=', week_start), ('date_end', '<=', week_end)
                ]

        # 處理搜尋
        search = kw.get('search')
        if search:
            domain += ['|', '|',
                ('name', 'ilike', search),
                ('sequence_number', 'ilike', search),
                ('request_status', 'ilike', search)
            ]

        # 獲取審批請求並加入排序
        requests = request.env['approval.request'].with_user(current_user).search(
            domain,
            order='sequence_number desc'  # 審批編號降序排序
        )
        # _logger.info(f"找到的審批請求數量: {len(requests)}")

        # 審批請求查詢與分組處理
        grouped_requests = []
        groupby = kw.get('groupby')
        if groupby:
            if groupby == 'status':
                statuses = ['new', 'pending', 'approved', 'refused', 'cancel']
                status_names = {
                    'new': '新建',
                    'pending': '待審批',
                    'approved': '已批准',
                    'refused': '已拒絕',
                    'cancel': '已取消'
                }
                for status in statuses:
                    status_requests = requests.filtered(lambda r: r.request_status == status)
                    if status_requests:
                        grouped_requests.append({
                            'name': status_names.get(status, status),
                            'requests': status_requests
                        })
            elif groupby == 'user':
                users = requests.mapped('request_owner_id')
                for user in users:
                    user_requests = requests.filtered(lambda r: r.request_owner_id == user)
                    if user_requests:
                        grouped_requests.append({
                            'name': user.name,
                            'requests': user_requests
                        })
            elif groupby == 'date':
                today = datetime.now().date()
                overdue_requests = requests.filtered(lambda r: r.date_end and r.date_end.date() < today)
                today_requests = requests.filtered(lambda r: r.date_end and r.date_end.date() == today)
                future_requests = requests.filtered(lambda r: r.date_end and r.date_end.date() > today)
                no_deadline_requests = requests.filtered(lambda r: not r.date_end)
                
                if overdue_requests:
                    grouped_requests.append({'name': '已逾期', 'requests': overdue_requests})
                if today_requests:
                    grouped_requests.append({'name': '今日到期', 'requests': today_requests})
                if future_requests:
                    grouped_requests.append({'name': '未來到期', 'requests': future_requests})
                if no_deadline_requests:
                    grouped_requests.append({'name': '無期限', 'requests': no_deadline_requests})

        # _logger.info(f"最終搜索條件: {domain}")
        # 保存搜尋前的展開狀態
        expand_state = kw.get('expand_state', 'all')

        return request.render("approval_website.approval_type_detail_template", {
            'approval_type': category,  # 注意這裡改成 category
            'requests': requests,
            'grouped_requests': grouped_requests,
            'groupby': groupby,
            'filter_type': filter_type,
            'search': search,
            'is_manager': is_manager,
            'current_user': current_user,
            'date_from': date_from,
            'date_to': date_to,
            'expand_state': expand_state
        })

    @http.route(['/approval-request/<model("approval.request"):approval_request>'], type='http', auth="user", website=True)
    def approval_request_detail(self, approval_request, **kw):
        current_user = request.env.user
        is_manager = current_user.has_group('approvals.group_approval_manager')
        
        _logger.info(f"當前用戶: {current_user.id}, 用戶名: {current_user.name}")
        _logger.info(f"是否為管理員: {is_manager}")

        # 檢查記錄是否存在
        if not approval_request.exists():
            return request.render('website.404')
            
        # 檢查用戶權限
        can_access = False
        
        # 1. 檢查是否為管理員
        if is_manager:
            can_access = True
        # 2. 檢查是否為申請人
        elif approval_request.request_owner_id == current_user:
            can_access = True
        # 3. 檢查是否為審批人
        elif current_user.id in approval_request.approver_ids.mapped('user_id.id'):
            can_access = True
        # 4. 檢查是否為創建者
        elif approval_request.create_uid == current_user:
            can_access = True
            
        if not can_access:
            _logger.warning(f"用戶 {current_user.name} 嘗試訪問無權限的表單 {approval_request.id}")
            return request.render('website.403')

        # 使用 sudo() 來獲取完整記錄
        approval_request = approval_request.sudo()
        
        _logger.info(f"用戶 {current_user.name} 成功訪問表單 {approval_request.id}")
        
        values = {
            'approval_request': approval_request,
            'is_manager': is_manager,
            'current_user': current_user,
        }
        
        return request.render("approval_website.approval_request_detail_template", values)
        


