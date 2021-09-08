from flask import current_app

from util.sql_util import SQLUtil

CROSS_ORIGIN_HEADERS = ['Content-Type', 'Authorization']


def app_db() -> SQLUtil:
    return current_app.config['DC_DB']
