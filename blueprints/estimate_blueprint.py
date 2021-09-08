from flask import Blueprint, current_app, jsonify, request as req
from flask_cors import cross_origin

from util.app_util import CROSS_ORIGIN_HEADERS, app_db
from util import app_logger, auth_util, validation_util

estimate = Blueprint('estimate', __name__)
logger = app_logger.create_logger('estimate', current_app.config['IS_DEV'])
requires_auth = auth_util.init_auth('estimate')


@estimate.route('/recent-estimates', methods=['GET'])
@cross_origin(headers=CROSS_ORIGIN_HEADERS)
@requires_auth(admin_required=True)
def recent_estimates():
    logger.info('GET /api/estimate/recent-estimates')
    return jsonify(app_db().fetch_recent_estimates())


@estimate.route('/recently-received', methods=['GET'])
@cross_origin(headers=CROSS_ORIGIN_HEADERS)
@requires_auth(admin_required=True)
def recently_received_jobs():
    logger.info('GET /api/estimate/recently-received')
    return jsonify(app_db().fetch_recently_received_jobs())


@estimate.route('/active-contracts', methods=['GET'])
@cross_origin(headers=CROSS_ORIGIN_HEADERS)
@requires_auth(admin_required=True)
def active_contracts():
    logger.info('GET /api/estimate/active-contracts')
    return jsonify(app_db().fetch_active_contracts())


@estimate.route('/search', methods=['GET'])
@cross_origin(headers=CROSS_ORIGIN_HEADERS)
@requires_auth(admin_required=True)
def search_customer():
    query: str = req.args.get('query').strip().lower().replace(' ', '%') \
        if req.args.get('query') \
        else ''
    search_type: str = req.args.get('searchType').strip().lower() \
        if req.args.get('searchType') \
        else ''
    logger.info('GET /api/estimate/search?query=%s&searchType=%s', query, search_type)

    db = app_db()
    if search_type == 'customer':
        return jsonify(db.search_by_customer_name(query))
    elif search_type == 'company':
        return jsonify(db.search_by_company_name(query))
    elif search_type == 'address':
        return jsonify(db.search_by_job_address(query))
    else:
        return jsonify([])


@estimate.route('/customer/<customer_id>', methods=['GET'])
@cross_origin(headers=CROSS_ORIGIN_HEADERS)
@requires_auth(admin_required=True)
def customer(customer_id: str):
    logger.info('GET /api/estimate/customer/%s', customer_id)
    validation_util.require_numeric(customer_id)

    db = app_db()
    data = db.get_customer(customer_id)
    data['jobs'] = db.get_jobs_by_customer(customer_id)
    return jsonify(data)


@estimate.route('/job/<job_id>', methods=['GET'])
@cross_origin(headers=CROSS_ORIGIN_HEADERS)
@requires_auth(admin_required=True)
def job(job_id: str):
    logger.info('GET /api/estimate/job/%s', job_id)
    validation_util.require_numeric(job_id)

    db = app_db()
    data = db.get_job_details(job_id)
    data['workItems'] = db.get_work_items_by_job(job_id)
    data['payments'] = db.get_payments_by_job(job_id)
    data['invoices'] = db.get_invoices_by_job(job_id)
    return jsonify(data)
