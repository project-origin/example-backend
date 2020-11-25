import originexample.services.account as acc


def get_resolution(delta):
    """
    TODO write me

    :param timedelta delta:
    :rtype: SummaryResolution
    """
    if delta.days >= (365 * 3):
        return acc.SummaryResolution.YEAR
    elif delta.days >= 60:
        return acc.SummaryResolution.MONTH
    elif delta.days >= 3:
        return acc.SummaryResolution.DAY
    else:
        return acc.SummaryResolution.HOUR


def update_transfer_priorities(user, session):
    """
    TODO write me

    :param User user:
    :param sqlalchemy.orm.Session session:
    """
    session.execute("""
        update agreements_agreement
        set transfer_priority = s.row_number - 1
        from (
            select a.id, row_number() over (
                partition by a.user_from_id
                order by a.transfer_priority asc
            )
          from agreements_agreement as a
          where a.state = 'ACCEPTED'
          order by a.transfer_priority asc
        ) as s
        where agreements_agreement.id = s.id
        and agreements_agreement.user_from_id = :user_from_id
    """, {'user_from_id': user.id})
