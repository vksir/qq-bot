import json
import requests
from webob import Request, Response
from wsgiref.simple_server import make_server

from log import log
from config import DataParser
from msg_handler import MsgHandler


class Application:
    def __init__(self, cfg: dict, qq_bot_ip='127.0.0.1', qq_bot_port=5700):
        self._qq_bot_url = f'http://{qq_bot_ip}:{qq_bot_port}'
        self._handler = MsgHandler(cfg)

    def __call__(self, env, start_response):
        req = Request(env)
        resp = Response()
        data = json.loads(req.body.decode())
        parser = DataParser(data)
        self.deal_with_event(parser)
        return resp(env, start_response)

    def deal_with_event(self, parser: DataParser):
        message_type = parser.message_type
        if message_type == 'private':
            res = self._handler(parser)
            self.send_msg(parser.user_id, res)
        elif message_type == 'group':
            res = self._handler(parser)
            self.send_msg(parser.user_id, res, group_id=parser.group_id)
        else:
            # todo other event
            pass

    def send_msg(self, user_id: int, msg: str, group_id: int = None):
        url = f'{self._qq_bot_url}/send_msg'
        if group_id:
            msg = f'[CQ:at,qq={user_id}]{msg}'
            params = dict(group_id=group_id, message=msg)
        else:
            url = f'{self._qq_bot_url}/send_private_msg'
            params = dict(user_id=user_id, message=msg)
        requests.post(url, params=params)


class HttpServer:
    def __init__(self, app, bind_ip='127.0.0.1', bind_port=5701):
        self._app = app
        self._bind_ip = bind_ip
        self._port = bind_port

    def start(self):
        with make_server(self._bind_ip, self._port, self._app) as httpd:
            print('qq_bot http server start')
            log.info('http server start')
            httpd.serve_forever()
