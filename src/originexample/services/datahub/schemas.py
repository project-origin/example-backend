# from originexample.commodities import Ggo
# from originexample.schemas import Schema, fields, pre_load
# from originexample.facilities import Facility, Measurement, get_technology
#
#
# def _get_technology_type(data):
#     if 'technology_code' in data and 'source_code' in data:
#         return get_technology(data['technology_code'], data['source_code'])
#
#
# class MeteringPointSchema(Schema):
#     __type__ = Facility
#     gsrn = fields.String(required=True)
#     facility_type = fields.String(data_key='meter_type', required=True)
#     technology_type = fields.Function(deserialize=lambda data: _get_technology_type(data))
#     technology_code = fields.String(data_key='technology_type')
#     source_code = fields.String(data_key='source_type')
#     sector = fields.String(required=True)
#     street_code = fields.String(data_key='streetCode')
#     street_name = fields.String(data_key='streetName')
#     building_number = fields.String(data_key='buildingNumber')
#     city_name = fields.String(data_key='cityName')
#     postcode = fields.String()
#     municipality_code = fields.String(data_key='municipalityCode')
#
#     @pre_load
#     def unwrap_envelope(self, data, **kwargs):
#         data.update(data.pop('address'))
#         if 'production_type' in data:
#             data.update(data.pop('production_type'))
#         return data
#
#
# class MeasurementSchema(Schema):
#     __type__ = Measurement
#     facility_gsrn = fields.String(data_key='gsrn', required=True)
#     start = fields.DateTime(data_key='from', required=True)
#     amount = fields.Integer(required=True)
#     unit = fields.String(required=True)
#
#
# # class GgoSchema(Schema):
# #     __type__ = Ggo
# #     facility_gsrn = fields.String(data_key='gsrn', required=True)
# #     technology_code = fields.String(data_key='technology_type')
# #     source_code = fields.String(data_key='source_type')
# #     start = fields.DateTime(required=True)
# #     amount = fields.Integer(required=True)
# #     unit = fields.String(required=True)
