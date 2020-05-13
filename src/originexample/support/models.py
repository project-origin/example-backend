from dataclasses import dataclass


@dataclass
class SubmitSupportEnquiryRequest:
    email: str
    phone: str
    subject: str
    message: str


@dataclass
class SubmitSupportEnquiryResponse:
    success: bool
