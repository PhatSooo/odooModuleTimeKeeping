from odoo import models, fields, api

import requests, json
from requests.auth import HTTPDigestAuth
from base64 import b64encode
from datetime import datetime, timedelta, timezone

from ..util.constant import *

class ShiBa(models.Model):
    _name = "shi.ba"
    _description = "Shi Ba"

    # my_json_field = JsonField(string='My JSON Field')


    # attendance_state = fields.Integer(string='Attendance Events')
    attendance_state = fields.Selection([('0', 'Null'),('1', 'Check In'),('2', 'Break Out'),('3', 'Break In'),('4', 'Check Out')], string='Attendance Events')
    card_name = fields.Char(string='Name')
    create_time = fields.Integer(string='Time')
    user_id = fields.Integer(string='User ID.')
    mask = fields.Boolean(string='Mask')
    status = fields.Boolean(string='Status')
    method = fields.Selection([('0', 'Null'),('15', 'Face')], string='Mode')
    image_url = fields.Char(string='Image')
    recognize_number = fields.Integer(string='RecNo')

    # Preprocess Fields Before Loading To Views
    image_data = fields.Binary(string='Preview', compute='_compute_image_data')
    formatted_time = fields.Char(string='Formatted Time', compute='_compute_formatted_time')

    # Date Fields
    date_from = fields.Date(string='From', store=False)
    date_to = fields.Date(string='To', store=False)

    @api.depends('image_url')
    def _compute_image_data(self):
        for record in self:
            url = API_SERVER + 'FileManager.cgi?action=downloadFile&fileName=' + record.image_url
            response = requests.get(url, auth=HTTPDigestAuth(USERNAME, PASSWORD))

            if response.status_code == 200:
                self.image_data = b64encode(response.content)

            else:
                print(f'An error occurred: {response.status_code} {response.reason}')
    
    @api.depends('create_time')
    def _compute_formatted_time(self):
        for record in self:
            dt = datetime.fromtimestamp(record.create_time, timezone(timedelta(hours=7)))
            record.formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
    
    def call_api(self):
        url = API_SERVER + 'recordFinder.cgi?action=find&name=AccessControlCardRec&StartTime=' + START_UNIX + '&EndTime=' + END_UNIX +'1689181199'
        response = requests.get(url, auth=HTTPDigestAuth(USERNAME, PASSWORD))

        if response.status_code == 200:
            data = response.text
            lines = data.split('\n')
            result = {}
            for line in lines:
                if not line:
                    continue
                key, value = line.split('=', 1)
                value = value.strip()
                if value.isdigit():
                    value = int(value)
                elif not value:
                    value = None
                if '[' in key:
                    key, sub_key = key.split('.')
                    index = int(key[key.index('[') + 1:key.index(']')])
                    key = key[:key.index('[')]
                    if key not in result:
                        result[key] = []
                    if len(result[key]) <= index:
                        result[key].append({})
                    result[key][index][sub_key] = value
                else:
                    result[key] = value

            json_data = json.dumps(result, ensure_ascii=False, indent=4)
            data = json.loads(json_data)

            return data
        else:
            print(f'An error occurred: {response.status_code} {response.reason}')

    def init(self):
        field_mapping = {
            'attendance_state': 'AttendanceState',
            'card_name': 'CardName',
            'create_time': 'CreateTime',
            'user_id': 'UserID',
            'mask': 'Mask',
            'status': 'Status',
            'method': 'Method',
            'image_url': 'URL',
            'recognize_number': 'RecNo',
        }

        data = self.call_api()
        model_data = {}

    
        for dt in data['records']:
            for field, key in field_mapping.items():
                if field == 'attendance_state':
                    model_data[field] = str(dt[key])
                elif field == 'method':
                    model_data[field] = str(dt[key])
                else:
                    model_data[field] = dt[key]

            existing_record = self.search([('create_time', '=', dt['CreateTime']), ('recognize_number', '=', dt['RecNo'])], limit=1)

            if existing_record:
                existing_record.write(model_data)
            else:
                self.create(model_data)