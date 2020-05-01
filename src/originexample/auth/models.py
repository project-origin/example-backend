import sqlalchemy as sa
from typing import List
from dataclasses import dataclass, field

from marshmallow import fields, EXCLUDE
from marshmallow_dataclass import NewType

from originexample.db import ModelBase


class User(ModelBase):
    """
    Represents one used in the system who is able to authenticate.
    """
    __tablename__ = 'auth_user'
    __table_args__ = (
        sa.UniqueConstraint('sub'),
    )

    id = sa.Column(sa.Integer, primary_key=True, index=True)
    created = sa.Column(sa.DateTime(timezone=True), server_default=sa.func.now())

    # Name / Company name
    name = sa.Column(sa.String(), nullable=False)

    # Subject ID / Account number
    sub = sa.Column(sa.String(), index=True, unique=True, nullable=False)

    # Tokens
    access_token = sa.Column(sa.String(), nullable=False)
    refresh_token = sa.Column(sa.String(), nullable=False)
    token_expire = sa.Column(sa.DateTime(), nullable=False)

    # Whether or not the user has been prompted to perform the onboarding flow
    has_performed_onboarding = sa.Column(sa.Boolean(), nullable=False, default=False)

    # Whether or not Facilities are currently being imported asynchronously
    is_importing_facilities = sa.Column(sa.Boolean(), nullable=False, default=False)

    def __str__(self):
        return 'User<%s>' % self.sub


@dataclass
class MappedUser:
    """
    Replicates the data structure of a User,
    but is compatible with marshmallow_dataclass obj-to-JSON
    """
    sub: str = field(metadata=dict(data_key='id'))
    name: str
    has_performed_onboarding: bool = field(metadata=dict(data_key='hasPerformedOnboarding'))


# -- Login request and response --------------------------------------------


@dataclass
class LoginRequest:
    class Meta:
        unknown = EXCLUDE
    return_url: str = field(metadata=dict(data_key='returnUrl'))




# -- Error request and response --------------------------------------------


@dataclass
class ErrorRequest:
    class Meta:
        unknown = EXCLUDE

    error: str = field(default=None)
    error_description: str = field(default=None)
    error_hint: str = field(default=None)


# -- VerifyLoginCallback request and response --------------------------------


Scope = NewType(
    name='Scope',
    typ=List[str],
    field=fields.Function,
    deserialize=lambda scope: scope.split(' '),
)


@dataclass
class VerifyLoginCallbackRequest:
    scope: Scope
    code: str
    state: str


# -- GetProfile request and response -----------------------------------------


@dataclass
class GetProfileResponse:
    success: bool
    user: MappedUser


# -- SearchUsers request and response ----------------------------------------


@dataclass
class AutocompleteUsersRequest:
    query: str


@dataclass
class AutocompleteUsersResponse:
    success: bool
    users: List[MappedUser]


# -- GetOnboardingUrl request and response ----------------------------------------


@dataclass
class GetOnboardingUrlResponse:
    success: bool
    url: str
