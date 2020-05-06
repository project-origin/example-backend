from .auth import controllers as auth
from .consuming import controllers as consuming
from .commodities import controllers as commodities
from .facilities import controllers as facilities
from .agreements import controllers as agreements


urls = (

    # Auth / Users
    ('/auth/login', auth.Login()),
    ('/auth/login/callback', auth.LoginCallback()),
    ('/auth/logout', auth.Logout()),
    ('/auth/error', auth.Error()),
    ('/auth/get-onboarding-url', auth.GetOnboardingUrl()),
    ('/users/profile', auth.GetProfile()),
    ('/users/autocomplete', auth.AutocompleteUsers()),

    # Facilities
    ('/facilities', facilities.GetFacilityList()),
    ('/facilities/edit', facilities.EditFacilityDetails()),
    ('/facilities/get-filtering-options', facilities.GetFilteringOptions()),
    ('/facilities/set-retiring-priority', facilities.SetRetiringPriority()),
    ('/facilities/retire-back-in-time', facilities.RetireBackInTime()),

    # Agreements
    ('/agreements', agreements.GetAgreementList()),
    ('/agreements/details', agreements.GetAgreementDetails()),
    ('/agreements/summary', agreements.GetAgreementSummary()),
    ('/agreements/propose', agreements.SubmitAgreementProposal()),
    ('/agreements/propose/respond', agreements.RespondToProposal()),
    ('/agreements/propose/withdraw', agreements.WithdrawProposal()),
    ('/agreements/propose/pending-count', agreements.CountPendingProposals()),

    # GGOs
    ('/commodities/distributions', commodities.GetGgoDistributions()),
    ('/commodities/measurements', commodities.GetMeasurements()),

    # Webhooks
    ('/webhook/on-ggo-received', consuming.OnGgoReceivedWebhook()),
    ('/webhook/on-meteringpoints-available', facilities.OnMeteringPointsAvailableWebhook()),

)
