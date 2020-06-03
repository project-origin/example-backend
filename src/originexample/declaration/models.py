import operator
from dataclasses import dataclass, field, fields

from originexample.common import DateRange


@dataclass
class EmissionValues:
    carbon_dioxide: float = field(default=0)           # CO2 / Kuldioxid
    methane: float = field(default=0)                  # CH4 / Metan
    nitrous_oxide: float = field(default=0)            # N2O / Lattergas
    greenhouse_gasses: float = field(default=0)        # Drivhusgasser
    sulfur_dioxide: float = field(default=0)           # SO2 / Svovldioxid
    nitrogen_dioxide: float = field(default=0)         # NOx / Kvælstofilte
    carbon_monoxide: float = field(default=0)          # C2 / Kulilte
    hydrocarbons: float = field(default=0)             # NMVOC / Uforbrændt kulbrinter
    particles: float = field(default=0)                # Partikler

    # Residues / Restprodukter
    coal_fly_ash: float = field(default=0)             # Kulflyveaske
    coal_slag: float = field(default=0)                # Kulslagge
    desulfuriazion_products: float = field(default=0)  # Afsvovlingsprodukter (Gips)
    slag: float = field(default=0)                     # Slagge (affalgsforbrænding)
    rga: float = field(default=0)                      # RGA (roggasaffald)
    bioash: float = field(default=0)                   # Bioaske
    radioactive_waste: float = field(default=0)        # Radioaktivt affald

    def __radd__(self, other):
        """
        :param EmissionValues|int|float other:
        :rtype: EmissionValues
        """
        return self + other

    def __add__(self, other):
        """
        :param EmissionValues|int|float other:
        :rtype: EmissionValues
        """
        return self.__do_arithmetic(other, operator.__add__)

    def __truediv__(self, other):
        """
        :param EmissionValues|int|float other:
        :rtype: EmissionValues
        """
        return self.__do_arithmetic(other, operator.__truediv__)

    def __do_arithmetic(self, other, calc):
        """
        :param EmissionValues|int|float other:
        :param function calc:
        :rtype: EmissionValues
        """
        if isinstance(other, EmissionValues):
            return EmissionValues(
                **{f.name: calc(getattr(self, f.name), getattr(other, f.name))
                   for f in fields(EmissionValues)}
            )
        elif isinstance(other, (int, float)):
            return EmissionValues(
                **{f.name: calc(getattr(self, f.name), other)
                   for f in fields(EmissionValues)}
            )

        return NotImplemented


@dataclass
class EcoDeclaration:
    general: EmissionValues
    individual: EmissionValues


# -- GetEcoDeclaration request and response ----------------------------------


@dataclass
class GetEcoDeclarationRequest:
    date_range: DateRange = field(metadata=dict(data_key='dateRange'))


@dataclass
class GetEcoDeclarationResponse:
    success: bool
    declaration: EcoDeclaration
