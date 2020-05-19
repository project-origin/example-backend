from dataclasses import dataclass, field


@dataclass
class SubmitSupportEnquiryRequest:
    email: str
    phone: str
    message: str

    subject_type: str = field(metadata=dict(data_key='subjectType'))
    subject: str

    # Whether or not to send a recipe (email) to the user
    recipe: bool

    # File upload
    file_name: str = field(default=None, metadata=dict(data_key='fileName'))
    file_source: str = field(default=None, metadata=dict(data_key='fileSource'))


@dataclass
class SubmitSupportEnquiryResponse:
    success: bool
