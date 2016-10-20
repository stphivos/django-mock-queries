from pydoc import locate

COMPARISON_EXACT = 'exact'
COMPARISON_IEXACT = 'iexact'
COMPARISON_CONTAINS = 'contains'
COMPARISON_ICONTAINS = 'icontains'
COMPARISON_GT = 'gt'
COMPARISON_GTE = 'gte'
COMPARISON_LT = 'lt'
COMPARISON_LTE = 'lte'
COMPARISON_IN = 'in'
COMPARISON_ISNULL = 'isnull'
COMPARISONS = (
    COMPARISON_EXACT,
    COMPARISON_IEXACT,
    COMPARISON_CONTAINS,
    COMPARISON_ICONTAINS,
    COMPARISON_GT,
    COMPARISON_GTE,
    COMPARISON_LT,
    COMPARISON_LTE,
    COMPARISON_IN,
    COMPARISON_ISNULL,
)

CONNECTORS_OR = 'OR'
CONNECTORS_AND = 'AND'
CONNECTORS = (
    CONNECTORS_OR,
    CONNECTORS_AND,
)

AGGREGATES_SUM = 'SUM'
AGGREGATES_COUNT = 'COUNT'
AGGREGATES_MAX = 'MAX'
AGGREGATES_MIN = 'MIN'
AGGREGATES_AVG = 'AVG'
AGGREGATES = (
    AGGREGATES_SUM,
    AGGREGATES_COUNT,
    AGGREGATES_MAX,
    AGGREGATES_MIN,
    AGGREGATES_AVG,
)

DjangoQ = locate('django.db.models.Q')
DjangoQuerySet = locate('django.db.models.QuerySet')
ObjectDoesNotExist = locate('django.core.exceptions.ObjectDoesNotExist')
MultipleObjectsReturned = locate('django.core.exceptions.MultipleObjectsReturned')
