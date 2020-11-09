from .auth import controllers as auth
from .eco import controllers as eco
from .commodities import controllers as commodities
from .facilities import controllers as facilities
from .agreements import controllers as agreements
from .disclosures import controllers as disclosures
from .support import controllers as support
from .forecast import controllers as forecast
from .webhooks import controllers as webhooks


urls = (

    # Auth / Users
    ('/auth/login', auth.Login()),
    ('/auth/login/callback', auth.LoginCallback()),
    ('/auth/edit-clients', auth.EditClients()),
    ('/auth/edit-profile', auth.EditProfile()),
    ('/auth/edit-profile/callback', auth.EditProfileCallback()),
    ('/auth/disable-user', auth.DisableUser()),
    ('/auth/disable-user/callback', auth.DisableUserCallback()),
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
    ('/agreements/cancel', agreements.CancelAgreement()),
    ('/agreements/set-transfer-priority', agreements.SetTransferPriority()),
    ('/agreements/set-facilities', agreements.SetFacilities()),
    ('/agreements/find-suppliers', agreements.FindSuppliers()),
    ('/agreements/propose', agreements.SubmitAgreementProposal()),
    ('/agreements/propose/respond', agreements.RespondToProposal()),
    ('/agreements/propose/withdraw', agreements.WithdrawProposal()),
    ('/agreements/propose/pending-count', agreements.CountPendingProposals()),
    ('/agreements/ggo-summary/csv', agreements.ExportGgoSummaryCSV()),

    # GGOs
    ('/commodities/distributions', commodities.GetGgoDistributions()),
    ('/commodities/ggo-summary', commodities.GetGgoSummary()),
    ('/commodities/measurements', commodities.GetMeasurements()),
    ('/commodities/measurements/csv', commodities.ExportMeasurementsCSV()),
    ('/commodities/ggo-summary/csv', commodities.ExportGgoSummaryCSV()),
    ('/commodities/ggo-list/csv', commodities.ExportGgoListCSV()),
    ('/commodities/get-peak-measurement', commodities.GetPeakMeasurement()),

    # Eco Declaration
    ('/eco-declaration', eco.GetEcoDeclaration()),
    ('/eco-declaration/pdf', eco.ExportEcoDeclarationPDF()),
    ('/eco-declaration/csv/emissions', eco.ExportEcoDeclarationEmissionsCSV()),
    ('/eco-declaration/csv/technologies', eco.ExportEcoDeclarationTechnologiesCSV()),

    # Disclosure
    ('/disclosure', disclosures.GetDisclosure()),
    ('/disclosure/list', disclosures.GetDisclosureList()),
    ('/disclosure/preview', disclosures.GetDisclosurePreview()),
    ('/disclosure/create', disclosures.CreateDisclosure()),
    ('/disclosure/delete', disclosures.DeleteDisclosure()),

    # Forecasts
    ('/forecast', forecast.GetForecast()),
    ('/forecast/list', forecast.GetForecastList()),
    ('/forecast/series', forecast.GetForecastSeries()),
    ('/forecast/submit', forecast.SubmitForecast()),

    # Webhooks
    ('/webhook/on-ggo-received', webhooks.OnGgoReceivedWebhook()),
    ('/webhook/on-measurement-published', webhooks.OnMeasurementPublishedWebhook()),
    ('/webhook/on-meteringpoint-available', webhooks.OnMeteringPointAvailableWebhook()),

    # Misc
    ('/support/submit-support-enquiry', support.SubmitSupportEnquiry()),

    # TODO remove
    ('/webhook/on-meteringpoints-available', webhooks.OnMeteringPointsAvailableWebhook()),

)
