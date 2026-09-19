"""Exact original-word certificate checking; no producer or core imports.

Each allowed-prefix state s has continuation series F_s=1+x sum F_t.
The constant matrix is the identity, so these equations have a unique formal
power-series solution. R(0)=1 and coefficient identities N_s=R+x sum N_t
therefore prove F_s=N_s/R for every length. N_empty*Q=P*R transfers the
checked start series to the requested rational formula P/Q, with Q(0)=1.
This is an all-length certificate for these fixed original words; finite count
agreement alone never establishes that result. This custom checker is not a
proof-assistant kernel and supplies no general source-theorem admission.
"""
import hashlib
import json

class Invalid(ValueError): pass
class Limit(RuntimeError): pass

def need(ok, reason):
    if not ok: raise Invalid(reason)

def bind(task):
    need(type(task) is dict, 'word task object')
    need(not set(task)-{'query','patterns','check_through','formula','name','family'}, 'unsupported word task fields')
    need(task.get('query')=='word_avoidance_identity', 'word query')
    words=task.get('patterns')
    need(type(words) is list and len(words)==2, 'exactly two patterns')
    need(all(type(w) is str and 1<=len(w)<=7 and not set(w)-set('01') for w in words), 'binary pattern bounds')
    need(words[0] not in words[1] and words[1] not in words[0], 'distinct reduced patterns required')
    horizon=task.get('check_through')
    need(type(horizon) is int and 0<=horizon<=14, 'original enumeration bound')
    formula=task.get('formula')
    need(formula in ('full_overlap','column_shortcut'), 'requested word formula')
    original={'query':task['query'],'patterns':words,'check_through':horizon,'formula':formula}
    identity=hashlib.sha256(json.dumps(original,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return {'identity':identity,'words':words,'horizon':horizon,'formula':formula}

def integer(x):
    need(type(x) is int, 'integer coefficient required')
    if abs(x).bit_length()>8192: raise Limit('word coefficient bit bound')
    return x

def canonical(p):
    while len(p)>1 and p[-1]==0: p.pop()
    return p

def read_poly(p):
    need(type(p) is list and 1<=len(p)<=65, 'word certificate polynomial degree bound')
    need(len(p)==1 or p[-1]!=0, 'canonical word polynomial')
    return [integer(x) for x in p]

def plus(a,b,budget,scale=1):
    n=max(len(a),len(b))
    if n>129: raise Limit('word polynomial intermediate degree bound')
    out=[]
    for i in range(n):
        budget.use()
        out.append(integer((a[i] if i<len(a) else 0)+scale*(b[i] if i<len(b) else 0)))
    return canonical(out)

def times(a,b,budget):
    if len(a)+len(b)-1>129: raise Limit('word polynomial intermediate degree bound')
    out=[0]*(len(a)+len(b)-1)
    for i,u in enumerate(a):
        for j,v in enumerate(b):
            budget.use(2)
            out[i+j]=integer(out[i+j]+u*v)
    return canonical(out)

def formula(binding,budget):
    """Checker rebuilds overlaps from target prefixes and source endswith."""
    words=binding['words']; entries=[[None,None],[None,None]]
    for target_index,target in enumerate(words):
        for source_index,source in enumerate(words):
            p=[0]*len(target)
            for k in range(1,len(target)):
                budget.use(max(1,k))
                prefix=target[:k]
                if k<len(source) and source.endswith(prefix): p[len(target)-k]+=1
            entries[source_index][target_index]=canonical(p)
    a,b=entries[0]; c,d=entries[1]
    one_a=plus([1],a,budget); one_d=plus([1],d,budget)
    D=plus(times(one_a,one_d,budget),times(b,c,budget),budget,-1)
    weights=[[0]*len(w)+[1] for w in words]
    N=plus(times(weights[0],plus(one_d,b,budget,-1),budget),
           times(weights[1],plus(one_a,c,budget,-1),budget),budget)
    H=plus(times([1,-2],D,budget),N,budget)
    col0=plus(a,c,budget); col1=plus(b,d,budget)
    equal_columns=col0==col1
    B=plus([1],col0,budget)
    if binding['formula']=='column_shortcut':
        need(equal_columns, 'constant-column premise is false')
        P=B; Q=plus(times([1,-2],B,budget),plus(weights[0],weights[1],budget),budget)
    else: P,Q=D,H
    # Check the original substituted identity, rather than promoting numeric
    # matrix guard reports to this polynomial carrier without a binding check.
    g=plus(col0,col1,budget,-1)
    f=plus(times(N,B,budget),times(plus(weights[0],weights[1],budget),D,budget),budget,-1)
    factored=times(times(plus(weights[1],weights[0],budget,-1),plus(b,c,budget,-1),budget),B,budget)
    correction=times(g,plus(times(one_a,weights[1],budget),times(c,weights[0],budget),budget,-1),budget)
    need(f==plus(factored,correction,budget), 'substituted factor identity failed')
    need(D[0]==1 and B[0]==1 and H[0]==1 and Q[0]==1, 'formal-series units')
    guards={'equal_column_polynomials':equal_columns,'equal_length_weights':weights[0]==weights[1],
            'equal_offdiagonal_polynomials':b==c,'equal_diagonal_polynomials':a==d,
            'substituted_residual':f,'factorization_checked':True,
            'formal_series_denominators_have_constant_one':True}
    if equal_columns:
        need((f==[0])==((weights[0]==weights[1]) or b==c), 'original polynomial guard classification')
        guards['column_shortcut_polynomial_identity']=f==[0]
    return P,Q,guards

def automaton(words,budget):
    prefixes={''}
    for word in words:
        for k in range(1,len(word)): prefixes.add(word[:k]); budget.use(k)
    states=sorted(prefixes,key=lambda x:(len(x),x)); transitions={}
    for state in states:
        dest=[]
        for letter in '01':
            text=state+letter
            budget.use(sum(len(w)*max(1,len(text)) for w in words))
            if any(w in text for w in words): continue
            chosen=''
            for candidate in states:
                budget.use(max(1,len(candidate)))
                if len(candidate)>len(chosen) and text.endswith(candidate): chosen=candidate
            dest.append(chosen)
        transitions[state]=dest
    return states,transitions

def coefficients(P,Q,n,budget):
    need(Q[0]==1,'series denominator constant')
    seq=[]
    for j in range(n+1):
        value=P[j] if j<len(P) else 0
        for k in range(1,min(j,len(Q)-1)+1):
            budget.use(2); value=integer(value-Q[k]*seq[j-k])
        seq.append(value)
    return seq

def check(task,certificate,budget):
    binding=bind(task)
    need(type(certificate) is dict and certificate.get('task_id')==binding['identity'], 'word certificate task binding')
    P,Q,guards=formula(binding,budget)
    need(read_poly(certificate.get('numerator'))==P and read_poly(certificate.get('denominator'))==Q, 'original requested formula binding')
    kind=certificate.get('kind')
    if kind=='word_series_identity':
        need(set(certificate)=={'kind','task_id','numerator','denominator','common_denominator','state_numerators'}, 'word identity certificate fields')
        R=read_poly(certificate.get('common_denominator')); need(R[0]==1,'common formal-series unit')
        states,transitions=automaton(binding['words'],budget)
        data=certificate.get('state_numerators')
        need(type(data) is dict and set(data)==set(states), 'complete original prefix states')
        nums={s:read_poly(data[s]) for s in states}
        for state in states:
            rhs=list(R)
            for target in transitions[state]: rhs=plus(rhs,[0]+nums[target],budget)
            need(nums[state]==rhs, 'original DFA state identity failed')
        need(times(nums[''],Q,budget)==times(P,R,budget), 'requested start-series identity failed')
        return {'ok':True,'task_id':binding['identity'],'scope':'all nonnegative lengths for these original patterns',
                'states_checked':len(states),'requested_numerator':P,'requested_denominator':Q,
                'guards':guards,'formal_status':'NOT_FORMALLY_VERIFIED'}
    need(kind=='word_series_counterexample','word certificate kind')
    need(set(certificate)=={'kind','task_id','numerator','denominator','length','actual_count','predicted_count'}, 'word counterexample fields')
    n=certificate.get('length')
    need(type(n) is int and 0<=n<=binding['horizon'],'word counterexample length')
    actual=0
    for number in range(1<<n):
        text=format(number,f'0{n}b') if n else ''
        budget.use(sum(len(w)*max(1,n) for w in binding['words']))
        actual+=not any(word in text for word in binding['words'])
    predicted=coefficients(P,Q,n,budget)[n]
    need(type(certificate.get('actual_count')) is int and type(certificate.get('predicted_count')) is int,'exact original counts')
    need(actual==certificate['actual_count'] and predicted==certificate['predicted_count'] and actual!=predicted,'original counterexample mismatch')
    return {'ok':True,'task_id':binding['identity'],'scope':'original finite word counterexample','length':n,
            'actual_count':actual,'predicted_count':predicted,'guards':guards}
