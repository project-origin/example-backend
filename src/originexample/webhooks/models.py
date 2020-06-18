from dataclasses import dataclass, field

from originexample.services.datahub import Measurement
from originexample.services.account import Ggo


@dataclass
class OnGgoReceivedWebhookRequest:
    ggo: Ggo
    sub: str


@dataclass
class OnMeasurementPublishedWebhookRequest:
    measurement: Measurement
    sub: str


@dataclass
class OnMeteringPointsAvailableWebhookRequest:
    sub: str
