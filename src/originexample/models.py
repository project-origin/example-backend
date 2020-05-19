from .auth import User
from .facilities import Facility, FacilityTag
from .agreements import TradeAgreement
from .technology import Technology


# This is a list of all database models to include when creating
# database migrations.

VERSIONED_DB_MODELS = (
    User,
    Facility,
    FacilityTag,
    TradeAgreement,
    Technology,
)
