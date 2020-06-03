import urllib
import requests
import marshmallow_dataclass as md
from datetime import datetime

from originexample import logger
from originexample.http import Unauthorized
from originexample.settings import ENERGY_DATA_SERVICE_URL, DEBUG

from .models import GetElectricityBalanceResponse


class EnergyDataService(object):

    def invoke(self, sql, response_schema):
        """
        :param str sql:
        :param Schema response_schema:
        :rtype obj:
        """
        query = urllib.parse.urlencode({'sql': sql})
        url = '%s?%s' % (ENERGY_DATA_SERVICE_URL, query)
        verify_ssl = not DEBUG

        try:
            response = requests.get(url=url, verify=verify_ssl)
        except:
            logger.exception(f'Invoking EnergyDataService resulted in an exception', extra={
                'url': url,
                'verify_ssl': verify_ssl,
            })
            raise

        if response.status_code == 401:
            raise Unauthorized
        elif response.status_code != 200:
            logger.error(f'Invoking EnergyDataService resulted in a status != 200', extra={
                'url': url,
                'verify_ssl': verify_ssl,
                'response_code': response.status_code,
                'response_content': str(response.content),
            })
            raise Exception('Request to EnergyDataService failed: %s' % str(response.content))

        response_json = response.json()

        return response_schema().load(response_json)

    def get_electricity_balance(self, begin, end):
        """
        :param datetime begin:
        :param datetime end:
        :rtype: GetElectricityBalanceResponse
        """
        sql = (
            "SELECT * from \"electricitybalancenonv\" "
            "WHERE \"HourUTC\" >= '%s' "
            "AND \"HourUTC\" <= '%s'"
        ) % (str(begin), str(end))

        return self.invoke(
            sql, md.class_schema(GetElectricityBalanceResponse))
