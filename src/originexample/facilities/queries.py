import sqlalchemy as sa

from originexample.auth import User

from .models import Facility, FacilityFilters, FacilityTag, FacilityType


class FacilityQuery(object):
    """
    TODO
    """
    def __init__(self, session, q=None):
        """
        :param Session session:
        :param FacilityQuery q:
        """
        self.session = session
        if q is None:
            self.q = session.query(Facility)
        else:
            self.q = q

    def __iter__(self):
        return iter(self.q)

    def __getattr__(self, name):
        return getattr(self.q, name)

    def apply_filters(self, filters):
        """
        :param FacilityFilters filters:
        :rtype: FacilityQuery
        """
        q = self.q

        if filters.facility_type:
            q = q.filter(Facility.facility_type == filters.facility_type)
        if filters.gsrn:
            q = q.filter(Facility.gsrn.in_(filters.gsrn))
        if filters.sectors:
            q = q.filter(Facility.sector.in_(filters.sectors))
        if filters.tags:
            q = q.filter(*[Facility.tags.any(tag=t) for t in filters.tags])
        if filters.technology:
            q = q.filter(Facility.technology == filters.technology)
        if filters.text:
            # SQLite doesn't support full text search, so this is the second
            # best solution (the only?) which enables us to perform both
            # production and test execution of this filtering option
            q = q.filter(sa.or_(
                Facility.gsrn.ilike('%%%s%%' % filters.text),
                Facility.name.ilike('%%%s%%' % filters.text),
                Facility.street_name.ilike('%%%s%%' % filters.text),
                Facility.city_name.ilike('%%%s%%' % filters.text),
            ))

        return FacilityQuery(self.session, q)

    def has_public_id(self, public_id):
        """
        :param str public_id:
        :rtype: FacilityQuery
        """
        return FacilityQuery(self.session, self.q.filter(
            Facility.public_id == public_id,
        ))

    def has_any_public_id(self, public_ids):
        """
        :param list[str] public_ids:
        :rtype: FacilityQuery
        """
        return FacilityQuery(self.session, self.q.filter(
            Facility.public_id.in_(public_ids),
        ))

    def has_gsrn(self, gsrn):
        """
        :param str gsrn:
        :rtype: FacilityQuery
        """
        return FacilityQuery(self.session, self.q.filter(
            Facility.gsrn == gsrn,
        ))

    def has_any_gsrn(self, gsrn):
        """
        :param list[str] gsrn:
        :rtype: FacilityQuery
        """
        return FacilityQuery(self.session, self.q.filter(
            Facility.gsrn.in_(gsrn),
        ))

    def belongs_to(self, user):
        """
        TODO

        :param User user:
        :rtype: FacilityQuery
        """
        return FacilityQuery(self.session, self.q.filter(
            Facility.user_id == user.id,
        ))

    def is_type(self, facility_type):
        """
        TODO

        :param str facility_type:
        :rtype: FacilityQuery
        """
        return FacilityQuery(self.session, self.q.filter(
            Facility.facility_type == facility_type,
        ))

    def is_producer(self):
        """
        :rtype: FacilityQuery
        """
        return self.is_type(FacilityType.PRODUCTION)

    def is_consumer(self):
        """
        :rtype: FacilityQuery
        """
        return self.is_type(FacilityType.CONSUMPTION)

    def is_retire_receiver(self):
        """
        :rtype: FacilityQuery
        """
        return FacilityQuery(self.session, self.q.filter(
            Facility.retiring_priority.isnot(None),
        ))

    def is_eligible_to_retire(self, ggo):
        """
        :param Ggo ggo:
        :rtype: FacilityQuery
        """
        return FacilityQuery(self.session, self.q.filter(
            Facility.sector == ggo.sector,
            Facility.facility_type == FacilityType.CONSUMPTION,
        ))

    def get_distinct_sectors(self):
        """
        :rtype: list[str]
        """
        return [row[0] for row in self.session.query(
            self.q.subquery().c.sector.distinct())]

    def get_distinct_gsrn(self):
        """
        :rtype: list[str]
        """
        return [row[0] for row in self.session.query(
            self.q.subquery().c.gsrn.distinct())]

    def get_distinct_technologies(self):
        """
        :rtype: list[str]
        """
        return [row[0] for row in self.session.query(
            self.q.subquery().c.technology.distinct())]

    def get_distinct_tags(self):
        """
        :rtype: list[str]
        """
        ids = [f.id for f in self.q.all()]

        q = self.session \
            .query(FacilityTag.tag.distinct()) \
            .filter(FacilityTag.facility_id.in_(ids))

        return [row[0] for row in q.all()]
