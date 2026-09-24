"""Bounded generic induction, residual conjectures and checked parent reentry.

Definitions and names are input data. No theorem templates, donor execution,
models or unchecked library are used. Search state is never proof authority.
"""
from __future__ import annotations
import copy
import hashlib
import itertools
import json
import re
from pathlib import Path

CAPS=dict(depth=4,candidates=1400,formal_attempts=100,repairs=8,
          normalize_steps=160,equality_nodes=32,side_size=7,variables=3,
          cell_terms=96,term_emissions=6000,nat_bound=2,list_length=2,
          assignments=4096,nodes=64,edges=128,history=128,stage_work=200000,
          lemmas=16,intermediate_nodes=4096)
CONSTRUCTORS={'zero':((), 'Nat'),'succ':(('Nat',),'Nat'),
              'nil':((),'List'),'cons':(('Nat','List'),'List')}


class SearchLimit(RuntimeError):pass


class Slice:
    def __init__(self,parent,limit):self.parent=parent;self.limit=limit;self.work=0
    def use(self,amount=1):
        if self.work+amount>self.limit:raise SearchLimit('stage work limit')
        self.parent.use(amount);self.work+=amount


def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)
def digest(value):return hashlib.sha256(canonical(value).encode()).hexdigest()
def variable(t):return t[0]=='$'
def read(t):return ('$',t['v'],t['sort']) if type(t) is dict else (t[0],*(read(a) for a in t[1:]))
def data(t):return {'v':t[1],'sort':t[2]} if variable(t) else [t[0],*(data(a) for a in t[1:])]
def size(t):
    count=0;pending=[t]
    while pending:
        term=pending.pop();count+=1
        if not variable(term):pending.extend(term[1:])
    return count
def bounded_term(t):
    pending=[(t,0)];count=0
    while pending:
        term,depth=pending.pop();count+=1
        if count>4096 or depth>128:return False
        if not variable(term):pending.extend((a,depth+1) for a in term[1:])
    return True
def vars_of(t):
    out={}
    def walk(a):
        if variable(a):out.setdefault(a[1],a[2])
        else:
            for b in a[1:]:walk(b)
    walk(t);return out
def goal_vars(goal):return {**vars_of(goal[0]),**vars_of(goal[1])}
def goal_data(goal):return dict(lhs=data(goal[0]),rhs=data(goal[1]))
def read_goal(goal):return read(goal['lhs']),read(goal['rhs'])
def subst(t,env,budget):
    budget.use()
    if variable(t):return env.get(t[1],t)
    return (t[0],*(subst(a,env,budget) for a in t[1:]))
def positions(t,path=()):
    yield path,t
    if not variable(t):
        for i,a in enumerate(t[1:]):yield from positions(a,path+(i,))
def replace(t,path,u):
    if not path:return u
    aa=list(t);aa[path[0]+1]=replace(aa[path[0]+1],path[1:],u);return tuple(aa)
def alpha(goal):
    env={name:('$','v'+str(i),sort) for i,(name,sort) in enumerate(goal_vars(goal).items())}
    def walk(t):return env[t[1]] if variable(t) else (t[0],*(walk(a) for a in t[1:]))
    return walk(goal[0]),walk(goal[1])
def goal_id(goal):return digest(goal_data(alpha(goal)))


class Theory:
    def __init__(self,task,budget):
        self.symbols=dict(CONSTRUCTORS);self.rules=[];self.definitions={}
        for declaration in task['definitions']:
            budget.use()
            name=declaration['name'];self.definitions[name]=declaration
            self.symbols[name]=(tuple(declaration['inputs']),declaration['output'])
            for i,equation in enumerate(declaration['equations']):
                lhs,rhs=read_goal(equation)
                self.rules.append(dict(lhs=lhs,rhs=rhs,quantified=set(vars_of(lhs)),
                    source=dict(kind='definition',name=name,case=i)))
        self.precedence={name:i for i,name in enumerate(self.symbols)}
    def sort(self,t):return t[2] if variable(t) else self.symbols[t[0]][1]
    def dependencies(self,goal):
        names={t[0] for side in goal for _,t in positions(side) if not variable(t)}
        pending=list(names)
        while pending:
            name=pending.pop()
            for eq in self.definitions.get(name,{}).get('equations',[]):
                for _,term in positions(read(eq['rhs'])):
                    if not variable(term) and term[0] not in names:
                        names.add(term[0]);pending.append(term[0])
        return set(CONSTRUCTORS)|names


def match(pattern,term,quantified,theory,budget,env=None):
    budget.use();env={} if env is None else env
    if variable(pattern):
        if pattern[1] not in quantified:return env if pattern==term else None
        if theory.sort(term)!=pattern[2]:return None
        if pattern[1] in env:return env if env[pattern[1]]==term else None
        env[pattern[1]]=term;return env
    if variable(term) or pattern[0]!=term[0] or len(pattern)!=len(term):return None
    for a,b in zip(pattern[1:],term[1:]):
        if match(a,b,quantified,theory,budget,env) is None:return None
    return env


def greater(a,b,precedence,budget):
    budget.use()
    if a==b or variable(a):return False
    if any(s==b or greater(s,b,precedence,budget) for s in a[1:]):return True
    if variable(b) or not all(greater(a,t,precedence,budget) for t in b[1:]):return False
    if precedence[a[0]]>precedence[b[0]]:return True
    if a[0]==b[0]:
        for s,t in zip(a[1:],b[1:]):
            if s!=t:return greater(s,t,precedence,budget)
    return False


def rewrite_rules(theory,library,ih,budget):
    rules=list(theory.rules)
    for i,item in enumerate(library):
        a,b=read_goal(item['goal'])
        rules.append(dict(lhs=a,rhs=b,quantified=set(goal_vars((a,b))),source=dict(kind='lemma',index=i)))
    if ih:rules.append(ih)
    normal=[];symmetric=[]
    for rule in rules:
        for direction in (1,-1):
            a,b=(rule['lhs'],rule['rhs']) if direction==1 else (rule['rhs'],rule['lhs'])
            if variable(a) or not rule['quantified'].issubset(vars_of(a)):continue
            entry=(rule,direction,a,b)
            if rule['source']['kind']=='definition':
                if direction==1:normal.append(entry);symmetric.append(entry)
            else:
                symmetric.append(entry)
                if greater(a,b,theory.precedence,budget):normal.append(entry)
    return normal,symmetric


def successors(term,rules,theory,budget,max_size=4096):
    for path,part in reversed(list(positions(term))):
        for rule,direction,a,b in rules:
            if variable(part) or a[0]!=part[0]:continue
            env=match(a,part,rule['quantified'],theory,budget)
            if env is None or set(env)!=rule['quantified']:continue
            target=replace(term,path,subst(b,env,budget));budget.use()
            if target==term or size(target)>max_size or not bounded_term(target):continue
            yield target,dict(source=rule['source'],direction=direction,at=list(path),
                              subst={name:data(value) for name,value in sorted(env.items())})


def join(goal,theory,library,budget,ih=None):
    normal,symmetric=rewrite_rules(theory,library,ih,budget)
    ends=[];traces=[];stops=[]
    for term in goal:
        trace=[];seen={term};stop='NORMAL_FORM'
        for _ in range(CAPS['normalize_steps']):
            hit=next(successors(term,normal,theory,budget),None)
            if hit is None:break
            new,step=hit
            if new in seen:stop='REWRITE_CYCLE';break
            term=new;seen.add(term);trace.append(step)
        else:stop='REWRITE_LIMIT'
        ends.append(term);traces.append(trace);stops.append(stop)
    if ends[0]==ends[1]:return dict(rule='join',left=traces[0],right=traces[1]),None
    queues=[[ends[0]],[ends[1]]];paths=[{ends[0]:[]},{ends[1]:[]}];expanded=0
    limit=min(CAPS['intermediate_nodes'],max(map(size,ends))+5)
    for turn in range(CAPS['equality_nodes']):
        side=turn%2
        if not queues[side]:side=1-side
        if not queues[side]:break
        term=queues[side].pop(0);expanded+=1
        for target,step in successors(term,symmetric,theory,budget,limit):
            if target in paths[side]:continue
            if len(paths[side])>=CAPS['equality_nodes']*4:break
            paths[side][target]=paths[side][term]+[step]
            if target in paths[1-side]:
                return dict(rule='join',left=traces[0]+paths[0][target],right=traces[1]+paths[1][target]),None
            queues[side].append(target)
    return None,dict(goal=goal_data(goal),residual=goal_data(tuple(ends)),
                     left_trace=traces[0],right_trace=traces[1],stop=stops,expanded=expanded)


def attempt(goal,theory,library,budget):
    proof,residual=join(goal,theory,library,budget)
    if proof:return proof,None
    scope=goal_vars(goal);scores={name:0 for name in scope}
    for side in goal:
        for _,term in positions(side):
            if variable(term) or term[0] not in theory.definitions:continue
            arg=term[theory.definitions[term[0]]['recursion']+1]
            if variable(arg) and arg[1] in scores:scores[arg[1]]+=1
    order=sorted(scope,key=lambda name:-scores[name]);blocked=[]
    for name in order:
        cases={};sort=scope[name]
        for ctor,(inputs,output) in CONSTRUCTORS.items():
            if output!=sort:continue
            binders=[];occupied=set(scope)
            for i,kind in enumerate(inputs):
                fresh='e'+str(i)
                while fresh in occupied:fresh='_'+fresh
                occupied.add(fresh);binders.append(('$',fresh,kind))
            branch=tuple(subst(t,{name:(ctor,*binders)},budget) for t in goal)
            recursive=next((v for v in binders if v[2]==sort),None)
            ih=None
            if recursive is not None:
                a,b=(subst(t,{name:recursive},budget) for t in goal)
                ih=dict(lhs=a,rhs=b,quantified=set(scope)-{name},source=dict(kind='ih'))
            child,failed=join(branch,theory,library,budget,ih)
            if child is None:
                failed.update(kind='induction_case',variable=name,constructor=ctor,
                    binders=[data(v) for v in binders],
                    ih=None if ih is None else dict(goal=goal_data((ih['lhs'],ih['rhs'])),quantified=sorted(ih['quantified'])))
                blocked.append(failed);break
            cases[ctor]=dict(binders=[data(v) for v in binders],proof=child)
        else:return dict(rule='induction',variable=name,cases=cases),None
    residual['kind']='direct'
    return None,blocked[0] if blocked else residual


def typed_terms(theory,leaves,names,budget,max_size=7):
    """Finite linear grammar. Constants carry mask zero; each variable occurs once."""
    cells={};allmask=(1<<len(leaves))-1;emitted=0
    for i,t in enumerate(leaves):cells.setdefault((1,theory.sort(t),1<<i),[]).append(t)
    for name,(inputs,output) in theory.symbols.items():
        if name in names and not inputs:cells.setdefault((1,output,0),[]).append((name,))
    functions=[(name,ins,out) for name,(ins,out) in theory.symbols.items() if name in names and 1<=len(ins)<=2]
    for n in range(1,max_size+1):
        if n>1:
            fresh={}
            def put(sort,mask,t):
                bucket=fresh.setdefault((n,sort,mask),[])
                if len(bucket)<CAPS['cell_terms'] and t not in bucket:bucket.append(t)
            for name,inputs,output in functions:
                if len(inputs)==1:
                    for (sz,sort,mask),terms in list(cells.items()):
                        if sz!=n-1 or sort!=inputs[0]:continue
                        for a in terms:budget.use();put(output,mask,(name,a))
                else:
                    for (sa,ta,ma),aa in list(cells.items()):
                        if ta!=inputs[0]:continue
                        for (sb,tb,mb),bb in list(cells.items()):
                            if sa+sb!=n-1 or tb!=inputs[1] or ma&mb:continue
                            key=(n,output,ma|mb)
                            if len(fresh.get(key,()))>=CAPS['cell_terms']:continue
                            for a in aa:
                                for b in bb:
                                    budget.use();put(output,ma|mb,(name,a,b))
                                    if len(fresh.get(key,()))>=CAPS['cell_terms']:break
                                if len(fresh.get(key,()))>=CAPS['cell_terms']:break
            cells.update(fresh)
        for (sz,sort,mask),terms in list(cells.items()):
            if sz==n and mask==allmask:
                for term in terms:
                    emitted+=1
                    if emitted>CAPS['term_emissions']:return
                    budget.use();yield term


def shared(goal,theory):
    left={t for _,t in positions(goal[0]) if not variable(t) and len(t)>1}
    right={t for _,t in positions(goal[1]) if not variable(t) and len(t)>1}
    common=sorted(left&right,key=lambda t:(-size(t),canonical(data(t))))
    mapping={};occupied=set(goal_vars(goal))
    for term in common:
        if any(term in {t for _,t in positions(big)} for big in mapping):continue
        name='a'+str(len(mapping))
        while name in occupied:name='_'+name
        occupied.add(name);mapping[term]=('$',name,theory.sort(term))
    def walk(t):
        if t in mapping:return mapping[t]
        return t if variable(t) else (t[0],*(walk(a) for a in t[1:]))
    return tuple(walk(t) for t in goal) if mapping else None


def patterns(term,theory):
    if variable(term) or len(term)==1:return
    for keep in [-1]+[i for i,a in enumerate(term[1:]) if not variable(a) and len(a)>1]:
        mapping={}
        def atom(t):
            if not variable(t) and len(t)==1:return t
            if t not in mapping:mapping[t]=('$','g'+str(len(mapping)),theory.sort(t))
            return mapping[t]
        aa=[]
        for i,a in enumerate(term[1:]):
            aa.append((a[0],*(atom(b) for b in a[1:])) if i==keep else atom(a))
        yield (term[0],*aa)


def allowed(goal,theory,budget):
    if goal[0]==goal[1] or max(map(size,goal))>CAPS['side_size']:return False
    left,right=vars_of(goal[0]),vars_of(goal[1])
    if not 1<=len(left)<=CAPS['variables'] or left!=right:return False
    for side in goal:
        counts={name:0 for name in left}
        for _,term in positions(side):
            if variable(term):counts[term[1]]+=1
        if any(n!=1 for n in counts.values()):return False
    return theory.sort(goal[0])==theory.sort(goal[1])


def candidates(goal,residual,theory,policy,budget):
    names=theory.dependencies(goal);seen=set()
    def emit(a,b,method):
        pair=alpha((a,b))
        if not allowed(pair,theory,budget):return None
        if greater(pair[1],pair[0],theory.precedence,budget):pair=(pair[1],pair[0])
        elif not greater(pair[0],pair[1],theory.precedence,budget):return None
        pair=alpha(pair);key=goal_id(pair)
        if key in seen:return None
        seen.add(key);return pair,dict(method=method)
    if policy=='residual':
        # Generalize a ground changing argument, using input syntax only.
        for side,other in (goal,goal[::-1]):
            if variable(side) or side[0] not in theory.definitions:continue
            declaration=theory.definitions[side[0]]
            for index in range(len(declaration['inputs'])):
                if index==declaration['recursion'] or vars_of(side[index+1]):continue
                changed=False
                for eq in declaration['equations']:
                    left=read(eq['lhs'])
                    for _,term in positions(read(eq['rhs'])):
                        if not variable(term) and term[0]==side[0] and term[index+1]!=left[index+1]:changed=True
                if not changed:continue
                fresh='acc'
                while fresh in goal_vars(goal):fresh='_'+fresh
                v=('$',fresh,declaration['inputs'][index]);aa=list(side);aa[index+1]=v
                for bridge in typed_terms(theory,[other,v],names,budget,3):
                    hit=emit(tuple(aa),bridge,'generalize_changing_argument')
                    if hit:yield hit
        pair=shared(read_goal(residual['residual']),theory)
        if pair:
            hit=emit(*pair,'shared_subterm_abstraction')
            if hit:yield hit
        anchors=[];known=set()
        for side in read_goal(residual['residual']):
            for _,term in positions(side):
                for pattern in patterns(term,theory):
                    if pattern in known:continue
                    known.add(pattern);anchors.append(pattern)
        for pattern in anchors:
            leaves=[('$',name,sort) for name,sort in vars_of(pattern).items()]
            if not 1<=len(leaves)<=CAPS['variables']:continue
            local={t[0] for _,t in positions(pattern) if not variable(t)}|{'zero','nil'}
            if any(v[2]!=theory.sort(pattern) for v in leaves):
                local|={name for name,(ins,out) in theory.symbols.items()
                        if name in names and ins==(theory.sort(pattern),)*2 and out==theory.sort(pattern)}
            for rhs in typed_terms(theory,leaves,local,budget):
                if not greater(pattern,rhs,theory.precedence,budget):continue
                hit=emit(pattern,rhs,'typed_residual_frontier')
                if hit:yield hit
    else:
        # Same bounded typed universe, fixed equation-size/variable ordering.
        caches={};result_sort=theory.sort(goal[0]);sorts=(result_sort,'Nat' if result_sort=='List' else 'List')
        for total in range(3,2*CAPS['side_size']+1):
            for count in range(1,CAPS['variables']+1):
                minimum=2*count-1
                if total<2*minimum:continue
                for signature in itertools.product(sorts,repeat=count):
                    bound=min(CAPS['side_size'],total-minimum);cache_key=(signature,bound)
                    if cache_key not in caches:
                        leaves=[('$','g'+str(i),sort) for i,sort in enumerate(signature)]
                        caches[cache_key]=list(typed_terms(theory,leaves,names,budget,bound))
                    terms=caches[cache_key];by_size={}
                    for term in terms:
                        if theory.sort(term)==result_sort:by_size.setdefault(size(term),[]).append(term)
                    for a in terms:
                        if theory.sort(a)!=result_sort:continue
                        for b in by_size.get(total-size(a),()):
                            budget.use()
                            hit=emit(a,b,'fixed_typed_enumeration')
                            if hit:yield hit


def ground_domains():
    naturals=[('zero',),('succ',('zero',)),('succ',('succ',('zero',)))]
    lists=[('nil',)]
    for length in (1,2):
        for values in itertools.product(naturals,repeat=length):
            t=('nil',)
            for value in reversed(values):t=('cons',value,t)
            lists.append(t)
    return {'Nat':naturals,'List':lists}


def evaluate(term,theory,budget,cache,depth=0):
    budget.use()
    if depth>128:raise SearchLimit('ground evaluation depth limit')
    if term in cache:return cache[term]
    if variable(term):raise ValueError('nonground evaluation')
    args=tuple(evaluate(a,theory,budget,cache,depth+1) for a in term[1:])
    current=(term[0],*args)
    if term[0] in CONSTRUCTORS:result=current
    else:
        result=None
        for rule in theory.rules:
            if rule['lhs'][0]!=term[0]:continue
            env=match(rule['lhs'],current,rule['quantified'],theory,budget)
            if env is not None:
                result=evaluate(subst(rule['rhs'],env,budget),theory,budget,cache,depth+1);break
        if result is None:raise ValueError('validated ground definition has no case')
    if size(result)>CAPS['intermediate_nodes']:raise SearchLimit('ground result size limit')
    cache[term]=result;return result


def candidate_task(task,goal):
    result=copy.deepcopy(task);result['goal']=goal_data(goal);return result


def check_bundle(task,goal,proof,library,budget,checker):
    target=candidate_task(task,goal);identity=checker.bind(target,budget)['identity']
    certificate=dict(kind='recursive_identity',task_id=identity,lemmas=copy.deepcopy(library),proof=copy.deepcopy(proof))
    checked=checker.check(target,certificate,budget)
    return certificate,checked


def filter_candidate(task,pending,theory,budget,checker,cache):
    goal=read_goal(pending['goal']);scope=goal_vars(goal);domains=ground_domains()
    names=list(scope);cursor=pending.get('filter_cursor',0)
    assignments=itertools.islice(itertools.product(*(domains[scope[n]] for n in names)),CAPS['assignments'])
    for index,values in enumerate(assignments):
        if index<cursor:budget.use();continue
        env=dict(zip(names,values))
        left=evaluate(subst(goal[0],env,budget),theory,budget,cache)
        right=evaluate(subst(goal[1],env,budget),theory,budget,cache)
        if left!=right:
            target=candidate_task(task,goal)
            certificate=dict(kind='recursive_counterexample',task_id=checker.bind(target,budget)['identity'],
                             point={name:data(value) for name,value in env.items()})
            checked=checker.check(target,certificate,budget)
            pending.update(filter_cursor=index+1,filter_status='CHECKED_COUNTEREXAMPLE',certificate=certificate)
            return certificate,checked
        pending['filter_cursor']=index+1
    pending['filter_status']='SURVIVED_BOUNDED_TESTS';return None,None


def generation():
    root=Path(__file__).resolve().parent
    return hashlib.sha256(b''.join((root/name).read_bytes() for name in ('recursive.py','recursive_check.py'))).hexdigest()


def _seed_records(seed_records,checker,budget=None):
    checker.need(type(seed_records) in (list,tuple) and len(seed_records)<=8,'seed record bound')
    count=0
    for item in seed_records:
        if budget is not None:budget.use()
        checker.need(type(item) is dict and set(item)=={'source_task','source_certificate',
            'selected_indices','source_id','source_commit_id'},'seed record fields')
        checker.need(type(item['source_id']) is str and re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]{0,63}',item['source_id']) is not None,'seed source identifier')
        checker.need(type(item['source_commit_id']) is str and re.fullmatch(r'[0-9a-f]{64}',item['source_commit_id']) is not None,'seed source commit digest')
        indices=item['selected_indices']
        checker.need(type(indices) is list and bool(indices) and all(type(i) is int and 0<=i<=16 for i in indices),'seed indices')
        checker.need(indices==sorted(set(indices)),'seed indices must be distinct and ascending')
        count+=len(indices)
    checker.need(count<=8,'seed candidate bound')


def seed_context(task,seed_records,host,budget=None):
    """Context only, never a checked flag; callers charge this to common work."""
    checker=host.local_module('recursive_check');_seed_records(seed_records,checker,budget)
    if not seed_records:return None
    identity=checker.bind(task,budget)['identity']
    value=dict(schema='ember.recursive_seed.v1',receiving_task_id=identity,records=list(seed_records))
    if budget is not None:
        raw=checker._bytes(value,budget,host.STATE_LIMIT)
    else:raw=canonical(value).encode()
    return hashlib.sha256(raw).hexdigest()


def _episode_key(identity,policy,context,host):
    value=dict(kind='recursive_episode',root_task_id=identity,policy=policy)
    if context is not None:value['seed_context']=context
    return host.digest(value)


def episode_id(task,host,policy='residual',seed_records=(),budget=None):
    context=seed_context(task,seed_records,host,budget)
    identity=host.local_module('recursive_check').bind(task,budget)['identity']
    return _episode_key(identity,policy,context,host)


def progress_context(task,state,host,policy='residual',seed_records=(),budget=None):
    identity=episode_id(task,host,policy,seed_records,budget)
    content=[o for o in state['observations'] if o.get('task_id')==identity]
    if budget is not None:budget.use(len(host.canonical(content).encode()))
    return host.digest(content)


def _proof_references(proof,budget):
    """Traverse an already checked proof; IH references never leave their case."""
    pending=[proof];refs=set()
    while pending:
        node=pending.pop();budget.use()
        if node['rule']=='induction':pending.extend(case['proof'] for case in node['cases'].values())
        else:
            for step in node['left']+node['right']:
                budget.use()
                if step['source']['kind']=='lemma':refs.add(step['source']['index'])
    return refs


def _rebase_proof(proof,index_map,budget):
    result=copy.deepcopy(proof);pending=[result]
    while pending:
        node=pending.pop();budget.use()
        if node['rule']=='induction':pending.extend(case['proof'] for case in node['cases'].values())
        else:
            for step in node['left']+node['right']:
                budget.use()
                if step['source']['kind']=='lemma':step['source']['index']=index_map[step['source']['index']]
    return result


def prepare_seeds(task,seed_records,budget,host):
    """Rebuild checked closures under the receiving ORIGINAL full definitions.

    No rebased proof or checked flag is accepted. Source checking, extraction,
    rebasing and receiving prefix replay all use the receiving caller budget.
    """
    start=budget.work;checker=host.local_module('recursive_check')
    _seed_records(seed_records,checker,budget)
    result=dict(library=[],origins=[],candidates=[],skipped=[],phase_work={})
    if not seed_records:return dict(result,work=budget.work-start)
    checker.bind(task,budget);theory=Theory(task,budget)
    dependencies=theory.dependencies(read_goal(task['goal']))-set(CONSTRUCTORS)
    budget.use(sum(size(read(eq['rhs'])) for d in task['definitions'] for eq in d['equations'])+
               sum(size(t) for t in read_goal(task['goal'])))
    source_cache={};included={};selected=set()
    for record_index,item in enumerate(seed_records):
        source=item['source_task'];certificate=item['source_certificate'];began=budget.work
        raw=checker._bytes(dict(task=source,certificate=certificate),budget,host.STATE_LIMIT)
        source_key=raw
        if source_key not in source_cache:
            checked=checker.check(source,certificate,budget)
            checker.need(checked['kind']=='recursive_identity','a seed source must prove an identity')
            checker.need(source['domain']==task['domain'] and source['definitions']==task['definitions'],
                         'seed requires exact complete original definitions')
            entries=certificate['lemmas']+[dict(goal=source['goal'],proof=certificate['proof'])]
            certificate_digest=digest(certificate);budget.use(len(canonical(certificate).encode()))
            source_cache[source_key]=(checked['task_id'],certificate_digest,entries)
        source_id,certificate_digest,entries=source_cache[source_key]
        result['phase_work']['source_check']=result['phase_work'].get('source_check',0)+budget.work-began
        for index in item['selected_indices']:
            began=budget.work;checker.need(index<len(entries),'seed index outside original certificate')
            key=(source_id,certificate_digest,index)
            if key in selected:continue
            statement=read_goal(entries[index]['goal']);symbols=set()
            for term in statement:
                for _,part in positions(term):
                    budget.use()
                    if not variable(part) and part[0] not in CONSTRUCTORS:symbols.add(part[0])
            if not symbols&dependencies:
                result['skipped'].append(dict(source_record=record_index,entry_index=index,reason='no receiving dependency intersection'))
                continue
            closure=set();pending=[index]
            while pending:
                current=pending.pop();budget.use()
                if current in closure:continue
                checker.need(0<=current<len(entries),'seed dependency outside source')
                refs=_proof_references(entries[current]['proof'],budget)
                checker.need(all(type(i) is int and 0<=i<current for i in refs),'seed dependency must be earlier')
                closure.add(current);pending.extend(refs)
            new=[i for i in sorted(closure) if (source_id,certificate_digest,i) not in included]
            if len(result['library'])+len(new)>8:
                result['skipped'].append(dict(source_record=record_index,entry_index=index,reason='complete seed closure exceeds eight entries'))
                continue
            index_map={i:included[(source_id,certificate_digest,i)] for i in closure if (source_id,certificate_digest,i) in included}
            for i in new:
                index_map[i]=len(result['library'])
                entry=dict(goal=copy.deepcopy(entries[i]['goal']),proof=_rebase_proof(entries[i]['proof'],index_map,budget))
                result['library'].append(entry);included[(source_id,certificate_digest,i)]=index_map[i]
                result['origins'].append(dict(source_task_id=source_id,source_certificate_digest=certificate_digest,
                    entry_index=i,source_id=item['source_id'],source_commit_id=item['source_commit_id']))
            selected.add(key)
            candidate=dict(source_task_id=source_id,source_certificate_digest=certificate_digest,entry_index=index)
            candidate.update(id=digest(candidate),goal=copy.deepcopy(entries[index]['goal']),prefix_index=included[key])
            result['candidates'].append(candidate)
            result['phase_work']['closure_and_rebase']=result['phase_work'].get('closure_and_rebase',0)+budget.work-began
    if result['library']:
        began=budget.work;last=result['library'][-1]
        _,result['check']=check_bundle(task,read_goal(last['goal']),last['proof'],result['library'][:-1],budget,checker)
        result['phase_work']['receiving_prefix_check']=budget.work-began
    result['work']=budget.work-start
    result['phase_work']['other']=result['work']-sum(result['phase_work'].values())
    return result


def checkpoint(state,path,record,host):
    if len(host.canonical(record).encode())>host.STATE_LIMIT//2:raise SearchLimit('recursive episode half-state limit')
    updated=copy.deepcopy(state)
    updated['observations']=[o for o in updated['observations'] if o.get('task_id')!=record['task_id']]+[copy.deepcopy(record)]
    updated['observations']=updated['observations'][-128:]
    while len(host.canonical(updated).encode())+1>host.STATE_LIMIT and len(updated['observations'])>1:
        updated['observations'].pop(0)
    if len(host.canonical(updated).encode())+1>host.STATE_LIMIT:raise SearchLimit('recursive state size limit')
    if path is not None:
        destination=Path(path);destination.parent.mkdir(parents=True,exist_ok=True)
        temporary=destination.with_suffix(destination.suffix+'.tmp')
        temporary.write_text(host.canonical(updated)+'\n',encoding='utf-8',newline='\n');temporary.replace(destination)
    state.clear();state.update(updated)


def event(record,kind,**values):
    record['attempts'].append(dict(kind=kind,**values))
    if len(record['attempts'])>CAPS['history']:
        record['attempts'].pop(0);record['attempts_dropped']+=1


def validate_episode(record,task,theory,budget,checker,root,policy):
    """Reconstruct persisted goals, actual failed edges and generated candidates.

    Prefix library proofs are checked by the caller. Scheduling flags never
    replace that replay; every nonroot statement also needs producer provenance.
    """
    library=record['library'];nodes=record['nodes'];memo={};proposals={}
    checker.need(type(record.get('totals')) is dict,'recursive totals shape')
    for key,cap in (('candidates',1400),('formal_attempts',100),('commits',16),
                    ('parent_reentries',100),('counterexamples',1401)):
        n=record['totals'].get(key)
        checker.need(type(n) is int and 0<=n<=cap,'recursive total '+key)
    seed_count=record.get('seed_count',0)
    checker.need(type(seed_count) is int and 0<=seed_count<=8,'recursive seed count')
    checker.need(record['totals']['commits']==len(library)-seed_count,'recursive invented library count')
    checker.need(type(record.get('attempts_dropped')) is int and record['attempts_dropped']>=0,'history dropped count')
    checker.need(len(set(record['frontier']))==len(record['frontier']),'recursive frontier cycle')
    incoming={identity:[] for identity in nodes}
    def residual_for(parent,count):
        checker.need(type(count) is int and 0<=count<=len(library),'residual library prefix')
        key=(parent,count)
        if key not in memo:
            proof,residual=attempt(read_goal(nodes[parent]['goal']),theory,library[:count],budget)
            checker.need(proof is None and residual is not None,'saved unsupported edge is not a failed original attempt')
            memo[key]=residual
        return memo[key]
    def candidate_for(parent,count,index):
        checker.need(type(index) is int and 0<=index<CAPS['candidates'],'candidate provenance cursor')
        key=(parent,count,index)
        if key not in proposals:
            residual=residual_for(parent,count)
            found=None
            for i,item in enumerate(candidates(read_goal(nodes[parent]['goal']),residual,theory,policy,budget)):
                if i==index:found=item;break
            checker.need(found is not None,'saved candidate absent from original grammar cursor')
            proposals[key]=found
        return proposals[key]
    def finite_ok(item,goal):
        checker.need(type(item) is dict and item.get('goal')==goal,'saved finite test is for another goal')
        cursor=item.get('filter_cursor')
        checker.need(type(cursor) is int and 0<=cursor<=CAPS['assignments'],'saved finite-test cursor')
        checker.need(item.get('filter_status') in (None,'SURVIVED_BOUNDED_TESTS','CHECKED_COUNTEREXAMPLE'),'finite test status')
        if item.get('filter_status')=='CHECKED_COUNTEREXAMPLE':
            checked=checker.check(candidate_task(task,read_goal(goal)),item.get('certificate'),budget)
            checker.need(checked['kind']=='recursive_counterexample','finite counterexample kind')
    for identity,node in nodes.items():
        checker.need(type(node) is dict and type(node.get('goal')) is dict,'recursive node shape')
        target=copy.deepcopy(task);target['goal']=node['goal'];checker.bind(target,budget)
        checker.need(goal_id(read_goal(node['goal']))==identity,'recursive node identity')
        checker.need(type(node.get('depth')) is int and 0<=node['depth']<=CAPS['depth'],'recursive node depth')
        checker.need(node.get('status') in ('OPEN','BLOCKED','PROVED','EXHAUSTED'),'recursive node status')
        checker.need(type(node.get('awaiting_reentry',False)) is bool,'recursive reentry flag')
        checker.need(node['status']!='BLOCKED' or 'residual' in node,'blocked node lacks original residual')
        checker.need(type(node.get('cursor')) is int and 0<=node['cursor']<=CAPS['candidates'],'recursive node cursor')
        checker.need(type(node.get('repairs')) is int and 0<=node['repairs']<=CAPS['repairs'],'recursive repair counter')
        finite_ok(node.get('finite'),node['goal'])
        if node['status']=='PROVED':
            if identity==root:
                checker.need(type(record.get('final_certificate')) is dict,'proved root lacks evidence')
                checker.check(task,record['final_certificate'],budget)
            else:
                i=node.get('lemma_index')
                checker.need(type(i) is int and seed_count<=i<len(library) and library[i]['goal']==node['goal'],'proved child lacks checked invented library evidence')
        if 'residual' in node:
            count=node.get('residual_library_count')
            checker.need(node['residual']==residual_for(identity,count),'saved residual changed')
            checker.need(node.get('library_context')==digest(library[:count]),'saved residual library context')
        if 'pending' in node:
            pending=node['pending'];checker.need(type(pending) is dict,'pending candidate shape')
            finite_ok(pending,pending.get('goal'))
            candidate,why=candidate_for(identity,node.get('residual_library_count'),pending.get('candidate_index'))
            checker.need(pending.get('goal')==goal_data(candidate) and pending.get('candidate_id')==goal_id(candidate)
                         and pending.get('provenance')==why,'pending candidate differs from generated statement')
    for edge in record['edges']:
        checker.need(type(edge) is dict and edge.get('kind')=='proposed_auxiliary','recursive edge kind')
        parent,child=edge.get('parent'),edge.get('child')
        checker.need(parent in nodes and child in nodes and parent!=child and child!=root,'recursive edge endpoints')
        checker.need(nodes[child]['depth']==nodes[parent]['depth']+1,'recursive edge depth/cycle')
        candidate,why=candidate_for(parent,edge.get('library_count'),edge.get('candidate_index'))
        checker.need(goal_data(candidate)==nodes[child]['goal'] and why==edge.get('provenance'),'recursive edge candidate provenance')
        checker.need(edge.get('residual_id')==digest(residual_for(parent,edge['library_count'])),'recursive edge residual context')
        incoming[child].append(parent)
    checker.need(not incoming[root] and nodes[root]['depth']==0,'recursive root ancestry')
    checker.need(all(incoming[n] for n in nodes if n!=root),'orphan recursive child')
    for parent,child in zip(record['frontier'],record['frontier'][1:]):
        checker.need(parent in incoming[child],'frontier is not a parent-child chain')
    if record['schema']=='ember.recursive_episode.v2':
        invented={n.get('lemma_index') for key,n in nodes.items() if key!=root and n['status']=='PROVED'}
        checker.need(invented==set(range(seed_count,len(library))),'seeded invented library lacks producer nodes')


def _replay_record(prior,task,identity,saved_id,policy,context,seeds,theory,budget,checker,root,gen):
    checker.need(type(prior) is dict and prior.get('task_id')==saved_id and prior.get('kind')=='recursive_episode','recursive episode identity')
    schema='ember.recursive_episode.v1' if context is None else 'ember.recursive_episode.v2'
    checker.need(prior.get('schema')==schema,'recursive episode schema')
    checker.need(type(prior.get('nodes')) is dict and len(prior['nodes'])<=CAPS['nodes'],'recursive node cap')
    checker.need(type(prior.get('edges')) is list and len(prior['edges'])<=CAPS['edges'],'recursive edge cap')
    checker.need(type(prior.get('library')) is list and len(prior['library'])<=CAPS['lemmas'],'recursive library cap')
    checker.need(type(prior.get('attempts')) is list and len(prior['attempts'])<=CAPS['history'],'recursive history cap')
    checker.need(prior.get('original_task_id')==identity and prior.get('task')==task,'recursive original context')
    if context is None:
        checker.need(not any(key in prior for key in ('seed_context','seed_records','seed_count','seed_origins')),'empty episode cannot contain seed metadata')
    else:
        checker.need(prior.get('seed_context')==context and type(prior.get('seed_count')) is int and
            prior['seed_count']==len(seeds['library']) and prior.get('seed_origins')==seeds['origins'],
            'seeded episode context or origins changed')
        checker.need(prior['library'][:prior['seed_count']]==seeds['library'],'saved seed prefix differs from reconstructed proof')
    if prior.get('generation')!=gen or prior.get('grammar')!=CAPS or prior.get('policy')!=policy:return None,0
    record=copy.deepcopy(prior);replayed=0
    if record['library']:
        last=record['library'][-1]
        check_bundle(task,read_goal(last['goal']),last['proof'],record['library'][:-1],budget,checker)
        replayed=len(record['library'])
    checker.need(root in record['nodes'] and record['nodes'][root]['goal']==task['goal'],'recursive root node')
    checker.need(type(record.get('frontier')) is list and bool(record['frontier']) and record['frontier'][0]==root and
        len(record['frontier'])<=CAPS['depth']+1 and all(n in record['nodes'] for n in record['frontier']),'recursive frontier')
    validate_episode(record,task,theory,budget,checker,root,policy)
    return record,replayed


def inspect_episode(task,state,budget,host,policy='residual',seed_records=(),context_budget=None):
    """Fresh replay only: no native stage, candidate generation advance or write."""
    checker=host.local_module('recursive_check');checker.need(policy in ('direct','enumerate','residual'),'recursive policy')
    common=budget if context_budget is None else context_budget
    context=seed_context(task,seed_records,host,common)
    binding=checker.bind(task,budget);identity=binding['identity'];saved_id=_episode_key(identity,policy,context,host)
    seeds=prepare_seeds(task,seed_records,budget,host);theory=Theory(task,budget)
    root=goal_id(read_goal(task['goal']))
    prior=next((o for o in state['observations'] if o.get('task_id')==saved_id),None)
    record=None
    if prior is not None:
        if context is not None:checker.need(prior.get('seed_records')==list(seed_records),'saved seed records changed')
        record,_=_replay_record(prior,task,identity,saved_id,policy,context,seeds,theory,budget,checker,root,generation())
    residual=None if record is None else copy.deepcopy(record['nodes'][root].get('residual'))
    budget.use(sum(size(read(eq['rhs'])) for d in task['definitions'] for eq in d['equations'])+
               sum(size(t) for t in read_goal(task['goal'])))
    return dict(episode_id=saved_id,record=record,residual=residual,
        closure_count=len(theory.dependencies(read_goal(task['goal']))-set(CONSTRUCTORS)),seed_info=seeds)


def match_residual(residual,seed_info,task,budget,host):
    """Scheduling proposals only; inputs must come from this call's replay/preparation.

    This helper admits no theorem and advances no saved native cursor. Only source
    statement variables are quantified; receiving eigenvariables remain rigid.
    """
    start=budget.work;matched=[];details=[]
    if residual is None:return dict(count=0,matched_ids=[],matches=[],work=0,residual_present=False)
    checker=host.local_module('recursive_check');checker.bind(task,budget);theory=Theory(task,budget)
    sides=read_goal(residual['residual']);checker.need(all(bounded_term(t) for t in sides),'residual term bound')
    candidates_=seed_info['candidates'];checker.need(len(candidates_)<=8,'residual candidate bound')
    for candidate in candidates_:
        goal=read_goal(candidate['goal']);quantified=set(goal_vars(goal));hit=None
        for direction in (1,-1):
            a,b=goal if direction==1 else goal[::-1]
            if variable(a) or not quantified.issubset(vars_of(a)):continue
            for side,t in enumerate(sides):
                for path,part in positions(t):
                    budget.use();env=match(a,part,quantified,theory,budget)
                    if env is None or set(env)!=quantified:continue
                    replacement=subst(b,env,budget)
                    if replacement==part:continue
                    hit=dict(candidate_id=candidate['id'],direction=direction,side=side,at=list(path),
                        subst={name:data(value) for name,value in sorted(env.items())});break
                if hit:break
            if hit:break
        if hit and candidate['id'] not in matched:matched.append(candidate['id']);details.append(hit)
    return dict(count=len(matched),matched_ids=matched,matches=details,work=budget.work-start,residual_present=True)


def residual_matches(task,state,budget,host,seed_records=(),policy='residual',episode_seed_records=(),context_budget=None):
    common=budget if context_budget is None else context_budget
    inspection=inspect_episode(task,state,common,host,policy,episode_seed_records,common)
    seeds=prepare_seeds(task,seed_records,budget,host)
    result=match_residual(inspection['residual'],seeds,task,common,host)
    result.update(episode_id=inspection['episode_id'],residual=inspection['residual'],
                  closure_count=inspection['closure_count'],seed_info=seeds)
    return result


def run(task,state,state_path,budget,host,policy='residual',steps=4,seed_records=(),context_budget=None):
    checker=host.local_module('recursive_check')
    checker.need(policy in ('direct','enumerate','residual'),'recursive policy')
    checker.need(type(steps) is int and 1<=steps<=64,'recursive steps must be in 1..64')
    start=budget.work;binding=checker.bind(task,budget);identity=binding['identity']
    context=seed_context(task,seed_records,host,budget if context_budget is None else context_budget)
    saved_id=_episode_key(identity,policy,context,host)
    budget.use(len(host.canonical(task).encode()))
    theory=Theory(task,budget);original=read_goal(task['goal']);root=goal_id(original);gen=generation()
    prior=next((o for o in state['observations'] if o.get('task_id')==saved_id),None)
    record=dict(task_id=saved_id,kind='recursive_episode',schema='ember.recursive_episode.v1',
        original_task_id=identity,task=copy.deepcopy(task),generation=gen,policy=policy,grammar=CAPS,
        nodes={root:dict(goal=goal_data(original),depth=0,status='OPEN',cursor=0,repairs=0,
                        finite=dict(goal=goal_data(original),filter_cursor=0))},edges=[],library=[],
        frontier=[root],attempts=[],attempts_dropped=0,
        totals=dict(candidates=0,formal_attempts=0,counterexamples=0,commits=0,parent_reentries=0))
    seeds=prepare_seeds(task,seed_records,budget,host) if context is not None else None
    if context is not None:
        record.update(schema='ember.recursive_episode.v2',seed_context=context,seed_records=copy.deepcopy(list(seed_records)),
                      seed_count=len(seeds['library']),seed_origins=copy.deepcopy(seeds['origins']),library=copy.deepcopy(seeds['library']))
    replayed=0;invalidated=False
    if prior:
        if context is not None:checker.need(prior.get('seed_records')==list(seed_records),'saved seed records changed')
        restored,replayed=_replay_record(prior,task,identity,saved_id,policy,context,seeds,theory,budget,checker,root,gen)
        if restored is not None:record=restored
        else:invalidated=True
    cache={};executed=[];final=None;reason='bounded stages complete';changed=False
    phase_work={'input_and_replay':budget.work-start}
    if record.get('final_certificate'):
        checked=checker.check(task,record['final_certificate'],budget)
        status='CHECKED_RECURSIVE_IDENTITY' if checked['kind']=='recursive_identity' else 'CHECKED_RECURSIVE_COUNTEREXAMPLE'
        result=dict(status=status,certificate=record['final_certificate'],check=checked,
                    recursive=dict(replayed_lemmas=replayed,original_evidence_replay=True,episode_id=saved_id))
        if context is not None:result['recursive'].update(seed_context=context,seed_count=record['seed_count'],seed_info=seeds)
        return result
    for _ in range(steps):
        if not record['frontier']:reason='bounded grammar exhausted';break
        current=record['frontier'][-1];node=record['nodes'][current]
        if node['status']=='EXHAUSTED':
            if current==root:reason=node.get('reason','search exhausted');break
            record['frontier'].pop();changed=True;continue
        before=copy.deepcopy(record);stage=Slice(budget,min(CAPS['stage_work'],max(0,budget.limit-budget.work)))
        phase='';began=budget.work;stamp=budget.work
        def change_phase(name):
            nonlocal phase,stamp
            if phase:phase_work[phase]=phase_work.get(phase,0)+budget.work-stamp
            phase=name;stamp=budget.work
        try:
            goal=read_goal(node['goal']);library_key=digest(record['library'])
            if node.get('library_context')!=library_key and node['status']=='BLOCKED':
                node.update(status='OPEN',cursor=0);node.pop('pending',None)
            if node['status']=='OPEN':
                change_phase('finite_test')
                finite=node.setdefault('finite',dict(goal=node['goal'],filter_cursor=0))
                if finite.get('filter_status')!='SURVIVED_BOUNDED_TESTS':
                    certificate,checked=filter_candidate(task,finite,theory,stage,checker,cache)
                    if certificate:
                        record['totals']['counterexamples']+=1;node['status']='EXHAUSTED';node['reason']='checked candidate counterexample'
                        event(record,'COUNTEREXAMPLE',node=current,certificate=certificate)
                        if current==root:
                            final=dict(status='CHECKED_RECURSIVE_COUNTEREXAMPLE',certificate=certificate,check=checked)
                            record['final_certificate']=certificate
                        changed=True
                        if final:break
                        continue
                change_phase('formal_search')
                if node.get('awaiting_reentry') and node['repairs']>=CAPS['repairs']:
                    node.update(status='EXHAUSTED',reason='parent repair cap');changed=True;continue
                if record['totals']['formal_attempts']>=CAPS['formal_attempts']:
                    node.update(status='EXHAUSTED',reason='formal attempt cap');changed=True;continue
                proof,residual=attempt(goal,theory,record['library'],stage)
                record['totals']['formal_attempts']+=1
                if node.get('awaiting_reentry'):
                    record['totals']['parent_reentries']+=1;node.pop('awaiting_reentry')
                    node['repairs']+=1
                    event(record,'REENTER_PARENT',node=current,library_context=library_key)
                if proof is not None:
                    change_phase('proof_check')
                    certificate,checked=check_bundle(task,goal,proof,record['library'],stage,checker)
                    node.update(status='PROVED')
                    if current==root:
                        final=dict(status='CHECKED_RECURSIVE_IDENTITY',certificate=certificate,check=checked)
                        record['final_certificate']=certificate
                    elif len(record['library'])<CAPS['lemmas']:
                        node['lemma_index']=len(record['library']);record['library'].append(dict(goal=node['goal'],proof=proof))
                        record['totals']['commits']+=1;event(record,'LEMMA_COMMITTED',node=current,lemma_index=node['lemma_index'])
                        record['frontier'].pop()
                        for parent in record['frontier']:
                            record['nodes'][parent]['status']='OPEN';record['nodes'][parent]['awaiting_reentry']=True
                    else:node.update(status='EXHAUSTED',reason='checked lemma cap')
                else:
                    if node.get('residual')!=residual:node['cursor']=0
                    # The candidate stream is generated from the residual; a new residual starts at its head.
                    node.update(status='BLOCKED',residual=residual,library_context=library_key,
                                residual_library_count=len(record['library']))
                    event(record,'UNSUPPORTED_EDGE',node=current,residual=residual)
                    if policy=='direct' or node['depth']>=CAPS['depth']:
                        node.update(status='EXHAUSTED',reason='direct or repair depth limit')
                changed=True
                if final:break
            else:
                change_phase('candidate_generation')
                if node.get('repairs',0)>=CAPS['repairs'] or record['totals']['candidates']>=CAPS['candidates']:
                    node.update(status='EXHAUSTED',reason='repair or candidate cap');changed=True;continue
                if 'pending' not in node:
                    iterator=candidates(goal,node['residual'],theory,policy,stage)
                    found=None
                    for index,(candidate,provenance) in enumerate(iterator):
                        if index<node['cursor']:continue
                        if record['totals']['candidates']>=CAPS['candidates']:break
                        node['cursor']=index+1;record['totals']['candidates']+=1
                        cid=goal_id(candidate)
                        if cid in record['frontier']:
                            event(record,'ANCESTRY_CYCLE_REJECTED',node=current,candidate=cid);continue
                        old=record['nodes'].get(cid)
                        if old and (old['status']=='PROVED' or old.get('library_context')==library_key):continue
                        if old and old['depth']!=node['depth']+1:continue
                        found=dict(goal=goal_data(candidate),candidate_id=cid,candidate_index=index,
                                   filter_cursor=0,provenance=provenance)
                        break
                    if found is None:
                        node.update(status='EXHAUSTED',reason='candidate grammar exhausted');changed=True;continue
                    node['pending']=found
                change_phase('candidate_filter');pending=node['pending']
                certificate,checked=filter_candidate(task,pending,theory,stage,checker,cache)
                if certificate:
                    record['totals']['counterexamples']+=1
                    event(record,'CANDIDATE_COUNTEREXAMPLE',node=current,goal=pending['goal'],
                          provenance=pending['provenance'],certificate=certificate)
                    node.pop('pending');changed=True;continue
                cid=pending['candidate_id']
                if len(record['nodes'])>=CAPS['nodes'] or len(record['edges'])>=CAPS['edges']:
                    node.update(status='EXHAUSTED',reason='complete child exceeds graph cap');changed=True;continue
                child=dict(goal=pending['goal'],depth=node['depth']+1,status='OPEN',cursor=0,repairs=0,finite=copy.deepcopy(pending))
                record['nodes'][cid]=child
                record['edges'].append(dict(parent=current,child=cid,kind='proposed_auxiliary',
                    provenance=pending['provenance'],residual_id=digest(node['residual']),
                    candidate_index=pending['candidate_index'],library_count=node['residual_library_count']))
                event(record,'CANDIDATE_OPENED',parent=current,child=cid,goal=pending['goal'],provenance=pending['provenance'])
                node.pop('pending');record['frontier'].append(cid);changed=True
        except (SearchLimit,checker.Limit) as exc:
            reason=str(exc)
            # Keep only completed candidate/filter cursor work, never partial proof claims.
            if phase in ('finite_test','candidate_generation','candidate_filter'):
                changed=changed or record!=before
            else:record=before
            break
        except checker.Invalid as exc:
            if phase!='proof_check':raise
            # The separate checker refused a produced proof: never admit it, close this node,
            # and keep the stages this call already completed.
            record=before;record['nodes'][current].update(status='EXHAUSTED',reason='checker refused produced proof: '+str(exc))
            changed=True
        finally:
            if phase:phase_work[phase]=phase_work.get(phase,0)+budget.work-stamp
            executed.append(dict(node=current,phase=phase,work=budget.work-began))
    if changed or prior is None or invalidated:
        try:checkpoint(state,state_path,record,host)
        except SearchLimit as exc:
            reason=str(exc)
            if final:final['checkpoint_preserved']=True
    result=final or dict(status='UNKNOWN',reason=reason)
    result['recursive']=dict(episode_id=saved_id,original_task_id=identity,policy=policy,
        totals=copy.deepcopy(record['totals']),executed=executed,replayed_lemmas=replayed,
        frontier=list(record['frontier']),node_count=len(record['nodes']),edge_count=len(record['edges']),
        library_count=len(record['library']),state_bytes=len(host.canonical(record).encode()),
        work=budget.work-start,phase_work=phase_work,invalidated_generation=invalidated,grammar=CAPS)
    if context is not None:result['recursive'].update(seed_context=context,seed_count=record['seed_count'],seed_info=seeds)
    return result
