import marshmallow_dataclass as md
from datetime import datetime, timezone
from urllib.parse import urlparse

from flask import make_response

from originexample import logger
from originexample.db import atomic, inject_session
from originexample.http import Controller, redirect, BadRequest
from originexample.services.datahub import DataHubService
from originexample.services.account import AccountService
from originexample.cache import redis
from originexample.settings import (
    PROJECT_URL,
    FRONTEND_URL,
    ACCOUNT_SERVICE_LOGIN_URL,
    IDENTITY_SERVICE_EDIT_PROFILE_URL,
)

from .queries import UserQuery
from .backend import AuthBackend
from .decorators import requires_login, inject_user
from .models import (
    User,
    LoginRequest,
    ErrorRequest,
    AutocompleteUsersRequest,
    AutocompleteUsersResponse,
    VerifyLoginCallbackRequest,
    GetProfileResponse,
    GetOnboardingUrlResponse,
)


backend = AuthBackend()


class Login(Controller):
    """
    Redirects the user to IdentityService login URL, which
    contains a unique "login challenge" identifying the user.

    Saves the provided "return_url" to redis cache, so it's available when
    the client is redirected back to the LoginCallback endpoint (below).
    """
    METHOD = 'GET'

    Request = md.class_schema(LoginRequest)

    def handle_request(self, request):
        """
        :param LoginRequest request:
        :rtype: flask.Response
        """
        if request.return_url:
            return_url = request.return_url
        else:
            return_url = FRONTEND_URL

        login_url, state = backend.register_login_state()

        redis.set(state, return_url, ex=3600)

        return redirect(login_url, code=303)


class LoginCallback(Controller):
    """
    TODO
    """
    METHOD = 'GET'

    Request = md.class_schema(VerifyLoginCallbackRequest)

    datahub = DataHubService()
    account = AccountService()

    @atomic
    def handle_request(self, request, session):
        """
        :param VerifyLoginCallbackRequest request:
        :param Session session:
        :rtype: flask.Response
        """
        return_url = redis.get(request.state)

        if return_url is None:
            raise BadRequest('Click back in your browser')
        else:
            return_url = return_url.decode()
            redis.delete(request.state)

        # Fetch token
        try:
            token = backend.fetch_token(request.code, request.state)
        except:
            logger.exception(f'Failed to fetch token', extra={
                'scope': str(request.scope),
                'code': request.code,
                'state': request.state,
            })
            return self.redirect_to_failure(return_url)

        # Extract data from token
        id_token = backend.get_id_token(token)

        # No id_token means the user declined to give consent
        if id_token is None:
            return self.redirect_to_failure(return_url)

        expires = datetime \
            .fromtimestamp(token['expires_at']) \
            .replace(tzinfo=timezone.utc)

        # Lookup user from "subject"
        user = UserQuery(session) \
            .has_sub(id_token['sub']) \
            .one_or_none()

        if user is None:
            logger.info(f'User login: Creating new user and subscribing to webhooks', extra={
                'subject': id_token['sub'],
            })
            self.create_new_user(token, id_token, expires, session)
            self.datahub.webhook_on_meteringpoints_available_subscribe(token['access_token'])
            self.account.webhook_on_ggo_received_subscribe(token['access_token'])
        else:
            logger.info(f'User login: Updating tokens for existing user', extra={
                'subject': id_token['sub'],
            })
            self.update_user_attributes(user, token, expires)

        # Save session in Redis
        redis.set(id_token['sid'], id_token['sub'], ex=token['expires_at'])

        # Create HTTP response
        response = redirect(f'{ACCOUNT_SERVICE_LOGIN_URL}?returnUrl={return_url}', 303)
        response.set_cookie('SID', id_token['sid'], domain=urlparse(FRONTEND_URL).netloc)
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        response.headers['Cache-Control'] = 'public, max-age=0'

        return response

    def create_new_user(self, token, id_token, expires, session):
        """

        """
        user = User(
            sub=id_token['sub'],
            name=id_token['company'],
            email=id_token['email'],
            access_token=token['access_token'],
            refresh_token=token['refresh_token'],
            token_expire=expires,
        )
        user.update_last_login()

        session.add(user)
        session.flush()

    def update_user_attributes(self, user, token, expires):
        """

        """
        user.update_last_login()
        user.access_token = token['access_token']
        user.refresh_token = token['refresh_token']
        user.token_expire = expires

    def redirect_to_failure(self, return_url):
        """
        :param str return_url:
        :rtype: flask.Response
        """
        return redirect(f'{return_url}?success=0', code=303)


class EditProfile(Controller):
    """
    Redirects the user to IdentityService edit profile URL
    """
    METHOD = 'GET'

    def handle_request(self):
        """
        :rtype: flask.Response
        """
        return_url = f'{PROJECT_URL}/auth/edit-profile/callback'
        url = f'{IDENTITY_SERVICE_EDIT_PROFILE_URL}?return_url={return_url}'
        return redirect(url, code=303)


class EditProfileCallback(Controller):
    """
    Callback endpoint for when then user has completed editing his profile.
    Redirects to the login endpoint, which forces the IdentityService
    to refresh the user's id_token.
    """
    METHOD = 'GET'

    def handle_request(self):
        """
        :rtype: flask.Response
        """
        return redirect('/auth/login', code=303)


class Logout(Controller):
    """
    TODO
    """
    METHOD = 'GET'

    def handle_request(self):
        """
        :rtype: flask.Response
        """
        response = make_response(redirect(backend.get_logout_url(), code=303))
        response.delete_cookie('SID', domain=urlparse(FRONTEND_URL).netloc)
        return response


class Error(Controller):
    """
    TODO
    """
    METHOD = 'GET'
    Request = md.class_schema(ErrorRequest)

    @inject_user
    def handle_request(self, request, user):
        """
        :param ErrorRequest request:
        :param User user:
        :rtype: flask.Response
        """
        
        logger.error("An error occurred on Hydra.", {
            'error': request.error,
            'error_description': request.error_description,
            'error_hint': request.error_hint,
            'subject': user.sub
        })

        return redirect(FRONTEND_URL, code=303)


class GetOnboardingUrl(Controller):
    """
    TODO
    """
    Response = md.class_schema(GetOnboardingUrlResponse)

    service = DataHubService()

    @requires_login
    @atomic
    def handle_request(self, user, session):
        """
        :param User user:
        :param Session session:
        :rtype: GetOnboardingUrlResponse
        """
        response = self.service.get_onboarding_url(
            user.access_token, FRONTEND_URL)

        session.query(User) \
            .filter(User.id == user.id) \
            .update({'has_performed_onboarding': True})

        return GetOnboardingUrlResponse(
            success=True,
            url=response.url,
        )


class GetProfile(Controller):
    """
    Refreshes user's profile data along with tokens,
    and returns the User profile.
    """
    Response = md.class_schema(GetProfileResponse)

    @requires_login
    @atomic
    def handle_request(self, user, session):
        """
        :param User user:
        :param Session session:
        :rtype: GetProfileResponse
        """
        token = backend.refresh_token(user.refresh_token)
        id_token = backend.get_id_token(token)

        # Update user profile and tokens
        session.query(User) \
            .filter(User.id == user.id) \
            .update({
                'email': id_token['email'],
                'phone': id_token['phone'],
                'name': id_token['name'],
                'company': id_token['company'],
                'access_token': token['access_token'],
                'refresh_token': token['refresh_token'],
                'token_expire': datetime
                    .fromtimestamp(token['expires_at'])
                    .replace(tzinfo=timezone.utc),
            })

        user.email = id_token['email']
        user.phone = id_token['phone']
        user.name = id_token['name']
        user.company = id_token['company']

        return GetProfileResponse(
            success=True,
            user=user,
        )


class AutocompleteUsers(Controller):
    """
    TODO
    """
    Request = md.class_schema(AutocompleteUsersRequest)
    Response = md.class_schema(AutocompleteUsersResponse)

    @requires_login
    @inject_session
    def handle_request(self, request, user, session):
        """
        :param AutocompleteUsersRequest request:
        :param User user:
        :param Session session:
        :rtype: AutocompleteUsersResponse
        """
        users = UserQuery(session) \
            .starts_with(request.query) \
            .exclude(user) \
            .order_by(User.name.asc()) \
            .all()

        return AutocompleteUsersResponse(
            success=True,
            users=users,
        )
