"""Ember's first bounded offline mechanism: checked transition-count compression.

No model, network, third-party dependency, source program execution or eval.
TPM directions identify real operations in the trace, not truth votes.
"""
from __future__ import annotations
import argparse
import hashlib
import itertools
import importlib.util
import json
from pathlib import Path
import sys
import time
from types import SimpleNamespace

VERSION='ember-pyramid-16'
STATE_LIMIT=1_048_576
# Exact answers can exceed Python's default 4300-digit decimal conversion limit.
INT_DIGITS=100_000
_MODULES={}

class Refused(ValueError): pass
class Exhausted(RuntimeError): pass

class Budget:
    def __init__(self,limit=10_000_000): self.limit=limit; self.work=0
    def use(self,amount=1):
        self.work+=amount
        if self.work>self.limit: raise Exhausted('work budget exhausted')

def canonical(x): return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False)
def digest(x): return hashlib.sha256(canonical(x).encode()).hexdigest()

def load_json(path):
    with Path(path).open('rb') as handle: raw=handle.read(STATE_LIMIT+1)
    if len(raw)>STATE_LIMIT: raise Refused('JSON input exceeds 1 MiB')
    def pairs(items):
        out={}
        for key,value in items:
            if key in out: raise Refused('duplicate JSON key')
            out[key]=value
        return out
    def constant(value): raise Refused('nonfinite JSON value')
    return json.loads(raw.decode('utf-8'),object_pairs_hook=pairs,parse_constant=constant)

def local_module(name):
    if name not in ('algebra','algebra_check','word_series','word_check','campaign','recurrence','recurrence_check','invariant','invariant_check','invariant_map','obligations','recursive','recursive_check','source_episode','apex','apex_check','pyramid'): raise Refused('unknown owned module')
    if name not in _MODULES:
        spec=importlib.util.spec_from_file_location('ember_'+name,Path(__file__).with_name(name+'.py'))
        module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        _MODULES[name]=module
    return _MODULES[name]


def read_state(path):
    state={'version':VERSION,'observations':[]}
    if path is not None and Path(path).exists():
        state=load_json(path)
        if type(state) is not dict or state.get('version') not in (VERSION,'ember-pyramid-2','ember-pyramid-3','ember-pyramid-4','ember-pyramid-5','ember-pyramid-6','ember-pyramid-7','ember-pyramid-8','ember-pyramid-9','ember-pyramid-10','ember-pyramid-11','ember-pyramid-12','ember-pyramid-13','ember-pyramid-14','ember-pyramid-15'):
            raise Refused('incompatible experience generation')
        if type(state.get('observations')) is not list or len(state['observations'])>128:
            raise Refused('experience shape')
        if any(type(o) is not dict or type(o.get('task_id')) is not str for o in state['observations']):
            raise Refused('experience observation shape')
        if state['version']!=VERSION:
            state['migrated_from']=state['version']; state['version']=VERSION
    return state


def retain(state,path,observation):
    if path is None: return
    state['observations']=[o for o in state['observations'] if o['task_id']!=observation['task_id']]+[observation]
    state['observations']=state['observations'][-128:]
    while len(canonical(state).encode('utf-8'))+1>STATE_LIMIT and state['observations']:
        state['observations'].pop(0)
    destination=Path(path); destination.parent.mkdir(parents=True,exist_ok=True)
    temporary=destination.with_suffix(destination.suffix+'.tmp')
    temporary.write_text(canonical(state)+'\n',encoding='utf-8',newline='\n'); temporary.replace(destination)


def lemma_candidates(state,include_guarded=False):
    """Bounded original proof candidates, with guarded transfer an explicit opt-in."""
    if type(include_guarded) is not bool:raise Refused('guarded lemma selection must be Boolean')
    kinds=('polynomial_combination','localized_polynomial_combination') if include_guarded else ('polynomial_combination',)
    return [o for o in reversed(state['observations'])
            if o.get('kind')=='polynomial_consequence' and o.get('status')=='CHECKED_IMPLICATION'
            and type(o.get('task')) is dict and type(o.get('certificate')) is dict
            and o['certificate'].get('kind') in kinds][:8]


def remember_lemma(state,task,result):
    """Keep original checked evidence; selection follows the receiving policy.

    Callers admit the result first. Subsequent use still replays it; persisted
    status, task_id and source descriptions cannot establish a receiving claim.
    A campaign writes these records atomically with its active checkpoint.
    """
    if task.get('query')!='polynomial_consequence' or result.get('status')!='CHECKED_IMPLICATION': return
    identity=local_module('algebra_check').bind(task)['identity']
    observation={'task_id':identity,'kind':'polynomial_consequence','status':'CHECKED_IMPLICATION',
                 'task':json.loads(canonical(task)),'certificate':json.loads(canonical(result['certificate']))}
    state['observations']=[o for o in state['observations'] if o['task_id']!=identity]+[observation]
    state['observations']=state['observations'][-128:]


def invariant_candidates(state):
    """Remembered source laws are bounded proposals, replayed before use."""
    return [o for o in reversed(state['observations'])
            if o.get('kind')=='discover_invariant' and o.get('status')=='CHECKED_INVARIANT'
            and type(o.get('task')) is dict and type(o.get('certificate')) is dict][:8]


def remember_invariant(state,task,result):
    """Campaign admission precedes storage; later source and target checks remain required."""
    if task.get('query')!='discover_invariant' or result.get('status')!='CHECKED_INVARIANT': return
    identity=local_module('invariant_check').bind(task)['identity']
    observation=dict(task_id=identity,kind='discover_invariant',status='CHECKED_INVARIANT',
        task=json.loads(canonical(task)),certificate=json.loads(canonical(result['certificate'])))
    state['observations']=[o for o in state['observations'] if o['task_id']!=identity]+[observation]
    state['observations']=state['observations'][-128:]


def bind_discovery(task):
    if type(task) is not dict or task.get('query')!='test_overlap_shortcut':
        raise Refused('unsupported discovery query')
    if set(task)-{'query','claim','max_pattern_length','check_through','name','family'}: raise Refused('unsupported discovery fields')
    if task.get('claim')!='equal_column_sums_imply_weighted_shortcut':
        raise Refused('unsupported conjecture grammar')
    length=task.get('max_pattern_length'); horizon=task.get('check_through')
    if type(length) is not int or not 1<=length<=7: raise Refused('pattern bound')
    if type(horizon) is not int or not 0<=horizon<=14: raise Refused('enumeration bound')
    return length,horizon,digest({'query':task['query'],'claim':task['claim'],
        'max_pattern_length':length,'check_through':horizon})


def candidate_overlap(words,budget):
    """Producer representation: proper overlaps are counted by appended length."""
    degree=max(map(len,words)); A=[]
    for source in words:
        row=[]
        for target in words:
            poly=[0]*(degree+1)
            for length in range(1,min(len(source),len(target))):
                budget.use()
                if source[-length:]==target[:length]: poly[len(target)-length]+=1
            row.append(poly)
        A.append(row)
    return A


def shortcut_coefficients(words,beta,horizon,budget):
    numerator=list(beta); numerator[0]+=1
    denominator=[0]*(max(len(numerator)+1,max(map(len,words))+1))
    for i,value in enumerate(numerator):
        denominator[i]+=value; denominator[i+1]-=2*value; budget.use(2)
    for word in words: denominator[len(word)]+=1; budget.use()
    sequence=[]
    for n in range(horizon+1):
        value=numerator[n] if n<len(numerator) else 0
        for k in range(1,min(n,len(denominator)-1)+1):
            value-=denominator[k]*sequence[n-k]; budget.use(2)
        sequence.append(value)
    return sequence


def original_count(words,n,budget):
    count=0
    for letters in itertools.product('01',repeat=n):
        text=''.join(letters); budget.use(len(words)*max(1,n))
        count+=all(word not in text for word in words)
    return count


def check_discovery(task,certificate,budget):
    """Rebuild the original finite witness; no producer overlap table is trusted."""
    max_length,horizon,identity=bind_discovery(task)
    if type(certificate) is not dict or certificate.get('task_id')!=identity: raise Refused('wrong discovery task')
    words=certificate.get('patterns'); n=certificate.get('length')
    if type(words) is not list or len(words)!=2 or any(type(w) is not str or not 1<=len(w)<=max_length or set(w)-set('01') for w in words):
        raise Refused('word witness shape')
    if words[0] in words[1] or words[1] in words[0]: raise Refused('patterns not reduced')
    if type(n) is not int or not 0<=n<=horizon: raise Refused('witness horizon')
    if any(type(certificate.get(key)) is not int for key in ('actual_count','shortcut_count')):
        raise Refused('inexact count')
    # Separate overlap traversal, by prefix/suffix strings rather than producer indices.
    columns=[]
    for target in words:
        poly={}
        for source in words:
            for prefix in (target[:k] for k in range(1,len(target))):
                budget.use()
                if len(prefix)<len(source) and source.endswith(prefix):
                    exponent=len(target)-len(prefix); poly[exponent]=poly.get(exponent,0)+1
        columns.append(poly)
    if columns[0]!=columns[1]: raise Refused('column premise false')
    # Build coefficients independently from (1-2x)(1+beta)+sum x^length.
    num={0:1,**columns[0]}; den=dict(num)
    for power,c in num.items(): den[power+1]=den.get(power+1,0)-2*c; budget.use(2)
    for word in words: den[len(word)]=den.get(len(word),0)+1; budget.use()
    predicted=[1]
    for degree in range(1,n+1):
        value=num.get(degree,0)
        for power,c in den.items():
            if 0<power<=degree: value-=c*predicted[degree-power]; budget.use(2)
        predicted.append(value)
    # Count the actual original strings by integer decoding, separate from producer product().
    actual=0
    for integer in range(1<<n):
        text=format(integer,f'0{n}b') if n else ''
        budget.use(len(words)*max(1,n))
        actual+=not any(word in text for word in words)
    if actual!=certificate['actual_count'] or predicted[n]!=certificate['shortcut_count']:
        raise Refused('witness count mismatch')
    if actual==predicted[n]: raise Refused('no counterexample')
    return {'original_count':actual,'shortcut_count':predicted[n],'column_polynomial':columns[0]}


def discover(task,state_path=None,limit=10_000_000):
    start=time.perf_counter_ns(); budget=Budget(limit); tested=0
    trace=[{'direction':'N','operation':'test_stated_structural_generalization'},
           {'direction':'S','operation':'bind_reduced_binary_words_and_column_premise'}]
    try:
        length,horizon,identity=bind_discovery(task); state=read_state(state_path)
        prior=next((o.get('certificate') for o in state['observations'] if o['task_id']==identity and o.get('certificate')),None)
        if prior:
            try:
                checked=check_discovery(task,prior,budget)
                trace.append({'operation':'recheck_stored_original_word_witness','accepted':True})
                return {'status':'CHECKED_COUNTEREXAMPLE','task_id':identity,'certificate':prior,'check':checked,
                    'pairs_tested':0,'reused_after_fresh_check':True,'work':budget.work,'trace':trace,
                    'elapsed_ns':time.perf_counter_ns()-start}
            except Refused:
                trace.append({'operation':'reject_stored_observation','accepted':False})
        words=[''.join(w) for size in range(1,length+1) for w in itertools.product('01',repeat=size)]
        for pair in itertools.combinations(words,2):
            budget.use()
            if pair[0] in pair[1] or pair[1] in pair[0]: continue
            tested+=1; A=candidate_overlap(pair,budget)
            columns=[[A[0][j][k]+A[1][j][k] for k in range(len(A[0][j]))] for j in range(2)]
            budget.use(2*len(columns[0]))
            if columns[0]!=columns[1]: continue
            # Equal pattern lengths have a separate algebraic justification; prioritize the unresolved unequal case.
            if len(pair[0])==len(pair[1]): continue
            predicted=shortcut_coefficients(pair,columns[0],horizon,budget)
            for n in range(horizon+1):
                actual=original_count(pair,n,budget)
                if actual==predicted[n]: continue
                certificate={'task_id':identity,'patterns':list(pair),'length':n,
                    'actual_count':actual,'shortcut_count':predicted[n]}
                trace.append({'direction':'W','operation':'candidate_counterexample','pairs_tested':tested})
                before=budget.work; checked=check_discovery(task,certificate,budget)
                checking_work=budget.work-before
                retain(state,state_path,{'task_id':identity,'kind':'refuted_conjecture','certificate':certificate})
                return {'status':'CHECKED_COUNTEREXAMPLE','task_id':identity,'certificate':certificate,
                    'check':checked,'pairs_tested':tested,'reused_after_fresh_check':False,'work':budget.work,
                    'checking_work':checking_work,'trace':trace,'elapsed_ns':time.perf_counter_ns()-start,
                    'limits':'Bounded search in a fixed binary-word grammar; a refutation of this stated shortcut, not an invention of general mathematics.'}
        return {'status':'UNKNOWN','reason':'no counterexample found in this searched fragment; no universal proof',
            'pairs_tested':tested,'work':budget.work,'trace':trace,'elapsed_ns':time.perf_counter_ns()-start}
    except Exhausted:
        return {'status':'UNKNOWN','reason':'work budget exhausted','pairs_tested':tested,'work':budget.work,
            'trace':trace,'elapsed_ns':time.perf_counter_ns()-start}

def bind(task):
    if type(task) is not dict or task.get('query')!='transition_count': raise Refused('unsupported original query')
    if set(task)-{'query','matrix','initial','terminal','horizon','name','family'}: raise Refused('unsupported matrix fields')
    M,u,v,h=task.get('matrix'),task.get('initial'),task.get('terminal'),task.get('horizon')
    if type(M) is not list or not 1<=len(M)<=256: raise Refused('matrix dimension')
    n=len(M)
    if any(type(r) is not list or len(r)!=n for r in M): raise Refused('matrix shape')
    if type(u) is not list or type(v) is not list or len(u)!=n or len(v)!=n: raise Refused('vector shape')
    if type(h) is not int or not 0<=h<=4096: raise Refused('horizon')
    if any(type(x) is not int or abs(x)>1_000_000 for r in M for x in r): raise Refused('matrix entry')
    if any(type(x) is not int or abs(x)>1_000_000 for x in u+v): raise Refused('vector entry')
    return M,u,v,h,digest({'matrix':M,'initial':u,'terminal':v,'horizon':h,'query':'transition_count'})

def blocks_from(keys):
    groups={}
    for i,key in enumerate(keys): groups.setdefault(key,[]).append(i)
    return list(groups.values())

def propose(M,v,task_id,budget,trace):
    blocks=blocks_from(v)
    trace.append({'direction':'N','operation':'propose_quotient','blocks':len(blocks)})
    while True:
        labels=[0]*len(M)
        for a,block in enumerate(blocks):
            for i in block: labels[i]=a
        signatures=[]
        for i,row in enumerate(M):
            totals=[0]*len(blocks)
            for j,value in enumerate(row):
                budget.use(); totals[labels[j]]+=value
            signatures.append(tuple(totals))
        refined=[]; failures=[]
        for block in blocks:
            buckets={}
            for i in block: buckets.setdefault(signatures[i],[]).append(i)
            if len(buckets)>1:
                first=block[0]; other=next(i for i in block if signatures[i]!=signatures[first])
                column=next(j for j in range(len(blocks)) if signatures[first][j]!=signatures[other][j])
                failures.append({'states':[first,other],'target_block':column,
                                 'sums':[signatures[first][column],signatures[other][column]]})
            refined.extend(buckets.values())
        if not failures:
            Q=[list(signatures[b[0]]) for b in blocks]
            return {'task_id':task_id,'blocks':blocks,'quotient':Q,
                    'terminal':[v[b[0]] for b in blocks],'rule':'MP=PQ;v=Pw'}
        trace.append({'direction':'W','operation':'counterexample_to_current_merge','residuals':failures})
        trace.append({'direction':'S','operation':'refine_failed_blocks','before':len(blocks),'after':len(refined)})
        blocks=refined

def check(task,certificate,budget):
    """Separate finite checker: recomputes equations; no producer signatures used."""
    M,u,v,h,identity=bind(task)
    if type(certificate) is not dict or certificate.get('task_id')!=identity: raise Refused('wrong task binding')
    blocks=certificate.get('blocks'); Q=certificate.get('quotient'); w=certificate.get('terminal')
    if type(blocks) is not list or not blocks or any(type(b) is not list or not b for b in blocks): raise Refused('partition shape')
    flat=[i for b in blocks for i in b]
    if any(type(i) is not int for i in flat) or sorted(flat)!=list(range(len(M))): raise Refused('partition coverage')
    k=len(blocks)
    if type(Q) is not list or len(Q)!=k or any(type(r) is not list or len(r)!=k for r in Q): raise Refused('quotient shape')
    if type(w) is not list or len(w)!=k: raise Refused('terminal shape')
    if any(type(x) is not int for r in Q for x in r) or any(type(x) is not int for x in w): raise Refused('inexact certificate')
    for a,block in enumerate(blocks):
        for i in block:
            budget.use()
            if v[i]!=w[a]: raise Refused('v != P w')
            for b,target in enumerate(blocks):
                total=0
                for j in target: budget.use(); total+=M[i][j]
                if total!=Q[a][b]: raise Refused('M P != P Q')
    projected=[]
    for block in blocks:
        projected.append(sum(u[i] for i in block)); budget.use(len(block))
    return projected,Q,w

def evaluate(M,u,v,h,budget):
    edges=[[(j,c) for j,c in enumerate(row) if c] for row in M]
    budget.use(sum(len(r) for r in M))
    row=list(u)
    for _ in range(h):
        following=[0]*len(M)
        for i,value in enumerate(row):
            if value:
                for j,weight in edges[i]:
                    budget.use(2); following[j]+=value*weight
        row=following
    budget.use(2*len(v))
    return sum(a*b for a,b in zip(row,v))

def direct(task,limit=10_000_000):
    budget=Budget(limit); start=time.perf_counter_ns()
    try:
        M,u,v,h,identity=bind(task)
        answer=evaluate(M,u,v,h,budget)
        return {'status':'EXACT_DIRECT','answer':answer,'work':budget.work,
                'elapsed_ns':time.perf_counter_ns()-start,'task_id':identity}
    except Exhausted:
        return {'status':'UNKNOWN','work':budget.work,'elapsed_ns':time.perf_counter_ns()-start}

def solve_quotient(task,state_path=None,limit=10_000_000):
    start=time.perf_counter_ns(); budget=Budget(limit); trace=[]
    try:
        M,u,v,h,identity=bind(task)
        state=read_state(state_path)
        # A one-block success proposes one explicit recipe from a fixed grammar.
        # On transfer the checker, not stored success, decides applicability.
        experience=any(o.get('quotient_states')==1 for o in state['observations'])
        changed=False; checked=None; checking_work=0
        if experience:
            trace.append({'direction':'E','operation':'transfer_single_block_recipe',
                          'scope':'original matrix equations must be checked afresh'})
            budget.use(len(v))
            if len(set(v))==1:
                changed=True
                budget.use(len(M[0]))
                certificate={'task_id':identity,'blocks':[list(range(len(M)))],
                             'quotient':[[sum(M[0])]],'terminal':[v[0]],'rule':'MP=PQ;v=Pw'}
                before=budget.work
                try: checked=check(task,certificate,budget)
                except Refused as exc:
                    trace.append({'direction':'W','operation':'transferred_recipe_refused','reason':str(exc)})
                checking_work+=budget.work-before
        if checked is None:
            certificate=propose(M,v,identity,budget,trace)
            before=budget.work
            checked=check(task,certificate,budget)
            checking_work+=budget.work-before
        candidate_work=budget.work-checking_work
        a,Q,w=checked
        trace.append({'direction':'S','operation':'check_original_matrix_equations','accepted':True})
        before=budget.work
        answer=evaluate(Q,a,w,h,budget)
        evaluating_work=budget.work-before
        if state_path is not None:
            observation={'task_id':identity,'family':task.get('family','unspecified'),
                         'compressed':len(Q)<len(M),'original_states':len(M),'quotient_states':len(Q),
                         'policy':'guarded_partition_refinement','work':budget.work}
            retain(state,state_path,observation)
        return {'status':'CHECKED_EXACT','answer':answer,'task_id':identity,
                'work':budget.work,'candidate_work':candidate_work,'checking_work':checking_work,
                'evaluation_work':evaluating_work,'original_states':len(M),'quotient_states':len(Q),
                'certificate':certificate,'trace':trace,'experience_observed':experience,
                'route':'quotient',
                'experience_changes_search':changed,
                'elapsed_ns':time.perf_counter_ns()-start,
                'limits':'Known partition refinement and one experience-triggered recipe from a fixed grammar; no autonomous invention of a new theorem.'}
    except Exhausted:
        return {'status':'UNKNOWN','work':budget.work,'trace':trace,'elapsed_ns':time.perf_counter_ns()-start}


def initial_quotient(M,v,identity,blocks,budget,trace):
    labels=[0]*len(M)
    for a,block in enumerate(blocks):
        for i in block: labels[i]=a
    Q=[]
    for block in blocks:
        reference=None
        for i in block:
            sums=[0]*len(blocks)
            for j,c in enumerate(M[i]): budget.use(); sums[labels[j]]+=c
            if reference is None: reference=sums
            elif reference!=sums:
                trace.append({'direction':'W','operation':'initial_partition_failed',
                    'states':[block[0],i],'reference_sums':reference,'actual_sums':sums})
                return None
        Q.append(reference)
    return {'task_id':identity,'blocks':blocks,'quotient':Q,'terminal':[v[b[0]] for b in blocks],'rule':'MP=PQ;v=Pw'}


def solve_matrix(task,state_path=None,limit=10_000_000,strategy='auto'):
    if strategy=='quotient': return solve_quotient(task,state_path,limit)
    if strategy not in ('auto','direct'): raise Refused('matrix strategy')
    started=time.perf_counter_ns(); budget=Budget(limit); trace=[]
    try:
        M,u,v,h,identity=bind(task); state=read_state(state_path); n=len(M)
        checked=None; certificate=None; checking_work=0; route='direct'
        if strategy=='auto':
            blocks=blocks_from(v); budget.use(n)
            # Fixed scheduling choice; no trained/general efficiency claim.
            if len(blocks)<n and h>1 and limit-budget.work>=3*n*n+2*n:
                edges=sum(c!=0 for row in M for c in row); budget.use(n*n)
                direct_bound=n*n+2*h*edges+2*n
                probe_and_check_bound=2*n*n+2*n
                try_probe=(direct_bound>8*n*n and
                    direct_bound+probe_and_check_bound<=limit-budget.work)
                trace.append({'operation':'fixed_cost_policy','direct_work_upper_bound':direct_bound,
                    'try_initial_partition':try_probe,'fallback_reserved':try_probe})
                if try_probe:
                    trace.append({'direction':'N','operation':'propose_initial_terminal_partition','blocks':len(blocks)})
                    certificate=initial_quotient(M,v,identity,blocks,budget,trace)
                    if certificate is not None:
                        before=budget.work; checked=check(task,certificate,budget)
                        checking_work=budget.work-before; route='quotient'
                        trace.append({'direction':'S','operation':'check_original_matrix_equations','accepted':True})
            if checked is None: trace.append({'operation':'select_direct_exact_iteration'})
        candidate_work=budget.work-checking_work; before=budget.work
        if checked is None: answer=evaluate(M,u,v,h,budget); quotient_states=n
        else:
            a,Q,w=checked; answer=evaluate(Q,a,w,h,budget); quotient_states=len(Q)
        evaluation_work=budget.work-before
        retain(state,state_path,{'task_id':identity,'family':task.get('family','unspecified'),
            'kind':'matrix_observation','policy':strategy,'route':route,'original_states':n,
            'quotient_states':quotient_states,'work':budget.work})
        return {'status':'CHECKED_EXACT' if checked is not None else 'EXACT_DIRECT',
            'answer':answer,'task_id':identity,'route':route,'policy':strategy,'work':budget.work,
            'candidate_work':candidate_work,'checking_work':checking_work,'evaluation_work':evaluation_work,
            'original_states':n,'quotient_states':quotient_states,'certificate':certificate if checked else None,
            'trace':trace,'elapsed_ns':time.perf_counter_ns()-started,
            'limits':'Fixed cost policy. Direct answers come from exact numerical iteration; only quotient transformations have separate equation certificates.'}
    except Exhausted:
        return {'status':'UNKNOWN','work':budget.work,'trace':trace,'elapsed_ns':time.perf_counter_ns()-started}


def solve(task,state_path=None,limit=10_000_000,strategy='auto',guard_policy='residual_first',
          proof_policy='auto',lemma_records=(),invariant_policy='full',invariant_records=(),obligation_steps=4,
          recursive_policy='residual',recursive_steps=4,source_policy='gap_bridge',source_steps=8):
    if type(limit) is not int or limit<0: raise Refused('nonnegative integer work budget required')
    if type(task) is not dict: raise Refused('task object')
    query=task.get('query')
    if source_policy not in ('native_isolated','graph_isolated','fixed_bridge','gap_bridge'):
        raise Refused('source episode policy')
    if type(source_steps) is not int or not 1<=source_steps<=64:
        raise Refused('source steps must be 1..64')
    if query!='source_research_episode' and (source_policy!='gap_bridge' or source_steps!=8):
        raise Refused('source options apply only to source research episodes')
    if recursive_policy not in ('direct','enumerate','residual'):raise Refused('recursive identity search policy')
    if type(recursive_steps) is not int or not 1<=recursive_steps<=64:raise Refused('recursive steps must be 1..64')
    if query!='prove_recursive_identity' and (recursive_policy!='residual' or recursive_steps!=4):
        raise Refused('recursive options apply only to recursive identities')
    if invariant_policy not in ('full','mapped','reuse_first'):raise Refused('invariant search policy')
    if query!='discover_invariant' and invariant_policy!='full':raise Refused('invariant policy applies only to invariant discovery')
    if proof_policy not in ('auto','direct','lemma_first','target_sparse','cancellation_sparse','obligations','localized_first'): raise Refused('polynomial proof policy')
    if type(obligation_steps) is not int or not 1<=obligation_steps<=64:raise Refused('obligation steps must be 1..64')
    if proof_policy!='obligations' and obligation_steps!=4:raise Refused('obligation steps apply only to obligations policy')
    if query!='polynomial_consequence' and proof_policy!='auto': raise Refused('proof policy applies only to polynomial consequences')
    if type(lemma_records) not in (list,tuple) or len(lemma_records)>8: raise Refused('at most eight lemma observations')
    if type(invariant_records) not in (list,tuple) or len(invariant_records)>8: raise Refused('at most eight invariant observations')
    if invariant_records and query!='discover_invariant':raise Refused('invariant observations apply only to invariant discovery')
    if query=='transition_count': return solve_matrix(task,state_path,limit,strategy)
    if strategy!='auto': raise Refused('matrix strategy supplied for another query')
    if query in ('apex_research','prove_orbit_exclusion'):
        # The apex chooses subreasoner policies itself; caller policy flags stay default.
        if lemma_records or guard_policy!='residual_first':raise Refused('apex queries accept only original tasks')
        names=('Refused','Exhausted','Budget','STATE_LIMIT','bind','bind_discovery','local_module','read_state',
               'retain','canonical','digest','check','check_discovery','propose','solve','lemma_candidates',
               'remember_lemma','invariant_candidates','remember_invariant')
        host=SimpleNamespace(**{name:globals()[name] for name in names})
        apex=local_module('apex')
        return apex.run(task,state_path,limit,host) if query=='apex_research' else apex.solve_orbit(task,state_path,limit,host)
    if query=='source_research_episode':
        if lemma_records or invariant_records:
            raise Refused('source episodes accept original source questions, not supplied proof observations')
        if guard_policy!='residual_first':raise Refused('guard policy supplied for a source episode')
        names=('Refused','Exhausted','Budget','STATE_LIMIT','VERSION','canonical','digest','local_module','read_state')
        host=SimpleNamespace(**{name:globals()[name] for name in names})
        result=local_module('source_episode').run(task,state_path,limit,host,policy=source_policy,steps=source_steps)
        if type(result) is not dict or result.get('status') not in ('CHECKED_SOURCE_EPISODE','UNKNOWN'):
            raise Refused('source episode returned an unsupported result status')
        return result
    if query=='test_overlap_shortcut': return discover(task,state_path,limit)
    if query=='research_campaign':
        names=('Refused','Exhausted','Budget','STATE_LIMIT','bind','bind_discovery','local_module',
               'read_state','canonical','digest','check','check_discovery','solve','lemma_candidates','remember_lemma',
               'invariant_candidates','remember_invariant')
        host=SimpleNamespace(**{name:globals()[name] for name in names})
        return local_module('campaign').run(task,state_path,limit,host)
    if query=='prove_recursive_identity':
        if lemma_records:raise Refused('recursive invention starts without supplied polynomial records')
        started=time.perf_counter_ns();budget=Budget(limit)
        checker=local_module('recursive_check');engine=local_module('recursive')
        try:
            identity=checker.bind(task,budget)['identity'];state=read_state(state_path)
            previous=next((o for o in state['observations'] if o['task_id']==identity),None)
            result=None
            kinds={'recursive_identity':'CHECKED_RECURSIVE_IDENTITY',
                   'recursive_counterexample':'CHECKED_RECURSIVE_COUNTEREXAMPLE'}
            if previous and type(previous.get('certificate')) is dict:
                try:
                    certificate=previous['certificate'];checked=checker.check(task,certificate,budget)
                    result=dict(status=kinds[checked['kind']],certificate=certificate,check=checked,
                                reused_after_fresh_check=True)
                except checker.Invalid:pass
            if result is None:
                names=('Refused','Exhausted','Budget','STATE_LIMIT','canonical','digest','local_module','solve')
                host=SimpleNamespace(**{name:globals()[name] for name in names})
                result=engine.run(task,state,state_path,budget,host,policy=recursive_policy,steps=recursive_steps)
                if result['status']!='UNKNOWN':
                    checked=checker.check(task,result.get('certificate'),budget)
                    if result['status']!=kinds[checked['kind']]:raise Refused('recursive evidence/status mismatch')
                    result['check']=checked
            if result['status'] in kinds.values():
                retain(state,state_path,dict(task_id=identity,kind=query,status=result['status'],task=task,
                                            certificate=result['certificate']))
            result.update(task_id=identity,work=budget.work,elapsed_ns=time.perf_counter_ns()-started,
                          policy=recursive_policy)
            return result
        except (Exhausted,checker.Limit) as exc:
            return dict(status='UNKNOWN',reason=str(exc),work=budget.work,elapsed_ns=time.perf_counter_ns()-started)
    if query=='discover_invariant':
        started=time.perf_counter_ns();budget=Budget(limit)
        checker=local_module('invariant_check');engine=local_module('invariant')
        try:
            identity=checker.bind(task)['identity'];state=read_state(state_path)
            previous=next((o for o in state['observations'] if o['task_id']==identity),None)
            result=None
            if previous and type(previous.get('certificate')) is dict:
                try:
                    cert=previous['certificate'];checked=checker.check(task,cert,budget)
                    result=dict(status='CHECKED_INVARIANT',certificate=cert,check=checked,reused_after_fresh_check=True)
                except checker.Invalid:pass
            if result is None:
                if invariant_policy=='reuse_first':
                    candidates=(invariant_candidates(state)+list(invariant_records))[:8]
                    result=engine.run_reuse(task,budget,checker,local_module('algebra'),candidates)
                else:
                    result=engine.run(task,budget,checker,local_module('algebra'),policy=invariant_policy,
                        mapper=local_module('invariant_map') if invariant_policy=='mapped' else None)
            if result['status']=='CHECKED_INVARIANT':
                observation=dict(task_id=identity,kind=query,status=result['status'],task=task,certificate=result['certificate'])
                if 'dependency_map' in result:
                    observation['dependency_map']=result['dependency_map']
                    observation['map_status']='PROPOSAL_DATA_NOT_ADMISSION_EVIDENCE'
                elif result.get('reused_after_fresh_check') and previous.get('dependency_map'):
                    observation['dependency_map']=previous['dependency_map']
                    observation['map_status']='STORED_PROPOSAL_NOT_REPLAYED'
                retain(state,state_path,observation)
            result.update(task_id=identity,work=budget.work,elapsed_ns=time.perf_counter_ns()-started,policy=invariant_policy)
            return result
        except (Exhausted,checker.Limit) as exc:
            failed=dict(status='UNKNOWN',reason=str(exc),work=budget.work,elapsed_ns=time.perf_counter_ns()-started)
            if hasattr(exc,'law_reuse'):failed['law_reuse']=exc.law_reuse
            return failed
    if query in ('discover_recurrence','discover_word_recurrence'):
        started=time.perf_counter_ns();budget=Budget(limit)
        checker=local_module('recurrence_check');engine=local_module('recurrence')
        try:
            identity=checker.bind(task)['identity'];state=read_state(state_path)
            previous=next((o for o in state['observations'] if o['task_id']==identity),None)
            result=None
            if previous and type(previous.get('certificate')) is dict:
                try:
                    cert=previous['certificate'];checked=checker.check(task,cert,budget)
                    result=dict(status='CHECKED_RECURRENCE',certificate=cert,check=checked,reused_after_fresh_check=True)
                except checker.Invalid:pass
            if result is None:result=engine.run(task,budget,checker)
            if result['status']=='CHECKED_RECURRENCE':
                retain(state,state_path,dict(task_id=identity,kind=query,status=result['status'],certificate=result['certificate']))
            result.update(task_id=identity,work=budget.work,elapsed_ns=time.perf_counter_ns()-started)
            return result
        except (Exhausted,checker.Limit) as exc:
            return dict(status='UNKNOWN',reason=str(exc),work=budget.work,elapsed_ns=time.perf_counter_ns()-started)
    if query=='word_avoidance_identity':
        started=time.perf_counter_ns(); budget=Budget(limit)
        checker=local_module('word_check'); engine=local_module('word_series')
        try:
            identity=checker.bind(task)['identity']; state=read_state(state_path)
            previous=next((o for o in state['observations'] if o['task_id']==identity),None)
            result=None
            if previous and type(previous.get('certificate')) is dict:
                cert=previous['certificate']
                try:
                    checked=checker.check(task,cert,budget)
                    result={'status':'CHECKED_WORD_IDENTITY' if cert['kind']=='word_series_identity' else 'CHECKED_WORD_COUNTEREXAMPLE',
                        'certificate':cert,'check':checked,'reused_after_fresh_check':True}
                except checker.Invalid: pass
            if result is None: result=engine.run(task,budget,checker)
            if result['status'].startswith('CHECKED_'):
                retain(state,state_path,{'task_id':identity,'kind':query,'status':result['status'],
                    'certificate':result['certificate']})
            result.update(task_id=identity,work=budget.work,elapsed_ns=time.perf_counter_ns()-started)
            return result
        except (Exhausted,checker.Limit) as exc:
            return {'status':'UNKNOWN','reason':str(exc),'work':budget.work,'elapsed_ns':time.perf_counter_ns()-started}
    if query not in ('polynomial_consequence','discover_guards'): raise Refused('unsupported original query')
    started=time.perf_counter_ns(); budget=Budget(limit)
    try:
        checker=local_module('algebra_check'); engine=local_module('algebra')
        identity=checker.bind(task)['identity']; state=read_state(state_path)
        previous=next((o for o in state['observations'] if o['task_id']==identity),None)
        flat_candidates=(lemma_candidates(state)+list(lemma_records))[:8]
        candidates=((lemma_candidates(state,include_guarded=True)+list(lemma_records))[:8]
                    if proof_policy in ('lemma_first','obligations') else flat_candidates)
        if proof_policy=='obligations':
            names=('Refused','Exhausted','Budget','STATE_LIMIT','canonical','digest','local_module','solve')
            host=SimpleNamespace(**{name:globals()[name] for name in names})
            result=local_module('obligations').run(task,state,state_path,budget,host,candidates,obligation_steps,
                                                  leaf_records=flat_candidates)
        else:
            result=engine.run(task,budget,checker,guard_policy,previous,
                              lemma_records=candidates,proof_policy=proof_policy)
        if result['status'].startswith('CHECKED_'):
            observation={'task_id':identity,'kind':query,'status':result['status']}
            if 'certificate' in result: observation['certificate']=result['certificate']
            if result['status']=='CHECKED_IMPLICATION': observation['task']=task
            if 'accepted' in result: observation['guards']=[a['guard'] for a in result['accepted']]
            retain(state,state_path,observation)
        result.update(task_id=identity,work=budget.work,elapsed_ns=time.perf_counter_ns()-started)
        return result
    except (Exhausted,checker.Limit) as exc:
        failed={'status':'UNKNOWN','reason':str(exc),'work':budget.work,'elapsed_ns':time.perf_counter_ns()-started}
        if hasattr(exc,'localization'):failed['localization']=exc.localization
        return failed

def capabilities():
    return {'status':'CAPABILITIES','api_version':'ember.task.v1','runtime_version':VERSION,
        'queries':['transition_count','test_overlap_shortcut','polynomial_consequence',
                   'discover_guards','word_avoidance_identity','research_campaign','discover_recurrence','discover_word_recurrence','discover_invariant','prove_recursive_identity','source_research_episode',
                   'apex_research','prove_orbit_exclusion'],
        'layers':['direct','apex'],
        'apex':{'faces':['N','W','S','E'],
                'schedule':'per obligation, the face with the fewest attempts; routes inside a face by measured outcome and cost',
                'synthesized_routes':['law_instance','recursive_seeded','orbit_prefix','orbit_transfer','orbit_invariant'],
                'law_certificate_kinds':['law_instance'],
                'orbit_certificate_kinds':['orbit_witness','periodic_orbit','invariant_separation'],
                'pyramid':'python -I -B -X utf8 ember.py --pyramid prints the audited reasoning catalog and synthesis lattice',
                'scope':'Plans over implemented subreasoners and admits only original-task certificates; no unrestricted agenda'},
        'source_episode_policies':['native_isolated','graph_isolated','fixed_bridge','gap_bridge'],
        'source_episode_formats':['pie-problem-v1','ember.recursive_claim.v1'],
        'source_episode_scope':'Bounded inert structured sources; original Nat/List questions, explicit source claims and checked same-definition proof transfer',
        'recursive_identity_policies':['direct','enumerate','residual'],
        'recursive_identity_certificate_kinds':['recursive_identity','recursive_counterexample'],
        'recursive_identity_scope':'Nat and finite List(Nat); original structural recursion and separately checked induction; finite survivors remain unproved',
        'invariant_policies':['full','mapped','reuse_first'],
        'guard_grammars':['pair_equalities','coefficient_slices','assumption_slices'],
        'polynomial_proof_policies':['auto','direct','lemma_first','target_sparse','cancellation_sparse','obligations','localized_first'],
        'polynomial_certificate_kinds':['polynomial_combination','localized_polynomial_combination','rational_counterexample'],
        'campaign_polynomial_localization':'localize_polynomials=true adds an explicit original localized proof attempt',
        'polynomial_guarded_transfer':'lemma_first and obligations preserve all mapped original guards; premise children require flat certificates',
        'campaign_guarded_transfer':'reuse_guarded_polynomials=true adds an original lemma_first route with guarded source candidates',
        'campaign_discovery':'discover_after_solving optionally derives recurrence questions from settled transition-count and word-identity originals',
        'limits':{'json_input_bytes':STATE_LIMIT,'state_bytes':STATE_LIMIT,'observations':128,
                  'campaign_problems':16,'campaign_attempts_per_call':64,'lemma_candidates':8,
                  'recurrence_dimension':64,'recurrence_arithmetic_bits':8192,
                  'invariant_variables':6,'invariant_degree':3,'invariant_grid_points':50000,
                  'invariant_source_candidates':8,'invariant_renamings_per_source':16,
                  'obligation_nodes':64,'obligation_edges':128,'obligation_steps_per_call':64,
                  'recursive_functions':16,'recursive_lemmas':16,'recursive_episode_nodes':64,
                  'recursive_episode_edges':128,'recursive_steps_per_call':64,
                  'source_records':8,'source_record_bytes':65536,'source_total_bytes':524288,
                  'source_distinct_roots':4,'source_seed_entries':8,'source_steps_per_call':64,
                  'apex_problems':16,'apex_attempts_per_call':64,'law_carrier_states':64,
                  'orbit_steps':1024,'orbit_transfer_records':8,'output_integer_digits':INT_DIGITS},
        'exit_codes':{'0':'closed result or capabilities','2':'refused input','3':'UNKNOWN'},
        'state':'one writer per state file; resume requires the same explicit state path',
        'standing':'EXPERIMENTAL_SELF_ISOLATED','runtime_dependencies':'Python standard library',
        'work_budget':'charged operations, not an OS time or memory limit'}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('task',type=Path,nargs='?')
    parser.add_argument('--capabilities',action='store_true')
    parser.add_argument('--state',type=Path)
    parser.add_argument('--work',type=int,default=10_000_000)
    parser.add_argument('--strategy',choices=['auto','direct','quotient'],default='auto')
    parser.add_argument('--guard-policy',choices=['residual_first','enumerate_all'],default='residual_first')
    parser.add_argument('--proof-policy',choices=['auto','direct','lemma_first','target_sparse','cancellation_sparse','obligations','localized_first'],default='auto')
    parser.add_argument('--obligation-steps',type=int,default=4)
    parser.add_argument('--invariant-policy',choices=['full','mapped','reuse_first'],default='full')
    parser.add_argument('--recursive-policy',choices=['direct','enumerate','residual'],default='residual')
    parser.add_argument('--recursive-steps',type=int,default=4)
    parser.add_argument('--source-policy',choices=['native_isolated','graph_isolated','fixed_bridge','gap_bridge'],default='gap_bridge')
    parser.add_argument('--source-steps',type=int,default=8)
    parser.add_argument('--layer',choices=['direct','apex'],default='direct')
    parser.add_argument('--pyramid',action='store_true')
    args=parser.parse_args()
    if hasattr(sys,'set_int_max_str_digits'): sys.set_int_max_str_digits(INT_DIGITS)
    if args.capabilities:
        print(json.dumps(capabilities(),indent=2)); return 0
    if args.pyramid:
        mapped=local_module('pyramid').report(Path(__file__).resolve().parent)
        print(json.dumps(mapped,indent=2)); return 0 if mapped['audit']['ok'] else 2
    if args.task is None: parser.error('a task file, --capabilities or --pyramid is required')
    try:
        task=load_json(args.task)
        if args.layer=='apex' and not (type(task) is dict and task.get('query')=='apex_research'):
            # The higher layer receives the original unchanged as its only obligation.
            task={'query':'apex_research','problems':[task]}
        result=solve(task,args.state,args.work,args.strategy,args.guard_policy,args.proof_policy,invariant_policy=args.invariant_policy,obligation_steps=args.obligation_steps,recursive_policy=args.recursive_policy,recursive_steps=args.recursive_steps,source_policy=args.source_policy,source_steps=args.source_steps)
    except (Refused,ValueError,KeyError,TypeError) as e:
        result={'status':'REFUSED','reason':str(e)}
    print(json.dumps(result,indent=2))
    return 3 if result['status']=='UNKNOWN' else 2 if result['status']=='REFUSED' else 0

if __name__=='__main__': raise SystemExit(main())
