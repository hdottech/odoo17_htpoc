from odoo.tests import TransactionCase
from odoo.exceptions import ValidationError

class TestClassificationLevel(TransactionCase):

    def setUp(self):
        super(TestClassificationLevel, self).setUp()
        self.classification_level_model = self.env['classification_level']

    def test_create_level(self):
        level_data = {
            'name': 'LEVEL 001',
            'sequence': 10,
            'description': '缺失等級說明',
            'level': '缺失等級分類說明',
        }
        classification = self.classification_level_model.create(level_data)
        self.assertEqual(classification.name, 'LEVEL 001')
        self.assertEqual(classification.sequence, 10)
        self.assertEqual(classification.description, '缺失等級說明')
        self.assertEqual(classification.level, '缺失等級分類說明')

    def test_read_level(self):
        new_level = self.classification_level_model.create({
            'name': 'LEVEL 002',
            'sequence': 15,
            'description': '描述',
            'level': '分類'
        })
        level = new_level.read(['name', 'sequence', 'description', 'level'])
        self.assertEqual(level[0]['name'], 'LEVEL 002')
        self.assertEqual(level[0]['sequence'], 15)
        self.assertEqual(level[0]['description'], '描述')
        self.assertEqual(level[0]['level'], '分類')

    def test_update_level(self):
        level = self.classification_level_model.create({
            'name': 'LEVEL 003',
            'sequence': 20,
            'description': '描述',
            'level': '分類'
        })
        level.write({'sequence': 69})
        self.assertEqual(level.sequence, 69)

    def test_update_with_invalid_value(self):
        with self.assertRaises(ValidationError) as context:
            level = self.classification_level_model.create({
                'name': 'LEVEL 003',
                'sequence': 70,
                'description': '描述',
                'level': '分類'
            })
            level.write({'sequence': 150})
        self.assertEqual(str(context.exception), "Sequence must be less than 100")

    def test_delete_level(self):
        level = self.classification_level_model.search({
            'name': 'LEVEL 010',
            'sequence': 30,
            'description': '描述',
            'level': '分類'
        }) 
        level.unlink()
        check_level = self.classification_level_model.search([('name', '=', 'LEVEL 010')])
        self.assertFalse(check_level)
