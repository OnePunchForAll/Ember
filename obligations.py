"""Bounded durable AND-premise / OR-route search over original polynomial tasks.

Graph edges schedule work. Only freshly checked original evidence admits a root.
Composition keeps one original guard; required premise proofs remain flat.
Planning reconstructs source/core/binding obligations; saved flags admit nothing.
"""
import copy
import hashlib
from pathlib import Path

MAX_NODES=64
MAX_EDGES=128
MAX_BINDINGS=16
MAX_STAGE_WORK=200_000
MAX_PLAN_WORK=300_000


class PlanningEnded(RuntimeError):pass


class PlanningBudget:
    def __init__(self,parent,limit):self.parent=parent;self.limit=limit;self.work=0
    def use(self,amount=1):
        if self.work+amount>self.limit:raise PlanningEnded('reserved planning budget exhausted')
        self.parent.use(amount);self.work+=amount


def generation():
    root=Path(__file__).resolve().parent
    return hashlib.sha256(b''.join((root/name).read_bytes() for name in
        ('ember.py','algebra.py','algebra_check.py','obligations.py'))).hexdigest()


def structure(nodes):
    return {identity:{key:copy.deepcopy(value) for key,value in node.items()
        if key in ('role','task','requires','alternatives','plan_id')}
        for identity,node in nodes.items()}


def plan_graph(task,records,budget,host,allow_guarded=False):
    checker=host.local_module('algebra_check');algebra=host.local_module('algebra')
    checker.need(type(allow_guarded) is bool,'guarded planning flag must be Boolean')
    root_id=checker.bind(task)['identity']
    direct_id=host.digest(dict(role='direct',root=root_id))
    nodes={root_id:dict(role='original',task=copy.deepcopy(task),alternatives=[direct_id]),
           direct_id:dict(role='direct',task=copy.deepcopy(task),requires=[])}
    plans={};routes=[];rejected=[];bindings=0;edges=1
    prepared_sources=0;duplicates=0;seen_mapped={};pool_bytes=2
    # Preserve evidence and unsupported dependency declarations so preparation
    # can reject them. Dropping those fields here would bypass its intake rule.
    source_keys=('task','certificate',*algebra.PREMISE_GRAPH_KEYS)
    sources=[{key:o[key] for key in source_keys if key in o} if type(o) is dict else o
             for o in records[:8]]
    # Task metadata is not a mathematical premise, but it is present in planned
    # child records. Its change rebuilds those records instead of falsely
    # accusing an otherwise identical unresolved checkpoint of tampering.
    context_input=dict(root_task=task,sources=sources)
    if allow_guarded:context_input['allow_guarded']=True
    context=host.digest(context_input)
    for index,record in enumerate(sources):
        try:
            budget.use()
            checker.need(type(record) is dict and type(record.get('task')) is dict,'source record task')
            sb=checker.bind(record['task'])
            if sb['identity']==root_id:continue
            # Private, call-local preparation checks this source and its core
            # once. Each returned plan owns its evidence; no saved flag or
            # caller-supplied prepared dictionary can authorize a new plan.
            planner=algebra.prepare_premise_planner(task,record,budget,checker,allow_guarded=allow_guarded)
            prepared_sources+=1
            for mapping in algebra.lemma_bindings(sb['names'],task['variables']):
                if bindings>=MAX_BINDINGS:break
                bindings+=1
                try:
                    plan=planner(mapping)
                    child_ids=[checker.bind(child)['identity'] for child in plan['children']]
                    # A child equal to the original is not a decomposition. Keep
                    # the direct route; do not construct a circular proof graph.
                    checker.need(root_id not in child_ids,'premise equals the original root')
                    # Identical mapped evidence and ordered original children
                    # define the same transfer. Keep the first full provenance
                    # plan; equal child sets alone would not justify this merge.
                    equivalent=host.canonical(dict(receiving_task_id=plan['receiving_task_id'],
                        mapped_task=plan['mapped_task'],mapped_certificate=plan['mapped_certificate'],
                        children=plan['children'])).encode()
                    budget.use(len(equivalent))
                    if equivalent in seen_mapped:
                        duplicates+=1
                        rejected.append(dict(source=index,mapping=mapping,
                            reason='duplicate checked mapped transfer',duplicate_of=seen_mapped[equivalent]))
                        continue
                    route_id=host.digest(dict(role='transfer',root=root_id,plan=plan['plan_id']))
                    if route_id in plans:continue
                    additions={cid:dict(role='required_premise',task=copy.deepcopy(child),requires=[])
                               for cid,child in zip(child_ids,plan['children']) if cid not in nodes}
                    next_edges=edges+1+len(set(child_ids))
                    if len(nodes)+len(additions)+1>MAX_NODES or next_edges>MAX_EDGES:
                        rejected.append(dict(source=index,reason='complete plan exceeds graph node/edge cap'));continue
                    # Exact canonical object size: braces, each quoted key,
                    # colon, value, and separators. Avoid serializing all prior
                    # plans again for every insertion.
                    added_bytes=len(host.canonical(route_id).encode())+1+len(host.canonical(plan).encode())+(1 if plans else 0)
                    if pool_bytes+added_bytes>host.STATE_LIMIT//2:
                        rejected.append(dict(source=index,reason='complete plans exceed half-state reservation'));continue
                    nodes.update(additions)
                    nodes[route_id]=dict(role='transfer',plan_id=plan['plan_id'],requires=list(dict.fromkeys(child_ids)))
                    plans[route_id]=plan;routes.append(route_id);edges=next_edges
                    pool_bytes+=added_bytes;seen_mapped[equivalent]=route_id
                except (checker.Invalid,checker.Limit,KeyError,TypeError) as exc:
                    rejected.append(dict(source=index,mapping=mapping,reason=str(exc)))
        except PlanningEnded as exc:
            rejected.append(dict(source=index,reason=str(exc)));break
        except (checker.Invalid,checker.Limit,KeyError,TypeError) as exc:
            rejected.append(dict(source=index,reason=str(exc)))
        if bindings>=MAX_BINDINGS:break
    nodes[root_id]['alternatives']=routes+[direct_id]
    return dict(root_id=root_id,nodes=nodes,plans=plans,proposal_context=context,
        rejected_plans=rejected,binding_attempts=bindings,edge_count=edges,
        source_core_preparations=prepared_sources,duplicate_plans=duplicates,plan_pool_bytes=pool_bytes)


def checked_result(task,result,budget,checker,flat_premise=False):
    checker.need(type(result) is dict and result.get('status') in
                 ('CHECKED_IMPLICATION','CHECKED_COUNTEREXAMPLE'),'supported leaf evidence status')
    certificate=result.get('certificate');checked=checker.check(task,certificate,budget)
    status=checker.result_status(checked)
    checker.need(status==result['status'],'leaf status differs from certificate kind')
    if flat_premise:
        checker.need(checked['kind'] in ('polynomial_combination','rational_counterexample'),
                     'localized premise proof is unsupported; a flat premise proof is required')
    return checked


def compact(result):
    return {k:copy.deepcopy(result[k]) for k in ('status','certificate','reason','proof_method') if k in result}


def lift_premise_counterexample(task,original,result,budget,checker):
    """W: a checked premise refutation refutes the original only if the original checker admits its point."""
    point=result.get('certificate',{}).get('point')
    certificate=dict(kind='rational_counterexample',task_id=original,point=copy.deepcopy(point))
    try:checked=checker.check(task,certificate,budget)
    except checker.Invalid:return None
    return dict(status=checker.result_status(checked),certificate=certificate,proof_method='lifted_premise_counterexample')


def checkpoint(state,path,record,host):
    if path is None:return
    updated=copy.deepcopy(state)
    updated['observations']=[o for o in updated['observations'] if o['task_id']!=record['task_id']]+[copy.deepcopy(record)]
    updated['observations']=updated['observations'][-128:]
    # Preserve the active record, then discard oldest unrelated observations.
    while len(host.canonical(updated).encode())+1>host.STATE_LIMIT and len(updated['observations'])>1:
        updated['observations'].pop(0)
    if len(host.canonical(updated).encode())+1>host.STATE_LIMIT:
        raise host.Refused('active obligation checkpoint exceeds 1 MiB')
    destination=Path(path);destination.parent.mkdir(parents=True,exist_ok=True)
    temporary=destination.with_suffix(destination.suffix+'.tmp')
    temporary.write_text(host.canonical(updated)+'\n',encoding='utf-8',newline='\n');temporary.replace(destination)
    state.clear();state.update(updated)


def run(task,state,state_path,budget,host,records,steps=4,leaf_records=None):
    checker=host.local_module('algebra_check');algebra=host.local_module('algebra')
    if leaf_records is None:leaf_records=records
    checker.need(type(leaf_records) in (list,tuple) and len(leaf_records)<=8,
                 'at most eight original leaf proof candidates')
    original=checker.bind(task)['identity'];gen=generation()
    saved_id=host.digest(dict(kind='proof_obligations',root_task_id=original))
    previous=next((o for o in state['observations'] if o['task_id']==original),None)
    if previous and type(previous.get('certificate')) is dict:
        try:
            checked=checked_result(task,previous,budget,checker)
            return dict(status=previous['status'],certificate=copy.deepcopy(previous['certificate']),
                check=checked,reused_after_fresh_check=True,
                obligations=dict(original_task_id=original,executed=[],original_evidence_replay=True,
                    final_flat_replay=checked['kind']=='polynomial_combination',final_proof_kind=checked['kind']))
        except checker.Invalid:pass
    before=budget.work
    planning_limit=min(MAX_PLAN_WORK,max(0,(budget.limit-budget.work)//3))
    graph=plan_graph(task,records,PlanningBudget(budget,planning_limit),host,allow_guarded=True)
    planning_work=budget.work-before
    nodes=graph['nodes'];plans=graph['plans']
    # Planning can inspect guarded sources while the leaf solvers keep their
    # independently selected flat window. Both actual evidence lists affect
    # whether an unfinished attempt is still applicable.
    source_keys=('task','certificate',*algebra.PREMISE_GRAPH_KEYS)
    leaf_sources=[{key:o[key] for key in source_keys if key in o} if type(o) is dict else o
                  for o in leaf_records]
    context=host.digest(dict(planning_context=graph['proposal_context'],leaf_sources=leaf_sources))
    prior=next((o for o in state['observations'] if o['task_id']==saved_id),None)
    record=dict(task_id=saved_id,kind='proof_obligations',generation=gen,
        original_task_id=original,proposal_context=context,nodes=nodes,plans=plans,
        attempts=[],attempts_dropped=0,edge_count=graph['edge_count'],planning_limit=planning_limit)
    invalidated=[];replayed=[];executed=[];replay_work=0
    # No write occurs until the entire applicable checkpoint replay succeeds.
    if prior:
        checker.need(type(prior.get('nodes')) is dict and len(prior['nodes'])<=MAX_NODES,'saved obligation node bound')
        checker.need(all(type(n) is dict for n in prior['nodes'].values()),'saved obligation node shape')
        checker.need(type(prior.get('attempts')) is list and len(prior['attempts'])<=64,'saved obligation attempts bound')
        checker.need(type(prior.get('attempts_dropped',0)) is int and prior.get('attempts_dropped',0)>=0,'saved dropped-attempt count')
        if (prior.get('generation')==gen and prior.get('proposal_context')==context
            and type(prior.get('planning_limit')) is int and prior['planning_limit']>planning_limit
            and not set(prior['nodes']).issubset(nodes)):
            return dict(status='UNKNOWN',reason='planning allowance cannot reconstruct the fuller saved graph',
                obligations=dict(original_task_id=original,checkpoint_id=saved_id,executed=[],
                    planning_work=planning_work,planning_limit=planning_limit,prior_checkpoint_preserved=True))
        if (prior.get('generation')==gen and prior.get('proposal_context')==context
            and prior.get('planning_limit')==planning_limit):
            checker.need(structure(prior['nodes'])==structure(nodes) and prior.get('plans')==plans,
                         'saved obligation graph differs from reconstructed original dependencies')
        record['attempts']=copy.deepcopy(prior['attempts']);record['attempts_dropped']=prior.get('attempts_dropped',0)
        for identity,node in nodes.items():
            old=prior['nodes'].get(identity)
            if type(old) is not dict or old.get('role')!=node['role']:continue
            result=old.get('result')
            if type(result) is not dict:continue
            if result.get('status')=='UNKNOWN':
                if prior.get('generation')==gen and prior.get('proposal_context')==context:
                    allocation=old.get('allocation')
                    checker.need(type(allocation) is int and allocation>=0,'saved obligation allocation')
                    node.update(result=copy.deepcopy(result),allocation=allocation)
                continue
            if node['role']=='transfer':
                # Saved root evidence must independently settle the original.
                receiving=task
            elif node['role'] in ('required_premise','direct','original'):receiving=node['task']
            else:continue
            if node['role']=='required_premise' and old.get('task')!=node['task']:continue
            began=budget.work
            try:
                checked_result(receiving,result,budget,checker,flat_premise=node['role']=='required_premise')
                node['result']=compact(result);replayed.append(identity)
            except checker.Invalid:invalidated.append(identity)
            finally:replay_work+=budget.work-began
    root=nodes[original]
    if root.get('result',{}).get('status') in ('CHECKED_IMPLICATION','CHECKED_COUNTEREXAMPLE'):
        final=dict(root['result'],reused_after_fresh_check=True)
    else:final=None

    def retryable(node,allocation):
        result=node.get('result')
        return result is None or (result.get('status')=='UNKNOWN' and allocation>node.get('allocation',-1))

    def choose(allocation):
        for route_id in root['alternatives']:
            route=nodes[route_id]
            if route['role']=='direct':
                if retryable(route,allocation):return route_id
                continue
            children=[nodes[cid] for cid in route['requires']]
            if any(n.get('result',{}).get('status')=='CHECKED_COUNTEREXAMPLE' for n in children):continue
            # A checked alternative could already close the parent after replay.
            if route.get('result',{}).get('status')=='CHECKED_IMPLICATION':return route_id
            for cid in route['requires']:
                if retryable(nodes[cid],allocation):return cid
            if all(n.get('result',{}).get('status')=='CHECKED_IMPLICATION' for n in children) and retryable(route,allocation):
                return route_id
        return None

    for _ in range(steps if final is None else 0):
        remaining=budget.limit-budget.work
        if remaining<=0:raise host.Exhausted('obligation work budget exhausted')
        allocation=min(MAX_STAGE_WORK,max(1,remaining//2))
        identity=choose(allocation)
        if identity is None:break
        node=nodes[identity];role=node['role'];began=budget.work
        if role=='transfer' and node.get('result',{}).get('status')=='CHECKED_IMPLICATION':
            final=copy.deepcopy(node['result']);root['result']=compact(final);break
        if role=='transfer':
            plan=plans[identity]
            certs=[nodes[checker.bind(child)['identity']]['result']['certificate'] for child in plan['children']]
            portion=host.Budget(allocation)
            try:result=algebra.assemble_premises(task,plan,certs,portion,checker,allow_guarded=True)
            except (host.Exhausted,checker.Limit,checker.Invalid) as exc:result=dict(status='UNKNOWN',reason=str(exc))
            budget.use(portion.work)
        else:
            # These remain original receiving-context tasks. No successful child
            # is silently inserted among another child's assumptions.
            result=host.solve(node['task'],None,allocation,lemma_records=leaf_records)
            budget.use(result.get('work',allocation))
        if result['status']!='UNKNOWN':
            checked_result(task if role=='transfer' else node['task'],result,budget,checker,
                           flat_premise=role=='required_premise')
        node.update(result=compact(result),allocation=allocation)
        event=dict(node_id=identity,role=role,status=result['status'],allocation=allocation,
            work=budget.work-began,generation=gen,proposal_context=context)
        record['attempts'].append(event)
        if len(record['attempts'])>64:record['attempts'].pop(0);record['attempts_dropped']+=1
        executed.append(event)
        if role in ('direct','transfer') and result['status']!='UNKNOWN':
            final=compact(result);root['result']=compact(result)
        elif role=='required_premise' and result['status']=='CHECKED_COUNTEREXAMPLE':
            # A premise child keeps the original assumptions and guards, so its
            # refuting point is also offered to the original goal. The original
            # checker decides; otherwise the point only closes this transfer route.
            lifted=lift_premise_counterexample(task,original,result,budget,checker)
            if lifted is not None:
                final=lifted;root['result']=compact(lifted)
                event=dict(node_id=original,role='lifted_parent_refutation',status=lifted['status'],allocation=0,
                    work=0,generation=gen,proposal_context=context,premise_node_id=identity)
                record['attempts'].append(event)
                if len(record['attempts'])>64:record['attempts'].pop(0);record['attempts_dropped']+=1
                executed.append(event)
        checkpoint(state,state_path,record,host)
        if final is not None:break
    if final is None:final=dict(status='UNKNOWN',reason='bounded proof obligations remain unresolved')
    final['obligations']=dict(original_task_id=original,checkpoint_id=saved_id,generation=gen,
        proposal_context=context,node_count=len(nodes),edge_count=graph['edge_count'],
        planning_work=planning_work,planning_limit=planning_limit,replay_work=replay_work,replayed_nodes=replayed,
        source_core_preparations=graph.get('source_core_preparations'),
        duplicate_plans=graph.get('duplicate_plans'),plan_pool_bytes=graph.get('plan_pool_bytes'),
        invalidated_nodes=invalidated,executed=executed,rejected_plans=graph['rejected_plans'],
        nodes=copy.deepcopy(nodes),limits='Typed bounded premises; children require flat proofs, composition preserves any selected original guard, and only freshly checked original evidence admits the root.')
    return final
