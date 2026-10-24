"""Exact conditional decomposition for small ROBDDs.

If F(A,B,S) = (exists B. F) AND (exists A. F), the two projections
form a sound separator factorization. Equality is checked, never assumed.
Variables outside F's support are ignored; no approximate independence.
"""
from __future__ import annotations
from dataclasses import dataclass
from itertools import combinations
from legacy53.bdd import BDD, SymbolicLimit

@dataclass(frozen=True)
class Separator:
    left: tuple[int,...]
    right: tuple[int,...]
    shared: tuple[int,...]
    factor_left:int
    factor_right:int
    checked_equal:bool
    def data(self):
        return {'left':list(self.left),'right':list(self.right),'shared':list(self.shared),
                'checked_equal':self.checked_equal}

def support(m:BDD,root:int):
    found=set();seen=set();stack=[root]
    while stack:
        u=stack.pop()
        if u<=1 or u in seen:continue
        seen.add(u)
        v,lo,hi=m.nodes[u];found.add(v);stack.extend((lo,hi))
    return tuple(sorted(found))

def equivalent(m:BDD,a:int,b:int):
    """Uses satisfiability of asymmetric difference, not approximate equality."""
    return not m.intersects(a,m.neg(b)) and not m.intersects(b,m.neg(a))

def discover(m:BDD,f:int,max_separator:int=2,max_variables:int=9):
    variables=support(m,f)
    if len(variables)>max_variables:raise SymbolicLimit('separator discovery width budget')
    if len(variables)<2:return None
    # Prefer the smallest shared interface and balanced nonempty private sides.
    for size in range(min(max_separator,len(variables)-2)+1):
        candidates=[]
        for shared in combinations(variables,size):
            private=tuple(x for x in variables if x not in shared)
            # Quotient by swapping the left and right components.
            for width in range(1,len(private)//2+1):
                for left in combinations(private,width):
                    right=tuple(v for v in private if v not in left)
                    if len(left)==len(right) and left>right:continue
                    candidates.append((abs(len(left)-len(right)),tuple(left),right,tuple(shared)))
        for _,left,right,shared in sorted(candidates):
            # existential projection is a logically exact operation
            projected_left=m.exists(f,right)
            projected_right=m.exists(f,left)
            if equivalent(m,f,m.AND(projected_left,projected_right)):
                return Separator(left,right,shared,projected_left,projected_right,True)
    return None

def factor_count(m:BDD,part:Separator):
    """Join over separator assignments (exact but exponential in separator width)."""
    if not part.checked_equal:raise ValueError('uncertified factorization')
    count=0
    for mask in range(1<<len(part.shared)):
        assignment=m.AND(*(m.literal(v,(mask>>i)&1) for i,v in enumerate(part.shared)))
        a=m.AND(part.factor_left,assignment)
        b=m.AND(part.factor_right,assignment)
        # Both local factors contain their private side and the fixed shared
        # assignment. sat_count counts all global variables, including the
        # opposite private side and variables outside F's support.
        outside=m.variables-len(part.left)-len(part.right)-len(part.shared)
        count_a=m.sat_count(a)//(1<<(len(part.right)+outside))
        count_b=m.sat_count(b)//(1<<(len(part.left)+outside))
        count+=count_a*count_b*(1<<outside)
    return count


def build_from_tables(m:BDD,tables:list[dict]):
    """Construct conjunction of explicitly enumerated small local relations."""
    terms=[]
    for factor in tables:
        keys=tuple(factor['variables']);allowed=factor['allowed']
        if not allowed:terms.append(0);continue
        clauses=[]
        for assignment in allowed:
            if len(assignment)!=len(keys):raise ValueError('bad local assignment')
            clauses.append(m.AND(*(m.literal(v,bit) for v,bit in zip(keys,assignment))))
        terms.append(m.OR(*clauses))
    return m.AND(*terms)
