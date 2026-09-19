"""Bounded original-word generating-function producer; imports no checker.

Overlap rows are source words, columns target words; exponent is appended
target length. The checker reconstructs the requested rational formula and the
avoidance DFA separately. A proposed common denominator may retain state modes
which cancel in the start series. Exact state identities, not finite agreement,
establish the returned all-length result for the two supplied words.
"""
import itertools

def trim(p):
    while len(p)>1 and p[-1]==0: p.pop()
    return p

def add(a,b,budget,scale=1):
    out=[0]*max(len(a),len(b))
    for i,v in enumerate(a): out[i]+=v; budget.use()
    for i,v in enumerate(b): out[i]+=scale*v; budget.use()
    return trim(out)

def multiply(a,b,budget):
    out=[0]*(len(a)+len(b)-1)
    for i,u in enumerate(a):
        for j,v in enumerate(b): out[i+j]+=u*v; budget.use(2)
    return trim(out)

def produce_formula(words,budget):
    overlap=[]
    for source in words:
        row=[]
        for target in words:
            p=[0]*len(target)
            for k in range(1,min(len(source),len(target))):
                budget.use(k)
                if source[-k:]==target[:k]: p[len(target)-k]+=1
            row.append(trim(p))
        overlap.append(row)
    a,b=overlap[0]; c,d=overlap[1]
    L=[[0]*len(w)+[1] for w in words]
    D=add(multiply(add([1],a,budget),add([1],d,budget),budget),multiply(b,c,budget),budget,-1)
    N=add(multiply(L[0],add(add([1],d,budget),b,budget,-1),budget),
          multiply(L[1],add(add([1],a,budget),c,budget,-1),budget),budget)
    H=add(multiply([1,-2],D,budget),N,budget)
    col0=add(a,c,budget); col1=add(b,d,budget); B=add([1],col0,budget)
    J=add(multiply([1,-2],B,budget),add(L[0],L[1],budget),budget)
    return {'full_numerator':D,'full_denominator':H,'shortcut_numerator':B,
            'shortcut_denominator':J,'equal_columns':col0==col1,'overlap':overlap,'weights':L}

def state_proposal(words,R,budget,checker):
    states=sorted({w[:k] for w in words for k in range(len(w))},key=lambda s:(len(s),s))
    edges=[]
    for state in states:
        row=[]
        for bit in '01':
            text=state+bit
            budget.use(sum(len(w)*max(1,len(text)) for w in words))
            if any(text.endswith(w) for w in words): continue
            # Delete leading symbols until the remaining suffix is a state.
            suffix=text
            while suffix not in states: suffix=suffix[1:]; budget.use()
            row.append(states.index(suffix)); budget.use(len(states))
        edges.append(row)
    # If R is a common denominator, the adjugate bound gives degree <=deg R+m-1.
    # Failure of the subsequent identities is UNKNOWN, never a membership claim.
    degree=len(R)+len(states)-2
    checker.need(degree<=64,'word proposal degree bound')
    counts=[[1] for _ in states]
    for n in range(1,degree+1):
        for i,row in enumerate(edges):
            value=0
            for target in row: value+=counts[target][n-1]; budget.use()
            counts[i].append(checker.integer(value))
    nums={}
    for state,seq in zip(states,counts):
        poly=[]
        for n in range(degree+1):
            value=0
            for k in range(min(n,len(R)-1)+1): value+=R[k]*seq[n-k]; budget.use(2)
            poly.append(checker.integer(value))
        nums[state]=trim(poly)
    return nums

def coefficients(P,Q,horizon,budget,checker):
    out=[]
    for n in range(horizon+1):
        value=P[n] if n<len(P) else 0
        for k in range(1,min(n,len(Q)-1)+1): value-=Q[k]*out[n-k]; budget.use(2)
        out.append(checker.integer(value))
    return out

def run(task,budget,checker):
    bound=checker.bind(task); words=bound['words']; data=produce_formula(words,budget)
    if bound['formula']=='column_shortcut':
        checker.need(data['equal_columns'],'constant-column premise is false')
        P,Q=data['shortcut_numerator'],data['shortcut_denominator']
    else: P,Q=data['full_numerator'],data['full_denominator']
    common=data['full_denominator']
    certificate={'kind':'word_series_identity','task_id':bound['identity'],'numerator':P,'denominator':Q,
                 'common_denominator':common,'state_numerators':state_proposal(words,common,budget,checker)}
    try:
        checked=checker.check(task,certificate,budget)
        return {'status':'CHECKED_WORD_IDENTITY','task_id':bound['identity'],'certificate':certificate,'check':checked,
                'source_binding':{'patterns':words,'overlap':data['overlap'],'length_weights':data['weights']},
                'trace':[{'direction':'S','operation':'bind_original_words_and_overlap_formula'},
                         {'direction':'N','operation':'propose_common_denominator_state_numerators'},
                         {'direction':'S','operation':'check_original_DFA_polynomial_equations'}],
                'limits':'All-length identity for these fixed words through a custom exact checker; not a general overlap theorem or new discovery.'}
    except checker.Invalid as exc:
        # A failed certificate does not refute the formula. Seek an actual word
        # count discrepancy within the declared finite diagnostic horizon.
        predicted=coefficients(P,Q,bound['horizon'],budget,checker)
        for n in range(bound['horizon']+1):
            actual=0
            for symbols in itertools.product('01',repeat=n):
                text=''.join(symbols)
                budget.use(sum(len(w)*max(1,n) for w in words))
                actual+=all(w not in text for w in words)
            if actual!=predicted[n]:
                certificate={'kind':'word_series_counterexample','task_id':bound['identity'],
                             'numerator':P,'denominator':Q,'length':n,'actual_count':actual,'predicted_count':predicted[n]}
                checked=checker.check(task,certificate,budget)
                return {'status':'CHECKED_WORD_COUNTEREXAMPLE','task_id':bound['identity'],'certificate':certificate,'check':checked,
                        'identity_attempt_failure':str(exc),
                        'source_binding':{'patterns':words,'overlap':data['overlap'],'length_weights':data['weights']}}
        return {'status':'UNKNOWN','task_id':bound['identity'],
                'identity_attempt_failure':str(exc),
                'reason':'no state identity certificate and no original counterexample within the declared horizon',
                'finite_counts_agree_through':bound['horizon']}
