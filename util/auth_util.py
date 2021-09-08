from datetime import datetime
from os import environ

# noinspection PyProtectedMember
from flask import current_app, request as req, _request_ctx_stack, session
from functools import wraps
from jose import jwt
import requests
from typing import Dict
from werkzeug.exceptions import Forbidden, HTTPException, Unauthorized

from util.app_logger import create_logger
from util.type_util import SessionIdentity, JWTClaims

APP_ID = environ['APP_ID']
TENANT_ID = environ['TENANT_ID']
ADMIN_GROUP_ID = environ['ADMIN_GROUP_ID']
TIMECARD_GROUP_ID = environ['TIMECARD_GROUP_ID']


def is_admin(identity: SessionIdentity) -> bool:
    return 'is_admin' in identity and identity['is_admin']


def get_token_auth_header():
    auth = req.headers.get('Authorization', None)
    if not auth:
        raise Unauthorized('authorization header is expected')

    parts = auth.split()

    if len(parts) != 2 or parts[0].lower() != 'bearer':
        raise Unauthorized('authorization header must be Bearer token')
    return parts[1]


def set_session(claims: JWTClaims) -> SessionIdentity:
    session['identity'] = {
        'employee_id': claims['oid'].replace('-', ''),
        'exp': claims['exp'],
        'is_admin': 'groups' in claims and ADMIN_GROUP_ID in claims['groups'],
        'name': claims['name'],
        'payload': claims,
        'user_principal_name': claims['unique_name']
    }
    return session['identity']


def init_auth(name):
    logger = create_logger(name + '-auth_util', current_app.config['IS_DEV'])

    def requires_auth(admin_required=False, with_session=False):
        def decorator(f):
            @wraps(f)
            def decorated(*args, **kwargs):
                identity: SessionIdentity = session.get('identity', {})
                if is_active_session(identity):
                    validate_permissions(admin_required, identity)
                    _request_ctx_stack.top.current_user = identity['payload']
                    if with_session:
                        return f(identity, *args, **kwargs)
                    else:
                        return f(*args, **kwargs)

                token = get_token_auth_header()
                rsa_key = build_rsa_key(token)
                if rsa_key:
                    payload = decode_token(rsa_key, token, logger)

                    updated_identity: SessionIdentity = set_session(payload)
                    logger.info(
                        f"{updated_identity['name']} with employee_id {updated_identity['employee_id']} logged in from IP address {updated_identity['payload']['ipaddr']}"
                    )
                    validate_permissions(admin_required, updated_identity)

                    _request_ctx_stack.top.current_user = payload
                    if with_session:
                        return f(updated_identity, *args, **kwargs)
                    else:
                        return f(*args, **kwargs)
                logger.exception('unable to find appropriate key')
                raise Unauthorized()

            return decorated

        return decorator

    return requires_auth


def validate_permissions(admin_required: bool, identity: SessionIdentity) -> None:
    payload = identity['payload']
    groups = payload['groups']
    tenant_id = payload['tid']
    if TENANT_ID != tenant_id:
        raise Unauthorized('Not a member of this tenant. Tenant ID: ' + tenant_id)
    elif admin_required and ADMIN_GROUP_ID not in groups:
        raise Forbidden('Administrator access required. UPN: ' + identity['user_principal_name'])
    elif ADMIN_GROUP_ID not in groups and TIMECARD_GROUP_ID not in groups:
        raise Forbidden('Not authorized to access this page')


def is_active_session(identity: SessionIdentity) -> bool:
    return (
            'user_principal_name' in identity
            and 'employee_id' in identity
            and 'exp' in identity
            and 'payload' in identity
            and datetime.fromtimestamp(identity['exp']) > datetime.now()
    )


def build_rsa_key(token: str) -> Dict[str, any]:
    unverified_header = jwt.get_unverified_header(token)
    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            return {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }
    return {}


def decode_token(rsa_key: Dict[str, any], token: str, logger):
    try:
        return jwt.decode(
            token=token,
            key=rsa_key,
            algorithms=['RS256'],
            audience=f'api://{APP_ID}',
            issuer=f'https://sts.windows.net/{TENANT_ID}/'
        )
    except jwt.ExpiredSignatureError as e:
        logger.error('token is expired', exc_info=e)
        raise Unauthorized()
    except jwt.JWTClaimsError as e:
        logger.error('incorrect claims, please check the audience and issuer', exc_info=e)
        raise Unauthorized()
    except Exception as e:
        logger.error('Uncaught exception in util.auth_util.decode_token', exc_info=e)
        raise Unauthorized()


def execute_request(url, headers=None):
    res = requests.get(url, headers=headers)
    status_code = res.status_code

    if status_code == 200:
        return res.json()
    else:
        raise HTTPException(f'unable to call {url}. Status code: {str(status_code)}')


jwks = execute_request(f'https://login.microsoftonline.com/{TENANT_ID}/discovery/v2.0/keys?appid={APP_ID}')
# noinspection SpellCheckingInspection
