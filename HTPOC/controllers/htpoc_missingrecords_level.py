import json

from odoo import http
from odoo.http import request, Response

from ..utils.authutils import authenticate

class HtpocClassificationController(http.Controller):
    @http.route('/classification_level', auth="public", methods=['GET'])
    @authenticate
    def get_classification_level(self, **kwargs):
        levels = request.env['classification_level'].search([])

        classification_levels = []
        for level in levels:
            classification_levels.append({
                'id': level.id,
                'name': level.name,
                # 'description': level.description,
                'level': level.level
            })

        return Response(json.dumps(classification_levels), content_type="application/json")
    
    
    @http.route('/classification_level/<int:level_id>', auth="public", methods=['GET'])
    @authenticate
    def get_classification_level_by_id(self, level_id, **kwargs):
        try:
            level = request.env['classification_level'].browse(level_id)

            response_data = {
                'id': level.id,
                'name': level.name,
                'level': level.level
            }

            return Response(json.dumps(response_data), content_type="application/json")
        except Exception as e:
            return Response(json.dumps({'error': 'something went wrong', 'error_detail': str(e)}), status=500)
        
    @http.route('/classification_level', auth="public", methods=['POST'], csrf=False)
    @authenticate
    def create_level(self, **kwargs):
        try:
            request_data = json.loads(request.httprequest.data.decode("utf-8"))

            name = request_data.get('name')
            level_value = request_data.get('level')

            if not all([name, level_value]):
                return Response("Bad Request: name and level are required", status=400)

            check_level_exist = request.env['classification_level'].search([('name', '=', name)])
            if check_level_exist:
                return Response(f"level with this name ({name}) is already exist!", status=400)

            new_level = request.env['classification_level'].create({
                'name': name,
                'level': str(level_value),
            })

            response = json.dumps({'id': new_level.id, 'name': new_level.name, 'level': new_level.level})
            return Response(response, content_type="application/json")

        except Exception as e:
            return Response(f"There is error occured: {str(e)}", status=500)
        
    @http.route('/classification_level/<int:level_id>', auth="public", methods=['PUT'], csrf=False)
    @authenticate
    def update_level(self, level_id, **kwargs):
        try:
            # 根據 ID 獲取記錄
            level = request.env['classification_level'].browse(level_id)
            if not level.exists():
                return Response("Record not found", status=404)
            
            # 解析請求數據
            updated_data = json.loads(request.httprequest.data.decode("utf-8"))
            name = updated_data.get('name')
            level_value = updated_data.get('level')

            # 更新記錄
            level.write({
                'name': name,
                'level': level_value  # 確保 level 是正確的值
            })

            # 構建響應數據
            response_data = {
                'id': level.id,
                'name': level.name,
                'level': level.level
            }
            
            response = json.dumps(response_data)
            return Response(response, content_type="application/json")
        except Exception as e:
            return Response(f"There is error occurred: {str(e)}", status=500)
        
    @http.route('/classification_level/<int:level_id>', auth="public", methods=['DELETE'], csrf=False)
    @authenticate
    def delete_level(self, level_id, **kwargs):
        
        # 根據 ID 獲取記錄
        level = request.env['classification_level'].browse(level_id)
        level.unlink()

        response_data = {
            'id': level.id,
            'message':f"編號 #{level.id} 缺失等級已刪除"
        }
            
           
        return Response(json.dumps(response_data), content_type="application/json")
