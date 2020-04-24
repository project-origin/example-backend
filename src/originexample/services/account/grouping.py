from typing import List
from dataclasses import dataclass, field
from itertools import groupby

from originexample.facilities import get_technology
from originexample.services.account.models import SummaryGroup


def group_by_category(summary_groups, grouping):
    """
    :param list[SummaryGroup] summary_groups:
    :param list[str] grouping:
    :rtype: (str, list[SummaryGroup])
    """
    try:
        category_index = grouping.index('category')
    except ValueError:
        raise RuntimeError('Grouping does not contain "category"')

    def _get_category(sg):
        """
        :param SummaryGroup sg:
        :rtype: str
        """
        return sg.group[category_index]

    return groupby(
        sorted(summary_groups, key=_get_category),
        _get_category,
    )


def group_by_technology(summary_groups, grouping):
    """
    :param list[SummaryGroup] summary_groups:
    :param list[str] grouping:
    :rtype: collections.abc.Iterable[(str, list[SummaryGroup])]
    """
    try:
        tech_code_index = grouping.index('technologyCode')
        fuel_code_index = grouping.index('fuelCode')
    except ValueError:
        raise RuntimeError((
            'Grouping does not contain both '
            '"technologyCode" and "fuelCode"'
        ))

    def _get_technology(sg):
        """
        :param SummaryGroup sg:
        :rtype: str
        """
        return get_technology(
            tech_code=sg.group[tech_code_index],
            fuel_code=sg.group[fuel_code_index],
        )

    return groupby(
        sorted(summary_groups, key=_get_technology),
        _get_technology,
    )


def summarize_technologies(summary_groups, grouping):
    """
    :param list[SummaryGroup] summary_groups:
    :param list[str] grouping:
    :rtype: collections.abc.Iterable[(str, SummaryGroup)]
    """
    for technology, tech_groups in group_by_technology(summary_groups, grouping):
        yield technology, sum(tech_groups, SummaryGroup())


if __name__ == '__main__':
    grouping = ['category', 'technologyCode', 'fuelCode']

    groups = [
        SummaryGroup(['issued', 'T010000', 'F00000001'], [1, 2]),  # Solar
        SummaryGroup(['issued', 'T020000', 'F00000000'], [1, 2]),  # Wind
        SummaryGroup(['issued', 'T010000', 'F00000000'], [1, 2]),  # Solar
        SummaryGroup(['issued', 'T010000', 'F00000000'], [1, 1, 3]),  # Solar
    ]

    # res = [(cat, list(g)) for cat, g in group_by_category(groups, ['category', 'technologyCode', 'fuelCode'])]
    res = {cat: list(g) for cat, g in group_by_technology(groups, grouping)}

    assert len(res['Wind']) == 1, len(res['Wind'])
    assert len(res['Solar']) == 3, len(res['Solar'])

    res2 = dict(summarize_technologies(groups, grouping))

    y = 2
