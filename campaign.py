"""Durable offline research over typed tasks. Scheduling never admits an answer."""
import copy
from fractions import Fraction
import hashlib
from pathlib import Path
import time

QUERIES={'transition_count','test_overlap_shortcut','polynomial_consequence','discover_guards','word_avoidance_identity','discover_recurrence','discover_word_recurrence','discover_invariant','prove_recursive_identity'}


def generation():
    root=Path(__file__).resolve().parent
    return hashlib.sha256(b''.join((root/name).read_bytes() for name in
        ('ember.py','algebra.py','algebra_check.py','word_series.py','word_check.py','campaign.py','recurrence.py','recurrence_check.py','invariant.py','invariant_check.py','invariant_map.py','recursive.py','recursive_check.py'))).hexdigest()


def validate(problem,host,budget=None):
    """Bind one supported original with its own query binder; shared by higher layers."""
    query=problem['query']
    if query=='transition_count': host.bind(problem)
    elif query=='test_overlap_shortcut': host.bind_discovery(problem)
    elif query=='word_avoidance_identity': host.local_module('word_check').bind(problem)
    elif query in ('discover_recurrence','discover_word_recurrence'): host.local_module('recurrence_check').bind(problem)
    elif query=='discover_invariant':host.local_module('invariant_check').bind(problem)
    elif query=='prove_recursive_identity':host.local_module('recursive_check').bind(problem,budget)
    else: host.local_module('algebra_check').bind(problem)


def binding(task,host,budget=None):
    allowed={'query','problems','attempt_work','max_attempts','policy','name','discover_after_solving','reuse_invariants','localize_polynomials','reuse_guarded_polynomials'}
    if type(task) is not dict or set(task)-allowed or task.get('query')!='research_campaign':
        raise host.Refused('campaign task fields')
    problems=task.get('problems'); per=task.get('attempt_work',1_000_000)
    steps=task.get('max_attempts',64); policy=task.get('policy','structure_first')
    generalize=task.get('discover_after_solving',False)
    if type(generalize) is not bool:raise host.Refused('discover_after_solving must be Boolean')
    reuse_invariants=task.get('reuse_invariants',False)
    if type(reuse_invariants) is not bool:raise host.Refused('reuse_invariants must be Boolean')
    localize=task.get('localize_polynomials',False)
    if type(localize) is not bool:raise host.Refused('localize_polynomials must be Boolean')
    guarded_reuse=task.get('reuse_guarded_polynomials',False)
    if type(guarded_reuse) is not bool:raise host.Refused('reuse_guarded_polynomials must be Boolean')
    if type(problems) is not list or not 1<=len(problems)<=16: raise host.Refused('campaign problem count 1..16')
    if type(per) is not int or not 1<=per<=10_000_000: raise host.Refused('campaign attempt work bound')
    if type(steps) is not int or not 1<=steps<=64: raise host.Refused('campaign per-call attempts 1..64')
    if policy not in ('fixed','structure_first','learned'): raise host.Refused('campaign scheduling policy')
    for problem in problems:
        if type(problem) is not dict or problem.get('query') not in QUERIES: raise host.Refused('supported original campaign task required')
        validate(problem,host,budget)
    original={'query':'research_campaign','problems':problems,'attempt_work':per,'policy':policy}
    if generalize:original['discover_after_solving']=True
    if reuse_invariants:original['reuse_invariants']=True
    if localize:original['localize_polynomials']=True
    if guarded_reuse:original['reuse_guarded_polynomials']=True
    return problems,per,steps,policy,host.digest(original)


def context(problem,host):
    query=problem['query']; shape={'query':query}
    if query=='transition_count':
        shape.update(size=len(problem['matrix']),horizon_bits=problem['horizon'].bit_length())
    elif query in ('polynomial_consequence','discover_guards'):
        shape.update(variables=len(problem['variables']),equations=len(problem.get('assumptions',[])),
                     nonzero=len(problem.get('nonzero',[])),degree=problem.get('multiplier_degree',2))
    elif query=='word_avoidance_identity': shape['lengths']=[len(w) for w in problem['patterns']]
    elif query=='discover_recurrence': shape.update(dimension=len(problem['matrix']),order=problem.get('max_order',min(len(problem['matrix']),16)))
    elif query=='discover_word_recurrence':shape['lengths']=[len(w) for w in problem['patterns']]
    elif query=='discover_invariant':shape.update(variables=len(problem['variables']),degree=problem.get('max_degree',2),focus=len(problem.get('focus',problem['variables'])))
    elif query=='prove_recursive_identity':shape.update(functions=len(problem['definitions']),domain=problem['domain'])
    else: shape['pattern_bound']=problem['max_pattern_length']
    return host.digest(shape)


def routes(problem,index,host,generalize=False,reuse_invariants=False,localize=False,guarded_reuse=False):
    q=problem['query']; result=[]
    def add(strategy,receiving,role='original',options=None):
        result.append({'id':host.digest({'original':problem,'strategy':strategy,'receiving':receiving}),
                       'problem':index,'strategy':strategy,'task':receiving,'role':role,
                       'options':options or {},'context':context(problem,host)})
    if q=='transition_count':
        for strategy in ('auto','direct','quotient'): add(strategy,problem,options={'strategy':strategy})
    elif q=='prove_recursive_identity':
        for policy in ('direct','residual','enumerate'):
            add('recursive_'+policy,problem,options={'recursive_policy':policy})
    elif q=='discover_invariant':
        if reuse_invariants:add('invariant_reuse_first',problem,options={'invariant_policy':'reuse_first'})
        for policy in ('full','mapped'):add('invariant_'+policy,problem,options={'invariant_policy':policy})
        for degree in range(problem.get('max_degree',2)+1,4):
            add('invariant_degree_'+str(degree),{**problem,'max_degree':degree},'expansion',{'invariant_policy':'mapped'})
    elif q in ('polynomial_consequence','discover_guards'):
        if q=='polynomial_consequence':
            if guarded_reuse:add('guarded_lemma_first',problem,options={'proof_policy':'lemma_first'})
            if localize:add('localized_implication',problem,options={'proof_policy':'localized_first'})
            add('original_implication',problem)
        grammars=['pair_equalities','coefficient_slices','assumption_slices']
        chosen=problem.get('guard_grammar','pair_equalities')
        if q=='discover_guards': grammars.remove(chosen); grammars.insert(0,chosen)
        for grammar in grammars:
            receiving={**problem,'query':'discover_guards','guard_grammar':grammar}
            # Seven original equations leave the existing guard slot available.
            role='repair' if q=='polynomial_consequence' else 'original' if grammar==chosen else 'expansion'
            if len(receiving.get('assumptions',[]))<=7: add(grammar,receiving,role)
    else:
        add('original',problem)
        if q=='word_avoidance_identity' and problem['formula']=='column_shortcut':
            add('full_formula_repair',{**problem,'formula':'full_overlap'},'repair')
    if generalize:
        if q=='transition_count' and len(problem['matrix'])<=64:
            add('discover_recurrence',{'query':'discover_recurrence','domain':'QQ',
                'matrix':problem['matrix'],'initial':problem['initial'],'terminal':problem['terminal']},'generalization')
        elif q=='word_avoidance_identity':
            add('discover_word_recurrence',{'query':'discover_word_recurrence','patterns':problem['patterns']},'generalization')
    return result


def compact(result):
    out={k:copy.deepcopy(result[k]) for k in ('status','answer','certificate','reason') if k in result}
    if 'accepted' in result:
        out['accepted']=[{k:copy.deepcopy(a[k]) for k in ('guard','task','certificate')} for a in result['accepted']]
    if type(result.get('law_reuse')) is dict:
        out['law_reuse']={k:copy.deepcopy(result['law_reuse'][k]) for k in
            ('used','fallback','work','fallback_work','accepted_source_task_id','accepted_binding','cap_exhausted')
            if k in result['law_reuse']}
    # Candidate status counts are diagnostics; no unsupported exclusion is reused.
    return out


def polynomial_candidates(route,state,host):
    """Use exactly the candidate window fingerprinted for this route's policy."""
    if route['options'].get('proof_policy')=='lemma_first':
        return host.lemma_candidates(state,include_guarded=True)
    return host.lemma_candidates(state)


def proposal_context(route,state,host):
    """Bind a heuristic miss to the actual ordered candidate library it saw.

    This fingerprint only decides whether to retry. No stored source status,
    count, digest or obstruction can establish a receiving theorem.
    """
    if route['task']['query']=='prove_recursive_identity':
        return host.local_module('recursive').progress_context(route['task'],state,host,
            policy=route['options'].get('recursive_policy','residual'))
    if route['task']['query']=='polynomial_consequence':
        records=polynomial_candidates(route,state,host)
    elif (route['task']['query']=='discover_invariant'
          and route['options'].get('invariant_policy')=='reuse_first'):
        records=host.invariant_candidates(state)
    else:return None
    return host.digest([dict(task=o['task'],certificate=o['certificate']) for o in records])


def admit(task,result,budget,host):
    """Replay only mathematical evidence; never trust saved status/check flags."""
    if type(result) is not dict or type(result.get('status')) is not str: raise host.Refused('campaign result shape')
    q=task['query']; status=result['status']
    if status=='UNKNOWN': return False
    if q=='transition_count':
        if status not in ('EXACT_DIRECT','CHECKED_EXACT') or type(result.get('answer')) is not int:
            raise host.Refused('matrix campaign evidence')
        M,u,v,h,_=host.bind(task)
        if status=='CHECKED_EXACT':
            u,M,v=host.check(task,result.get('certificate'),budget)
        vector=list(v)
        for _ in range(h):
            nxt=[]
            for row in M:
                total=0
                for a,b in zip(row,vector): budget.use(2); total+=a*b
                nxt.append(total)
            vector=nxt
        total=0
        for a,b in zip(u,vector): budget.use(2); total+=a*b
        if total!=result['answer']: raise host.Refused('original matrix answer differs')
        return True
    if q=='test_overlap_shortcut':
        if status!='CHECKED_COUNTEREXAMPLE': raise host.Refused('word-discovery result status')
        host.check_discovery(task,result.get('certificate'),budget); return True
    if q=='word_avoidance_identity':
        c=host.local_module('word_check'); cert=result.get('certificate')
        checked=c.check(task,cert,budget)
        expected='CHECKED_WORD_IDENTITY' if cert['kind']=='word_series_identity' else 'CHECKED_WORD_COUNTEREXAMPLE'
        if status!=expected: raise host.Refused('word evidence/status mismatch')
        return checked['ok']
    if q in ('discover_recurrence','discover_word_recurrence'):
        if status!='CHECKED_RECURRENCE':raise host.Refused('recurrence evidence/status mismatch')
        return host.local_module('recurrence_check').check(task,result.get('certificate'),budget)['ok']
    if q=='discover_invariant':
        if status!='CHECKED_INVARIANT':raise host.Refused('invariant evidence/status mismatch')
        return host.local_module('invariant_check').check(task,result.get('certificate'),budget)['ok']
    if q=='prove_recursive_identity':
        checked=host.local_module('recursive_check').check(task,result.get('certificate'),budget)
        expected={'recursive_identity':'CHECKED_RECURSIVE_IDENTITY',
                  'recursive_counterexample':'CHECKED_RECURSIVE_COUNTEREXAMPLE'}[checked['kind']]
        if status!=expected:raise host.Refused('recursive evidence/status mismatch')
        return checked['ok']
    c=host.local_module('algebra_check')
    if q=='polynomial_consequence':
        cert=result.get('certificate'); checked=c.check(task,cert,budget)
        expected=c.result_status(checked)
        if status!=expected: raise host.Refused('algebra evidence/status mismatch')
        return checked['ok']
    if status!='CHECKED_GUARDS' or type(result.get('accepted')) is not list or not result['accepted']:
        raise host.Refused('guard campaign evidence')
    if len(result['accepted'])>79: raise host.Refused('guard result bound')
    for item in result['accepted']:
        if type(item) is not dict or type(item.get('guard')) is not str: raise host.Refused('guard record')
        receiving={**task,'query':'polynomial_consequence','assumptions':list(task.get('assumptions',[]))+[item['guard']]}
        receiving.pop('guard_grammar',None)
        # Reconstruct from original task; saved receiving-task bytes are not authority.
        if c.bind(item.get('task'))['identity']!=c.bind(receiving)['identity']:
            raise host.Refused('changed guard receiving assumptions')
        checked=c.check(receiving,item.get('certificate'),budget)
        if not checked.get('support_checked'): raise host.Refused('guard requires admissible support')
    return True


def samples_read(state,host):
    samples=state.get('scheduler_samples',[])
    if type(samples) is not list or len(samples)>128: raise host.Refused('scheduler sample bound')
    required={'context','strategy','task_id','generation','success','elapsed_ns'}
    seen=set()
    for sample in samples:
        if type(sample) is not dict or set(sample)!=required: raise host.Refused('scheduler sample shape')
        if any(type(sample[k]) is not str or len(sample[k])>100 for k in ('context','strategy','task_id','generation')):
            raise host.Refused('scheduler sample identity')
        if type(sample['success']) is not bool or type(sample['elapsed_ns']) is not int or not 0<=sample['elapsed_ns']<=10**15:
            raise host.Refused('scheduler sample value')
        key=tuple(sample[k] for k in ('context','strategy','task_id','generation'))
        if key in seen: raise host.Refused('duplicate scheduler observation')
        seen.add(key)
    return samples


def score(samples,route,gen):
    rows=[s for s in samples if s['context']==route['context'] and s['strategy']==route['strategy'] and s['generation']==gen]
    success=sum(s['success'] for s in rows); count=len(rows)
    p=Fraction(1+success,2+count)
    mean=(Fraction(1,100)+Fraction(sum(s['elapsed_ns'] for s in rows),10**9))/(1+count)
    return p/max(mean,Fraction(1,10**6))


def record_sample(state,route,original,gen,success,elapsed,host):
    row={'context':route['context'],'strategy':route['strategy'],'task_id':host.digest(original),
         'generation':gen,'success':bool(success),'elapsed_ns':elapsed}
    key=lambda s:(s['context'],s['strategy'],s['task_id'],s['generation'])
    samples=samples_read(state,host)
    state['scheduler_samples']=[s for s in samples if key(s)!=key(row)]+[row]
    state['scheduler_samples']=state['scheduler_samples'][-128:]


def checkpoint(state,path,record,host):
    if path is None: return
    # Leave space for the mandatory active checkpoint; evict other observations,
    # never this record. Oversized evidence remains unresolved instead of vanishing.
    others=[o for o in state['observations'] if o['task_id']!=record['task_id']]
    state['observations']=(others+[record])[-128:]
    while len(host.canonical(state).encode())+1>host.STATE_LIMIT and len(state['observations'])>1:
        state['observations'].pop(0)
    if len(host.canonical(state).encode())+1>host.STATE_LIMIT:
        raise host.Refused('active campaign checkpoint exceeds 1 MiB')
    target=Path(path); target.parent.mkdir(parents=True,exist_ok=True)
    temp=target.with_suffix(target.suffix+'.tmp')
    temp.write_text(host.canonical(state)+'\n',encoding='utf-8',newline='\n'); temp.replace(target)


def run(task,state_path,limit,host,layer=None):
    """A layer (the apex) may supply binding, plan, face schedule, synthesized
    execution and admission. Replay, checkpoints and budgets stay here; with no
    layer every campaign decision is unchanged."""
    start=time.perf_counter_ns(); budget=host.Budget(limit)
    try:
        problems,per,steps,policy,identity=(layer.binding if layer else binding)(task,host,budget)
    except (host.Exhausted,host.local_module('recursive_check').Limit) as exc:
        # Charged input validation must return UNKNOWN without touching an
        # existing fuller checkpoint when its allowance ends before binding.
        return dict(status='UNKNOWN',reason=str(exc),work=budget.work,
                    elapsed_ns=time.perf_counter_ns()-start)
    gen=layer.generation() if layer else generation()
    state=host.read_state(state_path); samples=samples_read(state,host)
    if layer: plan=layer.plan(problems,host)
    else:
        plan=[r for i,p in enumerate(problems) for r in routes(p,i,host,task.get('discover_after_solving',False),
              task.get('reuse_invariants',False),task.get('localize_polynomials',False),task.get('reuse_guarded_polynomials',False))]
    byid={r['id']:r for r in plan}
    kind=layer.kind if layer else 'research_campaign'
    old=next((o for o in state['observations'] if o['task_id']==identity and o.get('kind')==kind),None)
    record={'task_id':identity,'kind':kind,'generation':gen,'attempts':[],
            'superseded_attempts':[],'superseded_dropped':0}
    outcomes={}; invalidated=[]; executed=[]; decisions=[]; replay_work=0
    context_invalidated=[]
    errors=(host.Refused,host.local_module('algebra_check').Invalid,host.local_module('word_check').Invalid,
            host.local_module('recurrence_check').Invalid,host.local_module('invariant_check').Invalid,KeyError,TypeError)
    limits=(host.Exhausted,host.local_module('algebra_check').Limit,host.local_module('word_check').Limit,
            host.local_module('recurrence_check').Limit,host.local_module('invariant_check').Limit)
    if any(p['query']=='prove_recursive_identity' for p in problems):
        errors=(*errors,host.local_module('recursive_check').Invalid)
        limits=(*limits,host.local_module('recursive_check').Limit)
    if layer:
        errors=(*errors,*layer.errors); limits=(*limits,*layer.limits)
        admission=lambda route,result:layer.admit(route,result,budget,host)
        context_of=lambda route:layer.proposal_context(route,state,host)
    else:
        admission=lambda route,result:admit(route['task'],result,budget,host)
        context_of=lambda route:proposal_context(route,state,host)
    if old is not None:
        prior=old.get('attempts')
        if type(prior) is not list or len(prior)>64: raise host.Refused('campaign checkpoint attempt shape')
        history=old.get('superseded_attempts',[]);dropped=old.get('superseded_dropped',0)
        if (type(history) is not list or len(history)>64 or any(type(a) is not dict for a in history)
            or type(dropped) is not int or dropped<0):raise host.Refused('campaign superseded history shape')
        record['superseded_attempts']=copy.deepcopy(history);record['superseded_dropped']=dropped
    else: prior=[]
    def supersede(attempt):
        record['superseded_attempts'].append(dict(copy.deepcopy(attempt),superseded_reason='proposal_context_changed'))
        if len(record['superseded_attempts'])>64:
            record['superseded_attempts'].pop(0);record['superseded_dropped']+=1
    try:
        # Rebuild route identities from input. Every saved admission is replayed.
        seen_routes=set()
        for attempt in prior:
            if type(attempt) is not dict or attempt.get('route_id') not in byid:
                raise host.Refused('checkpoint contains an unbound route')
            if attempt['route_id'] in seen_routes: raise host.Refused('duplicate checkpoint route')
            seen_routes.add(attempt['route_id'])
            route=byid[attempt['route_id']]; result=attempt.get('result')
            if type(result) is dict and result.get('status')=='UNKNOWN':
                # No-result records only skip the exact unchanged generation/bounds.
                current_context=context_of(route)
                same_context=(current_context is None or attempt.get('proposal_context')==current_context)
                if old.get('generation')==gen and type(attempt.get('attempt_work_bound')) is int and attempt['attempt_work_bound']>=per and same_context:
                    record['attempts'].append(attempt); outcomes[route['id']]=result
                elif not same_context:context_invalidated.append(route['id']);supersede(attempt)
                continue
            before=budget.work
            try:
                admission(route,result)
                record['attempts'].append(attempt); outcomes[route['id']]=result
            except errors:
                invalidated.append(route['id'])
            replay_work+=budget.work-before
        def terminal(index):
            q=problems[index]['query']; own=[outcomes[r['id']] for r in plan if r['problem']==index and r['role']=='original' and r['id'] in outcomes]
            if q=='polynomial_consequence': return any(o['status']=='CHECKED_IMPLICATION' for o in own)
            if q=='discover_guards': return any(o['status']=='CHECKED_GUARDS' for o in own)
            return any(o['status']!='UNKNOWN' for o in own)
        def ready(route):
            if route['id'] in outcomes: return False
            i=route['problem']; q=problems[i]['query']
            if route['role']=='original': return not terminal(i)
            original=[r for r in plan if r['problem']==i and r['role']=='original']
            if route['role']=='generalization':
                return any(outcomes.get(r['id'],{}).get('status') not in (None,'UNKNOWN') for r in original)
            if not all(r['id'] in outcomes for r in original): return False
            values=[outcomes[r['id']]['status'] for r in original]
            if q=='discover_invariant' and route['role']=='expansion':
                return not any(outcomes.get(r['id'],{}).get('status')=='CHECKED_INVARIANT'
                    for r in plan if r['problem']==i)
            if route['role']=='expansion': return True
            if q=='polynomial_consequence': return 'CHECKED_IMPLICATION' not in values
            return 'CHECKED_WORD_COUNTEREXAMPLE' in values
        for _ in range(steps):
            # A later checked discovery can make an earlier heuristic miss stale.
            # Only knowledge-consuming routes reopen; max_attempts and total work
            # still bound this re-entry. Completed evidence is never invalidated
            # merely because a candidate library changed.
            kept_attempts=[]
            for attempt in record['attempts']:
                route=byid[attempt['route_id']]
                current_context=context_of(route)
                if (attempt['result'].get('status')=='UNKNOWN' and current_context is not None
                    and attempt.get('proposal_context')!=current_context and not terminal(route['problem'])):
                    outcomes.pop(route['id'],None);context_invalidated.append(route['id'])
                    supersede(attempt)
                else:kept_attempts.append(attempt)
            record['attempts']=kept_attempts
            available=[r for r in plan if ready(r)]
            if not available: break
            # Ordered original problems remain fair; score routes within that problem.
            first=min(r['problem'] for r in available); available=[r for r in available if r['problem']==first]
            samples=samples_read(state,host); extra={}
            if layer:
                available,extra=layer.order(available,record,byid,samples,gen,
                                            min(per,max(1,(limit-budget.work)//2)),host)
                reverse=False
            else:
                if policy=='learned': available.sort(key=lambda r:score(samples,r,gen),reverse=True)
                elif policy=='structure_first' and problems[first].get('assumptions'):
                    available.sort(key=lambda r:r['strategy']!='assumption_slices')
                problem_id=host.digest(problems[first])
                own=[r for r in plan if r['problem']==first]
                multiple_originals=sum(r['role']=='original' for r in own)>1
                choice_strategies={r['strategy'] for r in own if multiple_originals or r['role']!='original'}
                # A forced original check must not consume the later exploration choice.
                unseen=not any(s['task_id']==problem_id and s['generation']==gen and s['strategy'] in choice_strategies for s in samples)
                contexts={s['task_id'] for s in samples if s['generation']==gen and s['context']==available[0]['context'] and s['task_id']!=problem_id}
                reverse=policy=='learned' and unseen and (len(contexts)+1)%5==0
                if reverse: available.reverse()
            route=available[0]; remaining=limit-budget.work
            decisions.append({'problem':first,'eligible_order':[r['strategy'] for r in available],
                              'selected':route['strategy'],'exploration_reversed':reverse,**extra})
            if remaining<=0: raise host.Exhausted('campaign work budget exhausted')
            # Reserve some work for independent admission; a miss cannot fabricate success.
            allocation=min(per,max(1,remaining//2)); before=budget.work; began=time.perf_counter_ns()
            options=dict(route['options'])
            attempt_context=context_of(route)
            if route['task']['query']=='polynomial_consequence':
                options['lemma_records']=polynomial_candidates(route,state,host)
            if route['task']['query']=='discover_invariant' and options.get('invariant_policy')=='reuse_first':
                options['invariant_records']=host.invariant_candidates(state)
            if layer and 'synthesis' in route:
                # Synthesized routes compose subreasoners; admission below stays separate.
                result,candidate_state=layer.execute(route,state,allocation,host)
            elif route['task']['query']=='prove_recursive_identity':
                # Work on an isolated in-memory candidate instance. The outer
                # campaign owns the single atomic commit after original replay.
                candidate_state=copy.deepcopy(state)
                child_budget=host.Budget(allocation)
                try:
                    result=host.local_module('recursive').run(route['task'],candidate_state,None,
                        child_budget,host,policy=options.get('recursive_policy','residual'),steps=4)
                except (host.Exhausted,host.local_module('recursive_check').Limit) as exc:
                    result=dict(status='UNKNOWN',reason=str(exc))
                result['work']=child_budget.work
            else:
                candidate_state=None
                result=host.solve(route['task'],None,allocation,**options)
            budget.use(result.get('work',allocation))
            kept=compact(result); success=False
            if result['status']!='UNKNOWN': success=admission(route,kept)
            if candidate_state is not None:
                # UNKNOWN carries provisional progress, never an admission. The
                # producer replays its proofs again on every future invocation.
                state=candidate_state
            if success:
                host.remember_lemma(state,route['task'],kept)
                host.remember_invariant(state,route['task'],kept)
                if route['task']['query']=='discover_guards':
                    for item in kept['accepted']:
                        host.remember_lemma(state,item['task'],
                            {'status':'CHECKED_IMPLICATION','certificate':item['certificate']})
                if layer: layer.remember(state,route,kept,host)
            elapsed=time.perf_counter_ns()-began
            attempt={'route_id':route['id'],'result':kept,'work':budget.work-before,'elapsed_ns':elapsed,
                     'attempt_work_bound':allocation}
            if attempt_context is not None:attempt['proposal_context']=attempt_context
            record['attempts'].append(attempt); outcomes[route['id']]=kept; executed.append(route['strategy'])
            record_sample(state,route,problems[first],gen,success,elapsed,host)
            checkpoint(state,state_path,record,host)
        remaining_routes=[r for r in plan if ready(r)]
        unresolved=any(not any(outcomes.get(r['id'],{}).get('status') not in (None,'UNKNOWN')
                              for r in plan if r['problem']==i and r['role']=='original') for i in range(len(problems)))
        status='UNKNOWN' if remaining_routes or unresolved else 'CHECKED_CAMPAIGN'
        reason='budgeted frontier remains' if remaining_routes else 'route list exhausted with unresolved original obligations' if unresolved else 'original obligations have checked outcomes'
    except limits as exc:
        status='UNKNOWN'; reason=str(exc)
    # Previously completed evidence stays persisted if replay or current admission exhausts.
    # Do not overwrite a full prior checkpoint with a partially replayed record.
    summaries=[]
    for i,problem in enumerate(problems):
        rows=[]
        for route in plan:
            if route['problem']==i and route['id'] in outcomes:
                rows.append({'strategy':route['strategy'],'role':route['role'],'task':route['task'],
                             'result':outcomes[route['id']]})
                if layer: rows[-1].update(face=route['face'],node=route['node'])
        summaries.append({'original_task':problem,'attempts':rows})
    answer={'status':status,'reason':reason,'task_id':identity,'generation':gen,
            'problems':summaries,'executed_routes':executed,'scheduling_decisions':decisions,'invalidated_saved_routes':invalidated,
            'invalidated_proposal_context_routes':context_invalidated,
            'saved_attempt_count':len(record['attempts']),'replay_work':replay_work,'work':budget.work,
            'elapsed_ns':time.perf_counter_ns()-start,'policy':policy,
            'limits':'Finite typed workflow. A checked refutation settles only its original claim; repaired tasks keep their added assumptions. Learning ranks work, not mathematical truth.'}
    if layer: answer.update(layer.report(plan,outcomes,record,byid,executed))
    return answer
