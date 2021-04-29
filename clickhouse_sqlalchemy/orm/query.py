from contextlib import contextmanager

from sqlalchemy import exc
from sqlalchemy.sql.base import _generative
import sqlalchemy.orm.query as query_module
from sqlalchemy.orm.query import Query as BaseQuery
from sqlalchemy.orm.util import _ORMJoin as _StandardORMJoin

from ..ext.clauses import (
    ArrayJoin,
    LeftArrayJoin,
    LimitByClause,
    sample_clause,
)


class Query(BaseQuery):
    _with_totals = False
    _final = None
    _sample = None
    _limit_by = None
    _array_join = None

    def _compile_context(self, *args, **kwargs):
        context = super(Query, self)._compile_context(*args, **kwargs)
        query = context.query

        query._with_totals = self._with_totals
        query._final_clause = self._final
        query._sample_clause = sample_clause(self._sample)
        query._limit_by_clause = self._limit_by
        query._array_join = self._array_join

        return context

    @_generative
    def with_totals(self):
        if not self._group_by_clauses:
            raise exc.InvalidRequestError(
                "Query.with_totals() can be used only with specified "
                "GROUP BY, call group_by()"
            )

        self._with_totals = True

    def _add_array_join(self, columns, left):
        join_type = ArrayJoin if not left else LeftArrayJoin
        self._array_join = join_type(*columns)

    @_generative
    def array_join(self, *columns, **kwargs):
        left = kwargs.get("left", False)
        self._add_array_join(columns, left=left)

    @_generative
    def left_array_join(self, *columns):
        self._add_array_join(columns, left=True)

    @_generative
    def final(self):
        self._final = True

    @_generative
    def sample(self, sample):
        self._sample = sample

    @_generative
    def limit_by(self, by_clauses, limit, offset=None):
        self._limit_by = LimitByClause(by_clauses, limit, offset)

    def join(self, *props, **kwargs):
        type = kwargs.pop('type', None)
        strictness = kwargs.pop('strictness', None)
        distribution = kwargs.pop('distribution', None)
        rv = super(Query, self).join(*props, **kwargs)
        joined = list(set(rv._from_obj) - set(self._from_obj))[0]
        new = _ORMJoin._from_standard(joined,
                                      type=type,
                                      strictness=strictness,
                                      distribution=distribution)

        @contextmanager
        def replace_join():
            original = query_module.orm_join
            query_module.orm_join = new
            yield
            query_module.orm_join = original

        with replace_join():
            return super(Query, self).join(*props, **kwargs)

    def outerjoin(self, *props, **kwargs):
        kwargs['type'] = kwargs.get('type') or 'LEFT OUTER'
        return self.join(*props, **kwargs)


class _ORMJoin(_StandardORMJoin):
    @classmethod
    def _from_standard(cls, standard_join, type, strictness, distribution):
        return cls(
            standard_join.left,
            standard_join.right,
            standard_join.onclause,
            type=type,
            strictness=strictness,
            distribution=distribution
        )

    def __init__(self, left, right, onclause=None, type=None, strictness=None,
                 distribution=None):
        super(_ORMJoin, self).__init__(left, right, onclause, False, False,
                                       None, None)
        self.distribution = distribution
        self.strictness = str
        self.type = type
        self.strictness = None
        if strictness:
            self.strictness = strictness
        self.distribution = distribution
        self.type = type

    def __call__(self, *args, **kwargs):
        return self
