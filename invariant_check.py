"""Original-transition polynomial invariant checker; no producer or core import.

Reuse the owned polynomial parser and exact evaluator. Admission evaluates the
original transition ASTs on a complete degree grid, not producer coefficients.
"""
import hashlib
import importlib.util
import itertools
import json
import math
from pathlib import Path
import re

_spec=importlib.util.spec_from_file_location('ember_invariant_algebra_check',Path(__file__).with_name('algebra_check.py'))
_algebra=importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_algebra)
Invalid=_algebra.Invalid
Limit=_algebra.Limit
need=_algebra.need
exact=_algebra.exact
bounded=_algebra.bounded
value=_algebra.value


def bind(task):
    need(type(task) is dict,'invariant task object')
    allowed={'query','domain','variables','transition','max_degree','focus','initial','name','family'}
    need(not set(task)-allowed,'unsupported invariant task fields')
    need(task.get('query')=='discover_invariant' and task.get('domain')=='QQ','original rational invariant query')
    names=task.get('variables')
    need(type(names) is list and 1<=len(names)<=6 and
         all(type(s) is str and re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,23}',s) for s in names),
         'invariant variable declarations')
    need(len(set(names))==len(names),'duplicate invariant variables')
    expressions=task.get('transition')
    need(type(expressions) is list and len(expressions)==len(names),'one original transition per variable')
    parsed=[_algebra.parse(expression,names) for expression in expressions]
    need(all(sum(degrees)<=4 for _,degrees in parsed),'transition conservative degree sum exceeds four')
    degree=task.get('max_degree',2)
    need(type(degree) is int and 1<=degree<=3,'invariant degree bound 1..3')
    focus=task.get('focus',names)
    need(type(focus) is list and focus and all(type(s) is str and s in names for s in focus),
         'invariant focus must name a nonempty variable subset')
    need(len(set(focus))==len(focus),'duplicate invariant focus')
    initial=None
    if 'initial' in task:
        raw=task['initial']
        need(type(raw) is list and len(raw)==len(names),'initial rational point dimension')
        initial=[exact(q) for q in raw]
    original=dict(query='discover_invariant',domain='QQ',variables=names,
                  transition=expressions,max_degree=degree,focus=focus)
    if initial is not None:original['initial']=task['initial']
    identity=hashlib.sha256(json.dumps(original,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return dict(names=names,transitions=[node for node,_ in parsed],
                transition_degrees=[degrees for _,degrees in parsed],degree=degree,
                focus=[names.index(s) for s in focus],initial=initial,identity=identity)


def polynomial(raw,binding):
    need(type(raw) is list and 1<=len(raw)<=83,'nonempty bounded invariant polynomial')
    terms=_algebra.multiplier_read(raw,len(binding['names']),binding['degree'])
    powers=[exps for exps,_ in terms]
    need(powers==sorted(powers),'invariant terms must be lexicographically sorted')
    need(all(any(exps) for exps in powers),'invariant constant monomial is excluded')
    need(terms[0][1]==1,'invariant first coefficient must normalize to one')
    need(any(exps[i] for exps in powers for i in binding['focus']),'invariant must involve a focus variable')
    return terms


def check(task,certificate,budget):
    binding=bind(task)
    required={'kind','task_id','polynomial'}
    if binding['initial'] is not None:required.add('initial_value')
    need(type(certificate) is dict and set(certificate)==required,'invariant certificate exact fields')
    need(certificate['kind']=='polynomial_invariant' and certificate['task_id']==binding['identity'],
         'original invariant task binding')
    terms=polynomial(certificate['polynomial'],binding)
    n=len(binding['names']);degrees=[0]*n
    # For monomial x**e, deg_i(product(F_j**e_j)) <= sum_j e_j*deg_i(F_j).
    # Taking the maximum with deg_i(x**e) bounds P(F(x))-P(x) before cancellation.
    for exps,_ in terms:
        for i in range(n):
            budget.use(n+1)
            composed=sum(exps[j]*binding['transition_degrees'][j][i] for j in range(n))
            degrees[i]=max(degrees[i],composed,exps[i])
    points=math.prod(d+1 for d in degrees)
    if points>50_000:raise Limit('complete invariant degree grid exceeds 50000 points')
    for point in itertools.product(*(range(d+1) for d in degrees)):
        image=[value(node,binding['names'],point,budget) for node in binding['transitions']]
        before=_algebra.monomial_value(terms,point,budget)
        after=_algebra.monomial_value(terms,image,budget)
        need(before==after,'invariant fails original transition on complete degree grid')
    if binding['initial'] is not None:
        expected=exact(certificate['initial_value'])
        actual=_algebra.monomial_value(terms,binding['initial'],budget)
        need(actual==expected,'invariant initial value differs from original rational point')
    scope='For every rational state x, P(F(x))=P(x) for the original transition expressions.'
    if binding['initial'] is not None:
        scope+=' Every nonnegative iterate from the supplied initial point has the certified initial value.'
    return dict(ok=True,kind='polynomial_invariant',grid_points=points,
                derived_individual_degrees=degrees,initial_checked=binding['initial'] is not None,
                formal_status='NOT_FORMALLY_VERIFIED',scope=scope,
                proof='Complete original-AST degree grid over QQ and the univariate root bound; orbit induction when initialized.')
