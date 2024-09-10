from odoo.tests import HttpCase
import requests
import json


class TestMissingRecordsLevelAPI(HttpCase):
    def setUp(self):
        super(TestMissingRecordsLevelAPI, self).setUp()
        self.base_url ="http://localhost:8069"
        self.auth_token ="7fd48d25-7c2d-4636-b361-110a855db40f"
        self.session_id = self.authenticate

    def authenticate(self):
        url = f'{self.base_url}/web/session/authenticate'
        headers = {'Content-Type':'application/json'}
        data = {
            "jsonrpc": "2.0",
            "method":"call",
            "id":1,
            "method": "login",
            "params": {
                "db" : "odoo17_0709",
                "login" : "admin",
                "password" : "admin"

            },
        }
        response = requests.post(url, headers=headers, data=json.dumps(data))

        def test_get_level(self):
            url = f'{self.base_url}/classification_level'
            headers = {
                'Authorization' : self.auth_token,
                'Cookie' : f'session_id={self.session_id}'
            }
            response = requests.get(url, headers=headers)
            self.assertEqual(response.status_code, 200)

