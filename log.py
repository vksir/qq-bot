import logging

from constants import LOG_PATH


def init_log(level=logging.INFO):
    global log
    log = logging.getLogger()
    log.setLevel(level)
    fm = logging.Formatter('%(asctime)s [%(levelname)s][%(filename)s] %(message)s', datefmt='%Y/%m/%d %H:%M:%S')

    fh = logging.FileHandler(LOG_PATH, mode='a', encoding='utf-8')
    fh.setFormatter(fm)
    log.addHandler(fh)


log = logging.getLogger()
