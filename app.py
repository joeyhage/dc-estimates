from os import environ

from flask import Flask, jsonify, session, request
from flask_cors import cross_origin
from flask_session import Session
from werkzeug.exceptions import HTTPException

from util.app_util import CROSS_ORIGIN_HEADERS
from util.type_util import SessionIdentity
from util import app_logger, auth_util, sql_util

app = Flask(__name__, static_folder=None)
app.config['IS_DEV'] = 'DEV' in environ
logger = app_logger.create_logger('app', app.config['IS_DEV'])
logger.info('Starting up...')

app.config['DC_DB'] = sql_util.init_db(app)
app.config['SESSION_TYPE'] = 'sqlalchemy'
app.config['SESSION_SQLALCHEMY'] = app.config['DC_DB'].get_db()
app.config['SESSION_SQLALCHEMY_TABLE'] = 'Tbl_web_sessions'
app.config['SESSION_COOKIE_SECURE'] = True

# noinspection SpellCheckingInspection
app.secret_key = environ['SESSION_SECRET']
Session(app)

with app.app_context():
    from blueprints import estimate_blueprint

    requires_auth = auth_util.init_auth('app')
    app.register_blueprint(estimate_blueprint.estimate, url_prefix='/api/estimate')


@app.route('/api/hello', methods=['GET'])
def hello():
    logger.info('GET /api/hello')
    return 'Hello!'


@app.route('/api/init-session', methods=['GET'])
@cross_origin(headers=CROSS_ORIGIN_HEADERS)
@requires_auth()
def init_session():
    logger.info('GET /api/init-session')
    identity: SessionIdentity = session.get('identity', {'is_admin': False, 'name': '', 'employeeId': ''})
    return jsonify({
        'isAdmin': identity['is_admin'],
        'fullName': identity['name'],
        'employeeId': identity['employee_id']
    })


@app.after_request
def add_headers(response):
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'deny'
    response.headers['X-Permitted-Cross-Domain-Policies'] = 'none'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response


@app.errorhandler(HTTPException)
def handle_http_exception(e: HTTPException):
    logger.error('%d %s HTTPException', e.code, e.name, exc_info=e)
    return e.name, e.code


@app.errorhandler(Exception)
def handle_exception(e: Exception):
    logger.error('Uncaught application exception', exc_info=e)
    return 'Server Error', 500


if __name__ == '__main__':
    app.run()
