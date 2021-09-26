import json
import constants

from log import log
from constants import *
from tools import run_cmd


class DataParser:
    """OneBot Response Data Parser

    see https://docs.go-cqhttp.org/guide
    """

    def __init__(self, data: dict):
        log.debug(f'recv resp_data: {data}')

        # self
        self.self_id = data.get('self_id')

        # private and group msg
        self.message_type: str = data.get('message_type')
        self.user_id: int = data.get('user_id')
        self.msg = self._get_msg(data)
        sender = data.get('sender', {})
        self.nickname = sender.get('card') or sender.get('nickname') or self.user_id
        role = sender.get('role')
        self.is_admin = self.message_type == 'private' or role in ['owner', 'admin ']

        # only group msg
        self.group_id: int = data.get('group_id')

    def _get_msg(self, data: dict) -> str:
        """remove @QQ_BOT in msg"""

        msg: str = data.get('message')
        msg = msg.replace(f'[CQ:at,qq={self.self_id}]', '').strip()
        return msg


class CfgParser:
    def __init__(self):
        if not os.path.exists(CFG_PATH):
            self._init_cfg()

    @staticmethod
    def read() -> dict:
        with open(CFG_PATH, 'r') as f:
            return json.load(f)

    @staticmethod
    def write(cfg: dict):
        with open(CFG_PATH, 'w') as f:
            json.dump(cfg, f, indent=4)

    def _init_cfg(self):
        cfg = {
            'qq_bot': {
                'id': ''
            },
            'turing': {
                'user_id': '',
                'api_key': ''
            },
            'dst_server': [
                {
                    'name': '',
                    'ip': ''
                }
            ]
        }
        self.write(cfg)
        print(f'Please edit the configuration file.\n'
              f'You could run this command:\n'
              f'  vim {CFG_PATH}')
        exit()


def init_path():
    for dirname in dir(constants):
        if dirname.endswith('DIR') and not os.path.exists(eval(dirname)):
            run_cmd(f'mkdir -p {eval(dirname)}')