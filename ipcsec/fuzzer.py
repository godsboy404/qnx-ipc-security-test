import random
from dataclasses import replace
from .model import Case

def generate(count, seed=20261015):
    """Bounded deterministic corpus; values change logical fields, never allocate claimed sizes."""
    rng = random.Random(seed)
    cases = []
    for i in range(count):
        c = Case(f'CASE-{i:04d}')
        mode = i % 4
        if mode == 1:
            c = replace(c, declared_length=rng.choice([0,1,63,64,65,2**31-1]), mutation='boundary')
        elif mode == 2:
            key, value = rng.choice([('operation','INVALID'),('offset',-1),('offset',65),('flags',8)])
            c = replace(c, **{key:value}, mutation='field')
        elif mode == 3:
            c = replace(c, operation='INVALID', declared_length=65, flags=8, mutation='combination')
        cases.append(c)
    return cases

class FeedbackScheduler:
    """Exploratory ordering only; no coverage-guided or ML claim."""
    def __init__(self, cases):
        self.pending = list(cases)

    def next(self, previous=None):
        if previous and previous['target_outcome'] == 'SIMULATED_FAULT':
            self.pending.sort(key=lambda c: c.mutation != 'boundary')
        if not self.pending:
            return None
        return self.pending.pop(0)
