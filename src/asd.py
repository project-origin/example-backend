from datetime import date, timedelta
from originexample.db import make_session
from originexample.auth import User
from originexample.common import DateRange
from originexample.declaration import EnvironmentDeclaration


session = make_session()
user = session.query(User).first()
date_range = DateRange(
    # begin=date.today() - timedelta(days=2),
    # end=date.today(),
    begin=date(2019, 1, 1),
    end=date(2019, 12, 31),
)


declaration = EnvironmentDeclaration(user, date_range)
general = declaration.general
y = 2
