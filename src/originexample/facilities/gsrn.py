import re


tech_code_pattern = re.compile(r'^T[0-9]{6}$')
fuel_code_pattern = re.compile(r'^F[0-9]{8}$')


def get_technology(tech_code, fuel_code):
    """
    :param str tech_code:
    :param str fuel_code:
    :return str: Name of technology type
    """
    assert len(tech_code_pattern.findall(tech_code)) == 1, \
        'Invalid tech code provided: %s' % tech_code
    assert len(fuel_code_pattern.findall(fuel_code)) == 1, \
        'Invalid fuel code provided: %s' % fuel_code

    if tech_code.startswith('T01'):
        return 'Solar'
    elif tech_code.startswith('T02'):
        return 'Wind'
    elif tech_code.startswith('T03'):
        return 'Hydro'
    elif tech_code.startswith('T04'):
        return 'Marine'
    elif tech_code.startswith('T05'):
        return 'Thermal'  # TODO
    elif tech_code.startswith('T06'):
        return 'Nuclear'
    elif tech_code.startswith('T07'):
        return 'Other'

    raise ValueError((
        'Could not determine technology type for '
        'tech code %s and fuel code %s'
    ) % (tech_code, fuel_code))


def get_gsrn_tags(tech_code, fuel_code):
    """
    GSRN properties according to the documentation provided at the document
    "doc/AIB-2019-EECSFS-05 EECS Rules Fact Sheet 05 - Types of Energy Inputs and Technologies - Release 7.7 v5.pdf"
    """
    assert len(tech_code_pattern.findall(tech_code)) == 1
    assert len(fuel_code_pattern.findall(fuel_code)) == 1

    tags = []

    # Solar
    if tech_code.startswith('T01'):
        tags.append('Solar')

    # Wind
    elif tech_code.startswith('T02'):
        tags.append('Wind')

        if tech_code.endswith('01'):
            tags.append('Onshore')
        elif tech_code.endswith('02'):
            tags.append('Offshore')

    # Hydro-electric
    elif tech_code.startswith('T03'):
        tags.append('Hydro')

    # Marine
    elif tech_code.startswith('T04'):
        tags.append('Marine')

        if tech_code[-3] == '1':
            tags.append('Tidal')
        elif tech_code[-3] == '2':
            tags.append('Wave')
        elif tech_code[-3] == '3':
            tags.append('Currents')
        elif tech_code[-3] == '4':
            tags.append('Pressure')

    # Thermal
    elif tech_code.startswith('T05'):
        tags.append('Thermal')

    # Nuclear
    elif tech_code.startswith('T06'):
        tags.append('Nuclear')

    return tags


if __name__ == '__main__':
    assert get_technology('T010000')
