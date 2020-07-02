from dataclasses import dataclass

from originexample.services.account import Ggo
from originexample.services.datahub import Measurement, MeteringPoint


@dataclass
class OnGgoReceivedWebhookRequest:
    sub: str
    ggo: Ggo


@dataclass
class OnMeasurementPublishedWebhookRequest:
    sub: str
    measurement: Measurement


@dataclass
class OnMeteringPointAvailableWebhookRequest:
    sub: str
    meteringpoint: MeteringPoint


@dataclass
class OnMeteringPointsAvailableWebhookRequest:
    # TODO remove
    sub: str
