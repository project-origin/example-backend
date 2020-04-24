from .auth import User
from .facilities import Facility, FacilityTag
from .agreements import TradeAgreement
from .disclosures import Disclosure


# This is a list of all database models to include when creating
# database migrations.

VERSIONED_DB_MODELS = (
    User,
    Facility,
    FacilityTag,
    TradeAgreement,
    Disclosure,
)
