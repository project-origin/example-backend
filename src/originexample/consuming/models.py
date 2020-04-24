from dataclasses import dataclass, field

from originexample.services.account import Ggo


@dataclass
class OnGgoReceivedWebhookRequest:
    ggo: Ggo
    sub: str
