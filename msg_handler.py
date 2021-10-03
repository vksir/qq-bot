import re
import json
import requests

from log import log
from config import DataParser


class MsgHandler:
    def __init__(self, cfg: dict):
        self._cfg = cfg

        dst_server_lst = self._cfg.get('dst_server', [])
        self._dst_server_dict = {d['name']: d['ip'] for d in dst_server_lst}

    def __call__(self, parser: DataParser) -> str:
        msg = parser.msg
        if not msg.startswith('#'):
            user_id = self._cfg.get('turing', {}).get('user_id')
            api_key = self._cfg.get('turing', {}).get('api_key')
            turing_handler = TuringHandler(user_id, api_key)
            return turing_handler(parser)

        for name, ip in self._dst_server_dict.items():
            if re.search(r'^#\s*%s' % name, msg):
                dst_handler = DSTHandler(name, ip)
                return dst_handler(parser)

        return 'Invalid command.'


class DSTHandler:
    def __init__(self, name: str, ip: str, port=5800):
        self._name = name
        self._ip = ip
        self._port = port

    def __call__(self, parser: DataParser) -> str:
        who, is_admin = parser.nickname, parser.is_admin
        cmd, param = re.search(r'^#\s*%s\s*(\S+)\s*(.*)' % self._name, parser.msg, re.S).groups()
        log.info(f'recv dst_server control: cmd={cmd}, param={param}, '
                 f'who={who}, is_admin={is_admin}, msg={parser.msg}')

        if cmd not in ['mod-list', 'player-list', 'say'] and not is_admin:
            return 'Permission denied.'

        method = 'ctr_' + cmd.replace('-', '_')
        if cmd in ['start', 'stop', 'restart', 'update', 'mod-list', 'player-list', 'create-cluster']:
            method = 'ctr_action'

        if hasattr(self, method):
            data = getattr(self, method)(cmd, param, who)
            if data.get('ret'):
                info = data.get('info')
                info = f': {info}' if info else ''
                return f'{self._name} {cmd} failed{info}.'

            return self._get_response_msg(cmd, data)
        else:
            return 'Method not found.'

    def _get_response_msg(self, cmd: str, data: dict) -> str:
        resp_msg = f'{self._name}: {cmd} success.\n'

        player_lst = data.get('player_list')
        if player_lst is not None:
            resp_msg += '\n当前在线玩家:\n'
            if not player_lst:
                resp_msg += '无\n'
            else:
                for player in player_lst:
                    resp_msg += f'{player}\n'

        mod_lst = data.get('mod_list')
        if mod_lst is not None:
            resp_msg += '\nMod 列表:\n'
            if not mod_lst:
                resp_msg += '无\n'
            else:
                for i, mod_id in enumerate(mod_lst):
                    resp_msg += f'  ({i + 1}) {mod_id}\n'

        return resp_msg[:-1]

    def ctr_action(self, *args) -> dict:
        cmd = args[0]
        data = self._control(cmd)
        return data

    def ctr_mod_add(self, *args) -> dict:
        cmd, param = args[:2]
        if param.strip().startswith('return'):
            kwargs = dict(mod_overrides=param)
        else:
            kwargs = dict(mod_lst=param.split())
        data = self._control(cmd, kwargs)
        return data

    def ctr_mod_del(self, *args) -> dict:
        cmd, param = args[:2]
        data = self._control(cmd, dict(mod_lst=param.split()))
        return data

    def ctr_say(self, *args) -> dict:
        cmd, param, name = args[:3]
        say_word = f'{name}: {param}'
        data = self._control('say', dict(msg=say_word))
        return data

    def _control(self, method: str, kwargs: dict = None) -> dict:
        log.info(f'begin control: method={method}, kwargs={kwargs}')
        url = f'http://{self._ip}:{self._port}'
        data = {
            'method': method.replace('-', '_'),
            'kwargs': kwargs or {}
        }

        try:
            resp = requests.post(url, data=json.dumps(data))
        except requests.ConnectionError as e:
            log.error(f'post failed: error={e}')
            return self.response(1, info='connect refused')

        try:
            resp_data = json.loads(resp.text)
            log.info(f'control success: resp_data={resp_data}')
            return resp_data
        except json.JSONDecodeError as e:
            log.error(f'json decode failed: resp_text={resp.text}, error={e}')
            return self.response(1, info=resp.text)

    @staticmethod
    def response(ret: int,
                 info: str = None,
                 player_list: list = None,
                 mod_list: list = None) -> dict:
        return locals()


class TuringHandler:
    def __init__(self, user_id: str, api_key: str):
        self._user_id = user_id
        self._api_key = api_key

    def __call__(self, parser: DataParser) -> str:
        msg = parser.msg
        url = 'http://openapi.turingapi.com/openapi/api/v2'
        data = {
            "reqType": 0,
            "perception": {
                "inputText": {
                    "text": msg
                }
            },
            "userInfo": {
                "apiKey": self._api_key,
                "userId": self._user_id
            }
        }

        resp = requests.post(url, data=json.dumps(data))

        try:
            resp_data = json.loads(resp.text)
        except json.JSONDecodeError:
            info = 'json decode failed'
            log.error(f'{info}: resp_text={resp.text}')
            return info

        try:
            results = resp_data['results']
            for res in results:
                res_type = res['resultType']
                if res_type == 'text':
                    text = res['values']['text']
                    return text
        except Exception as e:
            info = 'get text failed'
            log.error(f'{info}: resp_data={resp_data}, error={e}')
            return info


