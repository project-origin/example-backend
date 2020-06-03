from .models import EmissionValues


biogas = EmissionValues(
    methane=2.48,
    nitrous_oxide=0.009,
    greenhouse_gasses=65,
    sulfur_dioxide=0.12,
    nitrogen_dioxide=1.17,
    carbon_monoxide=1.79,
    hydrocarbons=0.06,
    particles=0.02,
)


biomass = EmissionValues(
    methane=0.02,
    nitrous_oxide=0.006,
    greenhouse_gasses=2,
    sulfur_dioxide=0.05,
    nitrogen_dioxide=0.66,
    carbon_monoxide=0.66,
    hydrocarbons=0.03,
    particles=0.07,
    bioash=9.8,
)


oil = EmissionValues(
    carbon_dioxide=844,
    methane=0.02,
    nitrous_oxide=0.027,
    greenhouse_gasses=852,
    sulfur_dioxide=2.02,
    nitrogen_dioxide=1.59,
    carbon_monoxide=0.12,
    hydrocarbons=0.01,
    particles=0.07,
)


coal = EmissionValues(
    carbon_dioxide=761,
    methane=0.01,
    nitrous_oxide=0.006,
    greenhouse_gasses=763,
    sulfur_dioxide=0.07,
    nitrogen_dioxide=0.23,
    carbon_monoxide=0.08,
    hydrocarbons=0.01,
    particles=0.02,
    coal_fly_ash=36,
    coal_slag=6.2,
    desulfuriazion_products=13.1,
)


naturalgas = EmissionValues(
    carbon_dioxide=357,
    methane=0.81,
    nitrous_oxide=0.006,
    greenhouse_gasses=379,
    nitrogen_dioxide=0.49,
    carbon_monoxide=0.14,
    hydrocarbons=0.16,
)


nuclear = EmissionValues(
    radioactive_waste=0.0027,
)


waste = EmissionValues(
    carbon_dioxide=1036,
    nitrous_oxide=0.012,
    greenhouse_gasses=1040,
    sulfur_dioxide=0.08,
    nitrogen_dioxide=0.65,
    carbon_monoxide=0.04,
    hydrocarbons=0.01,
    slag=173,
    rga=26.2,
)


marine = EmissionValues()
hydro = EmissionValues()
wind = EmissionValues()
solar = EmissionValues()
other_renewable = EmissionValues()


# Emission values mapped by their technology label

EMISSIONS = {
    'Biogas': biogas,
    'Biomass': biomass,
    'Coal': coal,
    'Hydro': hydro,
    'Marine': marine,
    'Naturalgas': naturalgas,
    'Nuclear': nuclear,
    'Oil': oil,
    'Solar': solar,
    'Waste': waste,
    'Wind': wind,
}
