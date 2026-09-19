"""Original-task polynomial certificate checker. Imports no producer or Ember core."""
import ast
from fractions import Fraction
import hashlib
import itertools
import json
import math
import re

class Invalid(ValueError): pass
class Limit(RuntimeError): pass

def need(condition,reason):
    if not condition: raise Invalid(reason)

def exact(x):
    need(type(x) is list and len(x)==2 and all(type(v) is int for v in x),'rational pair')
    need(x[1]>0 and max(abs(x[0]).bit_length(),x[1].bit_length())<=8192,'rational bound')
    q=Fraction(*x)
    need([q.numerator,q.denominator]==x,'rational must be reduced')
    return q

def bounded(q):
    if max(abs(q.numerator).bit_length(),q.denominator.bit_length())>8192:
        raise Limit('exact arithmetic bit budget')
    return q

def degree(node,names,depth=0):
    need(depth<=24,'expression depth')
    n=len(names)
    if type(node) is ast.Constant:
        need(type(node.value) is int and abs(node.value)<=10**9,'integer literal')
        return [0]*n
    if type(node) is ast.Name:
        need(node.id in names,'undeclared variable')
        return [int(v==node.id) for v in names]
    if type(node) is ast.UnaryOp and type(node.op) in (ast.USub,ast.UAdd):
        return degree(node.operand,names,depth+1)
    need(type(node) is ast.BinOp,'polynomial syntax only')
    a=degree(node.left,names,depth+1)
    if type(node.op) is ast.Pow:
        need(type(node.right) is ast.Constant and type(node.right.value) is int and 0<=node.right.value<=8,'nonnegative literal power')
        out=[x*node.right.value for x in a]
    elif type(node.op) is ast.Div:
        need(type(node.right) is ast.Constant and type(node.right.value) is int and 0<abs(node.right.value)<=10**9,'nonzero constant denominator only')
        out=a
    else:
        b=degree(node.right,names,depth+1)
        if type(node.op) in (ast.Add,ast.Sub): out=[max(x,y) for x,y in zip(a,b)]
        elif type(node.op) is ast.Mult: out=[x+y for x,y in zip(a,b)]
        else: raise Invalid('unsupported polynomial operator')
    need(max(out,default=0)<=8 and sum(out)<=24,'degree bounds')
    return out

def parse(text,names):
    need(type(text) is str and 1<=len(text)<=4096,'expression text bound')
    try: tree=ast.parse(text,mode='eval').body
    except (SyntaxError,RecursionError) as exc: raise Invalid('polynomial parse') from exc
    need(sum(1 for _ in ast.walk(tree))<=256,'expression node bound')
    degrees=degree(tree,names)
    return tree,degrees

def bind(task):
    need(type(task) is dict,'task object')
    allowed={'query','domain','variables','assumptions','nonzero','goal','multiplier_degree',
             'counterexample_radius','guard_grammar','name','family'}
    need(not set(task)-allowed,'unsupported task fields')
    need(task.get('query') in ('polynomial_consequence','discover_guards'),'algebra query')
    grammar=task.get('guard_grammar','pair_equalities')
    need(type(grammar) is str and grammar in ('pair_equalities','coefficient_slices','assumption_slices'),'guard grammar')
    need(task['query']=='discover_guards' or 'guard_grammar' not in task,'guard grammar applies only to discovery')
    need(task.get('domain')=='QQ','rational carrier required')
    names=task.get('variables')
    need(type(names) is list and 1<=len(names)<=6 and all(type(s) is str and re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,23}',s) for s in names),'variable declarations')
    need(len(set(names))==len(names),'duplicate variables')
    equations=task.get('assumptions',[]); nonzero=task.get('nonzero',[])
    need(type(equations) is list and len(equations)<=8 and type(nonzero) is list and len(nonzero)<=8,'assumption bounds')
    need(task['query']!='discover_guards' or len(equations)<=7,'leave one assumption slot for a candidate guard')
    d=task.get('multiplier_degree',2); r=task.get('counterexample_radius',1)
    need(type(d) is int and 0<=d<=3 and type(r) is int and 0<=r<=2,'search bounds')
    goal,gd=parse(task.get('goal'),names)
    gs=[parse(s,names) for s in equations]; nz=[parse(s,names)[0] for s in nonzero]
    original={k:task[k] for k in ('query','domain','variables','goal')}
    original.update(assumptions=equations,nonzero=nonzero,multiplier_degree=d,counterexample_radius=r)
    if grammar!='pair_equalities': original['guard_grammar']=grammar
    identity=hashlib.sha256(json.dumps(original,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return {'names':names,'goal':goal,'goal_degree':gd,'generators':[t for t,_ in gs],
        'generator_degrees':[a for _,a in gs],'nonzero':nz,'degree':d,'radius':r,'identity':identity,
        'guard_grammar':grammar}

def value(node,names,point,budget):
    budget.use()
    if type(node) is ast.Constant: return Fraction(node.value)
    if type(node) is ast.Name: return Fraction(point[names.index(node.id)])
    if type(node) is ast.UnaryOp:
        q=value(node.operand,names,point,budget)
        return -q if type(node.op) is ast.USub else q
    a=value(node.left,names,point,budget)
    if type(node.op) is ast.Pow: return bounded(a**node.right.value)
    if type(node.op) is ast.Div: return bounded(a/node.right.value)
    b=value(node.right,names,point,budget)
    if type(node.op) is ast.Add: return bounded(a+b)
    if type(node.op) is ast.Sub: return bounded(a-b)
    if type(node.op) is ast.Mult: return bounded(a*b)
    raise Invalid('unvalidated expression')

def point_read(point,binding):
    need(type(point) is list and len(point)==len(binding['names']),'point dimension')
    return [exact(v) for v in point]

def admissible(binding,point,budget):
    return (all(value(g,binding['names'],point,budget)==0 for g in binding['generators'])
        and all(value(g,binding['names'],point,budget)!=0 for g in binding['nonzero']))

def multiplier_read(poly,n,degree_limit):
    need(type(poly) is list and len(poly)<=256,'multiplier size')
    result=[]; seen=set()
    for term in poly:
        need(type(term) is list and len(term)==2,'multiplier term')
        exps,coefficient=term
        need(type(exps) is list and len(exps)==n and all(type(v) is int and 0<=v<=degree_limit for v in exps) and sum(exps)<=degree_limit,'multiplier exponents')
        exps=tuple(exps); need(exps not in seen,'duplicate monomial'); seen.add(exps)
        q=exact(coefficient); need(q!=0,'zero multiplier term')
        result.append((exps,q))
    return result

def monomial_value(poly,point,budget):
    result=Fraction(0)
    for exps,c in poly:
        term=c
        for x,k in zip(point,exps): budget.use(); term=bounded(term*x**k)
        budget.use(); result=bounded(result+term)
    return result

def result_status(checked):
    """Classify the result of a fresh check; this does not check a certificate."""
    need(type(checked) is dict and checked.get('ok') is True,'checked algebra result required')
    kind=checked.get('kind')
    if kind in ('polynomial_combination','localized_polynomial_combination'):
        return 'CHECKED_IMPLICATION'
    if kind=='rational_counterexample': return 'CHECKED_COUNTEREXAMPLE'
    raise Invalid('unsupported checked algebra result kind')

def check(task,certificate,budget):
    need(type(certificate) is dict,'certificate object')
    b=bind(task); need(b['identity']==certificate.get('task_id'),'original algebra task binding')
    kind=certificate.get('kind')
    if kind=='rational_counterexample':
        p=point_read(certificate.get('point'),b)
        need(admissible(b,p,budget),'counterexample violates assumptions or nonzero guards')
        residual=value(b['goal'],b['names'],p,budget)
        need(residual!=0,'counterexample has zero residual')
        return {'ok':True,'kind':kind,'residual':[residual.numerator,residual.denominator]}
    localized=kind=='localized_polynomial_combination'
    need(kind=='polynomial_combination' or localized,'certificate kind')
    if localized:
        fields={'kind','task_id','nonzero_index','multipliers','support_point'}
        need(not set(certificate)-fields,'unsupported localized certificate fields')
        index=certificate.get('nonzero_index')
        need(type(index) is int and 0<=index<len(b['nonzero']),'original nonzero guard index')
        guard=b['nonzero'][index]
    raw=certificate.get('multipliers')
    need(type(raw) is list and len(raw)==len(b['generators']),'multiplier count')
    polys=[multiplier_read(p,len(b['names']),b['degree']) for p in raw]
    degrees=list(b['goal_degree'])
    if localized:
        degrees=[g+u for g,u in zip(degrees,degree(guard,b['names']))]
    for poly,gd in zip(polys,b['generator_degrees']):
        if not poly: continue
        hd=[max(e[i] for e,_ in poly) for i in range(len(degrees))]
        degrees=[max(a,g+h) for a,g,h in zip(degrees,gd,hd)]
    points=math.prod(d+1 for d in degrees)
    if points>50_000: raise Limit('complete degree grid exceeds 50000 points')
    # This checks R identically, not merely where the original assumptions hold.
    for p in itertools.product(*(range(d+1) for d in degrees)):
        lhs=value(b['goal'],b['names'],p,budget)
        if localized:
            budget.use()
            lhs=bounded(lhs*value(guard,b['names'],p,budget))
        rhs=Fraction(0)
        for poly,g in zip(polys,b['generators']):
            budget.use()
            term=monomial_value(poly,p,budget)*value(g,b['names'],p,budget)
            if localized: term=bounded(term)
            rhs=bounded(rhs+term)
        need(lhs==rhs,'polynomial-combination identity fails original degree grid')
    support=certificate.get('support_point')
    support_present='support_point' in certificate if localized else support is not None
    if support_present:
        need(admissible(b,point_read(support,b),budget),'guard support violates original conditions')
    result={'ok':True,'kind':kind,'grid_points':points,'derived_individual_degrees':degrees,
        'support_checked':support_present,'formal_status':'NOT_FORMALLY_VERIFIED',
        'scope':'The original rational polynomial implication, via a complete identity grid and the univariate root bound.'}
    if localized:
        result['nonzero_index']=index
        result['scope']='The original rational polynomial implication, via a complete identity grid, the univariate root bound and one original nonzero guard.'
    return result
