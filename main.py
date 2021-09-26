#!/usr/bin/python3
# coding: utf-8

import signal

import log
import config
from http_server import Application, HttpServer


def main():
    def safe_exit(*args):
        exit()
    signal.signal(signal.SIGINT, safe_exit)

    config.init_path()
    log.init_log()
    cfg_parser = config.CfgParser()
    cfg = cfg_parser.read()
    app = Application(cfg)
    server = HttpServer(app)
    server.start()


if __name__ == '__main__':
    main()
