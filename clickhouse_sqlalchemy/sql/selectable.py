from __future__ import annotations

from typing import Any, Tuple, TYPE_CHECKING

from sqlalchemy.sql import coercions, roles
from sqlalchemy.sql.base import _generative
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.sql.selectable import (
    Select as StandardSelect,
)

from ..ext.clauses import (
    ArrayJoin,
    LeftArrayJoin,
    LimitByClause,
    sample_clause,
)

if TYPE_CHECKING:
    from ._typing import _ColumnExpressionArgument

__all__ = ('Select', 'select')


class Select(StandardSelect):
    _with_cube = False
    _with_rollup = False
    _with_totals = False
    _final_clause = None
    _sample_clause = None
    _limit_by_clause = None
    _array_join = None
    _qualify_criteria: Tuple[ColumnElement[Any], ...] = ()

    @_generative
    def qualify(self, *qualify: _ColumnExpressionArgument[bool]) -> Self:
        """Return a new :func:`_expression.select` construct with
        the given expression added to
        its HAVING clause, joined to the existing clause via AND, if any.

        """

        for criterion in qualify:
            qualify_criteria = coercions.expect(
                roles.WhereHavingRole, criterion, apply_propagate_attrs=self
            )
            self._qualify_criteria += (qualify_criteria,)
        return self

    @_generative
    def with_cube(self):
        self._with_cube = True
        return self

    @_generative
    def with_rollup(self):
        self._with_rollup = True
        return self

    @_generative
    def with_totals(self):
        self._with_totals = True
        return self

    @_generative
    def final(self):
        self._final_clause = True
        return self

    @_generative
    def sample(self, sample):
        self._sample_clause = sample_clause(sample)
        return self

    @_generative
    def limit_by(self, by_clauses, limit, offset=None):
        self._limit_by_clause = LimitByClause(by_clauses, limit, offset)
        return self

    def _add_array_join(self, columns, left):
        join_type = ArrayJoin if not left else LeftArrayJoin
        self._array_join = join_type(*columns)

    @_generative
    def array_join(self, *columns, **kwargs):
        left = kwargs.get("left", False)
        self._add_array_join(columns, left=left)
        return self

    @_generative
    def left_array_join(self, *columns):
        self._add_array_join(columns, left=True)
        return self

    def join(self, right, onclause=None, isouter=False, full=False, type=None,
             strictness=None, distribution=None):
        return super().join(right, onclause=onclause, isouter=isouter, full=full)


select = Select
