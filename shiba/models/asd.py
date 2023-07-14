from odoo.fields import Field
import psycopg2
from ..util.constant import *
import requests, json
from requests.auth import HTTPDigestAuth

class JsonField(Field):
    """ Represents a postgresql Json column (JSON values are mapped to the Python equivalent type of list/dict). """
    type = 'json' # Odoo type of the field (string)

    def read(self, records):
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