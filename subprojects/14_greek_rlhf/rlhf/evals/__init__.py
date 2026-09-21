"""Evaluation results with an identity, and comparisons that declare their variable.

Public surface: the two builders (each returns a sealed Result), compare(), comparable(), Store,
stats, and weights_receipt(). The manifest-level check is deliberately NOT exported.
"""
from .manifest import from_lm_eval, from_official_greekmmlu                    # noqa: F401
from .result import Result                                                     # noqa: F401
from .compare import compare, comparable, ComparabilityError, POLICIES         # noqa: F401
from .weights import receipt as weights_receipt, load_receipt                  # noqa: F401
from .store import Store                                                       # noqa: F401
from . import stats                                                            # noqa: F401
