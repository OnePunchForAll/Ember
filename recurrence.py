"""Discover exact recurrence candidates; only the separate checker admits them."""
from fractions import Fraction as Q

def encoded(value):
    q=Q(value);return [q.numerator,q.denominator]

def word_system(words,budget):
    """Proposal-side automaton: suffix deletion, separate from the checker."""
    states=sorted({w[:k] for w in words for k in range(len(w))},key=lambda s:(len(s),s))
    index={s:i for i,s in enumerate(states)};M=[[0]*len(states) for _ in states]
    for i,state in enumerate(states):
        for symbol in '01':
            suffix=state+symbol;budget.use(sum(len(w) for w in words))
            if any(suffix.endswith(w) for w in words):continue
            while suffix not in index:suffix=suffix[1:];budget.use()
            M[i][index[suffix]]+=1
    return M,[1]+[0]*(len(states)-1),[1]*len(states)

def row_step(row,M,budget,checker):
    out=[Q(0)]*len(row)
    for i,value in enumerate(row):
        for j,weight in enumerate(M[i]):
            budget.use(2);out[j]=checker.bounded(out[j]+value*weight)
    return out

def scalar(row,v,budget,checker):
    total=Q(0)
    for x,y in zip(row,v):budget.use(2);total=checker.bounded(total+x*y)
    return total

def solve_linear(rows,targets,width,budget,checker):
    """Exact proposal-only elimination, free columns set to zero."""
    pivots={}
    for coefficients,target in zip(rows,targets):
        budget.use(width+1);row=list(map(Q,coefficients))+[Q(target)]
        for lead,prior in sorted(pivots.items()):
            scale=row[lead]
            if scale:
                for j in range(lead,width+1):
                    budget.use(2);row[j]=checker.bounded(row[j]-scale*prior[j])
        lead=next((j for j in range(width) if row[j]),None)
        if lead is None:
            if row[-1]:return None
            continue
        scale=row[lead]
        for j in range(lead,width+1):budget.use();row[j]=checker.bounded(row[j]/scale)
        pivots[lead]=row
    result=[Q(0)]*width
    for lead,row in sorted(pivots.items(),reverse=True):
        value=row[-1]
        for j in range(lead+1,width):budget.use(2);value=checker.bounded(value-row[j]*result[j])
        result[lead]=value
    return result

def run(task,budget,checker):
    b=checker.bind(task);n=b['n']
    if 'words' in b:M,u,v=word_system(b['words'],budget)
    else:M,u,v=b['matrix'],b['initial'],b['terminal']
    # Only observations are generated here; sample agreement cannot admit a law.
    rows=[list(map(Q,u))]
    for _ in range(2*n):rows.append(row_step(rows[-1],M,budget,checker))
    prefix=[scalar(row,v,budget,checker) for row in rows]
    trace=[dict(direction='S',operation='observe_original_system',terms=len(prefix))]
    relation=None;s=None
    for width in range(n+1):
        proposal=solve_linear([[rows[i][j] for i in range(width)] for j in range(n)],rows[width],width,budget,checker)
        if proposal is not None:relation=proposal;s=width;break
    if relation is None:return dict(status='UNKNOWN',reason='no row closure found within dimension',trace=trace)
    trace.append(dict(direction='N',operation='propose_closed_row_span',row_order=s))
    failed_orders=[]
    for r in range(b['max_order']+1):
        fitting=[[prefix[h+j] for j in range(r)] for h in range(len(prefix)-r)]
        candidate=solve_linear(fitting,prefix[r:],r,budget,checker)
        if candidate is None:
            failed_orders.append(r);continue
        trace.append(dict(direction='N',operation='propose_scalar_recurrence',order=r,
                          evidence='finite prefix proposal only'))
        certificate=dict(kind='linear_sequence_recurrence',task_id=b['identity'],order=r,
            coefficients=[encoded(q) for q in candidate],row_order=s,row_relation=[encoded(q) for q in relation],
            initial_terms=[encoded(q) for q in prefix[:r]])
        before=budget.work
        try:checked=checker.check(task,certificate,budget)
        except checker.Invalid as exc:
            trace.append(dict(direction='W',operation='refuse_candidate_on_original_system',reason=str(exc)))
            continue
        trace.append(dict(direction='S',operation='check_entry_closure_and_residual',accepted=True))
        return dict(status='CHECKED_RECURRENCE',certificate=certificate,check=checked,trace=trace,
            observed_terms=[encoded(q) for q in prefix],failed_prefix_orders=failed_orders,
            checking_work=budget.work-before,scope=checked['scope'],
            limits='Fixed linear-recurrence grammar; no empirical-law inference, minimality certificate or open-problem novelty claim.')
    return dict(status='UNKNOWN',reason='no verified recurrence within requested order and work bounds',trace=trace,
        observed_terms=[encoded(q) for q in prefix],failed_prefix_orders=failed_orders)
