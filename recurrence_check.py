"""Exact original-system recurrence checker; imports no producer or Ember core."""
from fractions import Fraction as Q
import hashlib
import json

class Invalid(ValueError): pass
class Limit(RuntimeError): pass

def need(condition,reason):
    if not condition: raise Invalid(reason)

def bounded(x):
    q=Q(x)
    if max(abs(q.numerator).bit_length(),q.denominator.bit_length())>8192:
        raise Limit('recurrence exact arithmetic bit limit')
    return q

def rational(pair):
    need(type(pair) is list and len(pair)==2 and all(type(x) is int for x in pair),'recurrence rational pair')
    need(pair[1]>0 and max(abs(pair[0]).bit_length(),pair[1].bit_length())<=8192,'recurrence rational bound')
    q=Q(*pair);need([q.numerator,q.denominator]==pair,'recurrence rational must be reduced')
    return q

def bind(task):
    need(type(task) is dict and task.get('query') in ('discover_recurrence','discover_word_recurrence'),'recurrence task query')
    if task['query']=='discover_word_recurrence':
        need(not set(task)-{'query','patterns','max_order','name','family'},'unsupported word recurrence fields')
        words=task.get('patterns')
        need(type(words) is list and len(words)==2,'exactly two recurrence patterns')
        need(all(type(w) is str and 1<=len(w)<=7 and not set(w)-set('01') for w in words),'binary recurrence pattern bounds')
        need(words[0] not in words[1] and words[1] not in words[0],'distinct reduced recurrence patterns required')
        n=len({w[:k] for w in words for k in range(len(w))})
        order=task.get('max_order',n)
        need(type(order) is int and 0<=order<=n,'word recurrence order bound')
        original=dict(query='discover_word_recurrence',patterns=words,max_order=order)
        identity=hashlib.sha256(json.dumps(original,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        return dict(words=words,n=n,max_order=order,identity=identity)
    need(not set(task)-{'query','domain','matrix','initial','terminal','max_order','name','family'},'unsupported recurrence fields')
    need(task.get('domain')=='QQ','recurrence rational carrier required')
    M,u,v=task.get('matrix'),task.get('initial'),task.get('terminal')
    need(type(M) is list and 1<=len(M)<=64,'recurrence dimension 1..64')
    n=len(M)
    need(all(type(row) is list and len(row)==n for row in M),'recurrence square matrix')
    need(type(u) is list and type(v) is list and len(u)==len(v)==n,'recurrence vector shape')
    need(all(type(x) is int and abs(x)<=1_000_000 for row in M for x in row),'recurrence integer matrix entries')
    need(all(type(x) is int and abs(x)<=1_000_000 for x in u+v),'recurrence integer vector entries')
    order=task.get('max_order',min(n,16))
    need(type(order) is int and 0<=order<=n,'recurrence order bound 0..dimension')
    original=dict(query='discover_recurrence',domain='QQ',matrix=M,initial=u,terminal=v,max_order=order)
    identity=hashlib.sha256(json.dumps(original,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return dict(matrix=M,initial=u,terminal=v,n=n,max_order=order,identity=identity)

def original_word_system(words,budget):
    """All original prefix states and both binary letters, reconstructed here."""
    prefixes={''}
    for word in words:
        for k in range(1,len(word)):budget.use(k);prefixes.add(word[:k])
    states=sorted(prefixes,key=lambda text:(len(text),text));M=[[0]*len(states) for _ in states]
    for i,state in enumerate(states):
        for letter in '01':
            extended=state+letter
            budget.use(sum(len(w)*max(1,len(extended)) for w in words))
            if any(w in extended for w in words):continue
            best=''
            for possible in states:
                budget.use(max(1,len(possible)))
                if len(possible)>len(best) and extended.endswith(possible):best=possible
            M[i][states.index(best)]+=1
    return M,[1]+[0]*(len(states)-1),[1]*len(states)

def dot(a,b,budget):
    total=Q(0)
    for x,y in zip(a,b):
        budget.use(2);total=bounded(total+bounded(x*y))
    return total

def check(task,certificate,budget):
    b=bind(task);n=b['n']
    if 'words' in b:M,u,v=original_word_system(b['words'],budget)
    else:M,u,v=b['matrix'],b['initial'],b['terminal']
    need(type(certificate) is dict and set(certificate)=={'kind','task_id','order','coefficients','row_order','row_relation','initial_terms'},'recurrence certificate shape')
    need(certificate['kind']=='linear_sequence_recurrence' and certificate['task_id']==b['identity'],'original recurrence task binding')
    r,s=certificate['order'],certificate['row_order']
    need(type(r) is int and 0<=r<=b['max_order'],'recurrence certificate order')
    need(type(s) is int and 0<=s<=n,'recurrence row closure order')
    raw=certificate['coefficients'];closure=certificate['row_relation'];initial=certificate['initial_terms']
    need(type(raw) is list and len(raw)==r and type(closure) is list and len(closure)==s,'recurrence coefficient dimensions')
    need(type(initial) is list and len(initial)==r,'recurrence initial term count')
    c=[rational(x) for x in raw];d=[rational(x) for x in closure];a=[rational(x) for x in initial]
    # Reconstruct the invariant's entry and every successor from original M,u.
    rows=[list(map(Q,u))]
    for _ in range(s):
        row=rows[-1]
        rows.append([dot(row,[M[i][j] for i in range(n)],budget) for j in range(n)])
    for j in range(n):
        need(rows[s][j]==dot(d,[rows[i][j] for i in range(s)],budget),'row span is not closed or entry is missing')
    # Reconstruct original columns and sequence seeds, not producer observations.
    columns=[list(map(Q,v))]
    for h in range(r):
        need(dot(u,columns[h],budget)==a[h],'recurrence initial term differs from original system')
        columns.append([dot(row,columns[-1],budget) for row in M])
    residual=[]
    for j in range(n):
        budget.use();residual.append(bounded(columns[r][j]-dot(c,[columns[i][j] for i in range(r)],budget)))
    for i in range(s):need(dot(rows[i],residual,budget)==0,'recurrence residual visible in original row orbit')
    scope=('a(h) counts binary words of length h avoiding both original patterns' if 'words' in b else 'a(h)=u*M**h*v for the original system')
    return dict(ok=True,order=r,row_order=s,
        scope='For every integer h>=0, a(h+r)=sum(c[j]*a(h+j)); '+scope+'.',
        proof='Original entry, row-span closure and residual orthogonality; induction in exact QQ.',
        formal_status='NOT_FORMALLY_VERIFIED',minimality='NOT_CERTIFIED')
