"""Bounded inert-source TPM episodes; source claims never authorize mathematics."""
import copy
import hashlib
import json
from pathlib import Path
import re
import time

CAPS=dict(sources=8,source_bytes=65536,total_source_bytes=524288,roots=4,
          nodes=64,edges=128,attempts=128,actions=64,candidates=8,seeds=8,root_work=2000000)
POLICIES=('native_isolated','graph_isolated','fixed_bridge','gap_bridge')
IDENTIFIER=re.compile(r'[A-Za-z_][A-Za-z_0-9]{0,63}\Z')
HEX=re.compile(r'[0-9a-f]{64}\Z')
CLOSED={'recursive_identity':'CHECKED_RECURSIVE_IDENTITY',
        'recursive_counterexample':'CHECKED_RECURSIVE_COUNTEREXAMPLE'}

class Capacity(RuntimeError):pass

def need(condition,message,host):
    if not condition:raise host.Refused(message)

def keys(value,required,host,optional=()):
    need(type(value) is dict and set(required)<=set(value)<=set(required)|set(optional),
         'source object fields differ from supported grammar',host)

def charged_digest(value,budget,host):
    raw=host.canonical(value).encode('utf-8');budget.use(len(raw));return hashlib.sha256(raw).hexdigest()

def generation():
    root=Path(__file__).resolve().parent
    return hashlib.sha256(b''.join((root/name).read_bytes() for name in
        ('source_episode.py','recursive.py','recursive_check.py'))).hexdigest()

def decode(text,host):
    def pairs(items):
        result={}
        for key,value in items:
            need(key not in result,'duplicate source JSON field',host);result[key]=value
        return result
    def constant(value):raise host.Refused('nonfinite source JSON literal')
    try:return json.loads(text,object_pairs_hook=pairs,parse_constant=constant)
    except (ValueError,TypeError,RecursionError) as exc:raise host.Refused('invalid bounded source JSON: '+str(exc)) from exc

def symbols(term,budget):
    result=set();pending=[term]
    while pending:
        value=pending.pop();budget.use()
        if type(value) is list:
            result.add(value[0]);pending.extend(value[1:])
    return result

def closure(task,budget):
    definitions={d['name']:d for d in task['definitions']}
    pending=list(symbols(task['goal']['lhs'],budget)|symbols(task['goal']['rhs'],budget));seen=set()
    while pending:
        name=pending.pop();budget.use()
        if name in seen or name not in definitions:continue
        seen.add(name)
        for equation in definitions[name]['equations']:
            pending.extend(symbols(equation['rhs'],budget)-seen)
    return seen

def bind(task,budget,host):
    keys(task,('query','sources'),host)
    need(task['query']=='source_research_episode','source episode query',host)
    sources=task['sources'];need(type(sources) is list and len(sources)<=CAPS['sources'],'source record bound',host)
    checker=host.local_module('recursive_check');seen=set();total=0;rows=[];roots={}
    for ordinal,source in enumerate(sources):
        keys(source,('id','sha256','utf8'),host)
        name,pin,text=source['id'],source['sha256'],source['utf8']
        need(type(name) is str and IDENTIFIER.fullmatch(name) and name not in seen,'unique bounded source identifier',host)
        seen.add(name)
        need(type(pin) is str and HEX.fullmatch(pin) and type(text) is str,'source digest/text shape',host)
        try:raw=text.encode('utf-8')
        except UnicodeError as exc:raise host.Refused('source text is not UTF-8 encodable') from exc
        total+=len(raw)
        need(len(raw)<=CAPS['source_bytes'] and total<=CAPS['total_source_bytes'],'source byte bound',host)
        budget.use(len(raw));need(hashlib.sha256(raw).hexdigest()==pin,'source literal byte digest mismatch',host)
        value=decode(text,host);budget.use(len(raw))
        row=dict(source_id=name,source_sha256=pin,ordinal=ordinal,status='NOT_ADAPTED',
                 channel='UNKNOWN',reason='unsupported structured source format')
        fmt=value.get('format') if type(value) is dict else None
        if fmt=='pie-problem-v1':
            keys(value,('format','theory','goal'),host,('name','family','split'))
            metadata={k:value[k] for k in ('name','family','split') if k in value}
            need(all(type(v) is str and len(v)<=256 for v in metadata.values()),'source metadata string bound',host)
            keys(value['theory'],('format','definitions'),host)
            need(value['theory']['format']=='pie-theory-v1','source theory format',host)
            original=dict(query='prove_recursive_identity',domain='NatList',definitions=value['theory']['definitions'],goal=value['goal'])
            claim='question';pointer='/goal';row['metadata']=metadata
        elif fmt=='ember.recursive_claim.v1':
            keys(value,('format','task','claim'),host)
            need(type(value['claim']) is str and value['claim'] in ('question','holds','fails'),'source claim stance',host)
            original=value['task'];claim=value['claim'];pointer='/task/goal'
        else:
            rows.append(row);continue
        try:binding=checker.bind(original,budget)
        except checker.Invalid as exc:raise host.Refused('malformed supported source task: '+str(exc)) from exc
        identity=binding['identity']
        if identity not in roots:
            need(len(roots)<CAPS['roots'],'distinct adapted root bound',host)
            roots[identity]=dict(task_id=identity,task=copy.deepcopy(original),ordinal=ordinal,
                                 closure=sorted(closure(original,budget)),sources=[])
        else:need(roots[identity]['task']==original,'task identity collision',host)
        roots[identity]['sources'].append(name)
        row.update(status='ADAPTED',task_id=identity,claim=claim,pointer=pointer,
                   channel='SOURCE_QUESTION' if claim=='question' else 'SOURCE_CLAIM')
        row.pop('reason');rows.append(row)
    for root in roots.values():
        stances={row['claim'] for row in rows if row.get('task_id')==root['task_id']}
        root['tension']={'holds','fails'}<=stances
    return dict(sources=rows,roots=roots,source_bytes=total)

class Account:
    """Every attempted charge reaches the shared caller exactly once."""
    def __init__(self,parent,accounts,key,host,cap=None):
        self.parent=parent;self.accounts=accounts;self.key=key;self.host=host;self.work=0
        remaining=parent.limit-parent.work
        self.limit=max(0,min(remaining,cap if cap is not None else remaining))
    def use(self,amount=1):
        self.work+=amount
        if self.key=='common':self.accounts['common']+=amount
        else:self.accounts['roots'][self.key]+=amount
        self.parent.use(amount)
        if self.work>self.limit:raise self.host.Exhausted('source root/account allowance exhausted')

def admit(task,result,budget,host):
    checker=host.local_module('recursive_check')
    need(type(result) is dict and result.get('status') in CLOSED.values(),'checked original result required',host)
    try:checked=checker.check(task,result.get('certificate'),budget)
    except checker.Invalid as exc:raise host.Refused('original source evidence rejected: '+str(exc)) from exc
    need(result['status']==CLOSED[checked['kind']],'original source evidence/status mismatch',host)
    return dict(status=result['status'],certificate=copy.deepcopy(result['certificate']),check=checked)

def make_graph(binding,record,host,budget):
    if record['policy']=='native_isolated':return dict(nodes={},edges=[])
    nodes={};edges=[]
    def node(kind,content,channel,status):
        body=dict(type=kind,content=content,channel=channel,status=status,boundary='Original Nat and finite List(Nat), exact source span and full theory')
        identity=charged_digest(body,budget,host);nodes[identity]=body
        if len(nodes)>CAPS['nodes']:raise Capacity('outer source graph node limit')
        return identity
    def edge(kind,a,b,content=None):
        body=dict(type=kind,source=a,target=b,content=content or {})
        identity=charged_digest(body,budget,host)
        if not any(e['id']==identity for e in edges):edges.append(dict(id=identity,**body))
        if len(edges)>CAPS['edges']:raise Capacity('outer source graph edge limit')
    originals={identity:node('OriginalTask',dict(task_id=identity,task=root['task']),'UNKNOWN','BOUND')
               for identity,root in binding['roots'].items()}
    claims={}
    for source in binding['sources']:
        source_node=node('Source',dict(source_id=source['source_id'],sha256=source['source_sha256'],ordinal=source['ordinal']),'FACT','HASHED')
        if source['status']=='NOT_ADAPTED':
            gap=node('Gap',dict(source_id=source['source_id'],reason=source['reason']),'UNKNOWN','NOT_ADAPTED')
            edge('Failure',source_node,gap);continue
        claim=node('SourceClaim',dict(source_id=source['source_id'],task_id=source['task_id'],claim=source['claim'],pointer=source['pointer']),
                   'SOURCE_CLAIM' if source['claim']!='question' else 'UNKNOWN','ASSERTED' if source['claim']!='question' else 'REQUESTED')
        claims[source['source_id']]=claim;edge('ExtractedFrom',claim,source_node)
        edge({'holds':'Asserts','fails':'Denies','question':'Requests'}[source['claim']],claim,originals[source['task_id']])
    for i,left in enumerate(binding['sources']):
        for right in binding['sources'][i+1:]:
            if left.get('task_id') and left.get('task_id')==right.get('task_id') and {left.get('claim'),right.get('claim')}=={'holds','fails'}:
                edge('Tension',claims[left['source_id']],claims[right['source_id']],dict(scope='Source disagreement, not inconsistent mathematics'))
    evidence={}
    for identity in binding['roots']:
        root=record['roots'][identity]
        if root.get('result'):
            result=root['result'];ev=node('CheckedEvidence',dict(task_id=identity,status=result['status'],certificate_digest=host.digest(result['certificate'])),
                                        'FACT','CHECKED_ORIGINAL')
            evidence[identity]=ev;edge('CheckedUse',ev,originals[identity])
        else:
            gap=node('Gap',dict(task_id=identity,reason='original obligation unresolved'),'UNKNOWN','OPEN');edge('Prerequisite',gap,originals[identity])
    for bridge in record['bridges']:
        proposed=node('BridgeCandidate',bridge,'INFERENCE','PROPOSED')
        checked=node('CheckedBridge',bridge,'FACT','CHECKED_PREFIX')
        if bridge['source_task_id'] in evidence:edge('MechanismProvider',evidence[bridge['source_task_id']],proposed)
        edge('SynthesisCandidate',proposed,originals[bridge['receiver_task_id']]);edge('CheckedUse',checked,originals[bridge['receiver_task_id']])
    for attempt in record['attempts']:
        summary={k:attempt[k] for k in ('index','root_id','phase','status','allocation','work','context','native_id','seed_count','origin')}
        summary['attempt_digest']=charged_digest(attempt,budget,host)
        observed=node('Attempt',summary,'FACT','OBSERVED')
        edge('Measurement',observed,originals[attempt['root_id']])
        if attempt['status']=='UNKNOWN':edge('Failure',observed,originals[attempt['root_id']])
    stop=node('Stop',dict(reason=record['stop']),'UNKNOWN','STOPPED')
    for identity in originals:edge('Measurement',stop,originals[identity])
    return dict(nodes=nodes,edges=edges)

def protected(state,record,host):
    ids={record['task_id'],*record['native_ids']}
    owners={}
    for observation in state['observations']:
        if observation.get('kind')=='source_research_episode':
            ids.add(observation['task_id'])
            need(type(observation.get('native_ids')) is list,'source live-set shape',host)
            for identity in observation['native_ids']:
                need(type(identity) is str,'source live native identity',host)
                ids.add(identity);owners.setdefault(identity,set()).add(observation['task_id'])
    present={o['task_id']:o for o in state['observations']}
    need(len(present)==len(state['observations']),'duplicate instance observation identity',host)
    for identity in record['native_ids']:need(identity in present,'source live native record is missing',host)
    return {identity:host.canonical(present[identity]) for identity in ids if identity in present},owners

def merge_check(candidate,snapshot,owned,host):
    present={o['task_id']:o for o in candidate['observations']}
    if len(present)!=len(candidate['observations']):raise host.Refused('candidate duplicate observation')
    for identity,raw in snapshot.items():
        if identity not in present:raise Capacity('native checkpoint evicted protected live evidence')
        if identity not in owned and host.canonical(present[identity])!=raw:
            raise Capacity('native checkpoint changed protected foreign evidence')

def checkpoint(candidate,path,record,accounts,common,host):
    record['accounts']=copy.deepcopy(accounts)
    updated=copy.deepcopy(candidate)
    updated['observations']=[o for o in updated['observations'] if o['task_id']!=record['task_id']]+[copy.deepcopy(record)]
    if len(updated['observations'])>128:raise Capacity('outer checkpoint would evict a live observation')
    raw=host.canonical(updated).encode('utf-8')+b'\n';common.use(len(raw))
    updated['observations'][-1]['accounts']=copy.deepcopy(accounts)
    raw=host.canonical(updated).encode('utf-8')+b'\n'
    if len(raw)>host.STATE_LIMIT:raise Capacity('complete source checkpoint exceeds 1 MiB')
    if path is not None:
        target=Path(path);target.parent.mkdir(parents=True,exist_ok=True)
        temporary=target.with_suffix(target.suffix+'.tmp');temporary.write_bytes(raw);temporary.replace(target)
    return updated

def seed_records(binding,record,receiver,budget,host):
    originals=binding['roots'];task=originals[receiver]['task'];relevant=set(originals[receiver]['closure'])
    result=[];count=0;seen=set()
    for identity in record['commit_order']:
        root=record['roots'][identity];result0=root.get('result')
        if identity==receiver or root['origin']!='episode_started' or not result0 or result0['status']!='CHECKED_RECURSIVE_IDENTITY':continue
        original=originals[identity]['task']
        budget.use(len(host.canonical(original['definitions']).encode())+len(host.canonical(task['definitions']).encode()))
        if original['domain']!=task['domain'] or original['definitions']!=task['definitions']:continue
        certificate=result0['certificate'];signature=(identity,host.digest(certificate))
        if signature in seen:continue
        seen.add(signature);selected=[]
        entries=[item['goal'] for item in certificate['lemmas']]+[original['goal']]
        for index,goal in enumerate(entries):
            if count>=CAPS['candidates']:break
            if (symbols(goal['lhs'],budget)|symbols(goal['rhs'],budget))&relevant:
                selected.append(index);count+=1
        if selected:
            source_id=originals[identity]['sources'][0]
            result.append(dict(source_task=copy.deepcopy(original),source_certificate=copy.deepcopy(certificate),
                               selected_indices=selected,source_id=source_id,source_commit_id=root['commit_id']))
    return result

def select_next(binding,record,state,common,receiving_budget,host,score_enabled=True):
    """Inspect real saved residuals and rank; never solve or persist.

    The diagnostic ablation changes only the score used to sort. All inspected
    evidence, bridge eligibility, costs and reported matches remain the same.
    """
    need(type(score_enabled) is bool,'residual score switch must be Boolean',host)
    engine=host.local_module('recursive');policy=record['policy']
    unresolved=[k for k in binding['roots'] if not record['roots'][k].get('result')]
    diagnostics=[k for k in unresolved if not record['roots'][k]['diagnostic']] if policy=='gap_bridge' else []
    phase='diagnostic' if diagnostics else 'research';eligible=[]
    for key in (diagnostics[:1] if diagnostics else unresolved):
        account=receiving_budget(key)
        if account.limit<=0:continue
        original=binding['roots'][key];data=record['roots'][key]
        seeds=[] if phase=='diagnostic' or policy in ('native_isolated','graph_isolated') else seed_records(binding,record,key,common,host)
        context=engine.seed_context(original['task'],seeds,host,budget=common)
        allowance=min(receiving_budget(key).limit,200000 if phase=='diagnostic' else CAPS['root_work'])
        last=data['last']
        if last and last['phase']==phase and last['context']==context and allowance<=last['allocation']:continue
        score=0;matched=[];residual=None;candidates=[]
        if policy=='gap_bridge' and phase=='research':
            old_seeds=data['contexts'][-1]['seed_records'] if data['contexts'] else []
            inspection=engine.inspect_episode(original['task'],state,receiving_budget(key),host,
                                              seed_records=old_seeds,context_budget=common)
            residual=inspection['residual']
            prepared=engine.prepare_seeds(original['task'],seeds,receiving_budget(key),host)
            candidates=prepared['candidates']
            matching=engine.match_residual(residual,prepared,original['task'],common,host)
            score=matching['count'];matched=matching['matched_ids']
        ranking=dict(tension=bool(original['tension']),residual_matches=score,matched_ids=matched,
                     residual_present=residual is not None,closure_count=len(original['closure']),ordinal=original['ordinal'])
        allowance=min(receiving_budget(key).limit,200000 if phase=='diagnostic' else CAPS['root_work'])
        if allowance<=0:continue
        if last and last['phase']==phase and last['context']==context and allowance<=last['allocation']:continue
        eligible.append(dict(root_id=key,seed_records=seeds,context=context,allocation=allowance,
                             ranking=ranking,residual=residual,candidates=candidates))
    if policy=='gap_bridge' and phase=='research':
        eligible.sort(key=lambda item:(not item['ranking']['tension'],
            -item['ranking']['residual_matches'] if score_enabled else 0,
            item['ranking']['closure_count'],item['ranking']['ordinal']))
    else:eligible.sort(key=lambda item:item['ranking']['ordinal'])
    return dict(phase=phase,selected=eligible[0]['root_id'] if eligible else None,
                eligible=eligible,score_enabled=score_enabled)

def bridge_rows(receiver,native_id,context,prepared):
    return [dict(receiver_task_id=receiver,source_task_id=c['source_task_id'],
                 source_certificate_digest=c['source_certificate_digest'],entry_index=c['entry_index'],
                 candidate_id=c['id'],seed_context=context,native_id=native_id)
            for c in prepared.get('candidates',[])]

def native_summary(value):
    return {k:copy.deepcopy(value[k]) for k in ('episode_id','original_task_id','policy','totals','seed_count',
        'seed_context','node_count','edge_count','library_count','work','phase_work','executed','replayed_lemmas') if k in value}

def replay_contexts(binding,record,state,common,receiving_budget,host):
    """Reconstruct every live native context and every claimed checked bridge.

    Returns whether a validated native episode had advanced beyond its saved summary.
    """
    engine=host.local_module('recursive');native_ids=[];bridges=[];advanced=False
    latest={a['native_id']:a for a in record['attempts']}
    for key in binding['roots']:
        data=record['roots'][key]
        task=binding['roots'][key]['task']
        for saved in data['contexts']:
            keys(saved,('native_id','seed_records'),host)
            seeds=saved['seed_records'];need(type(seeds) is list,'stored bridge sources list',host)
            for seed in seeds:
                keys(seed,('source_task','source_certificate','selected_indices','source_id','source_commit_id'),host)
                source_key=host.local_module('recursive_check').bind(seed['source_task'],common)['identity']
                need(source_key in record['roots'],'bridge source outside this episode',host)
                source=record['roots'][source_key];original=binding['roots'][source_key]
                need(source['origin']=='episode_started' and source.get('result') and
                     source['result']['status']=='CHECKED_RECURSIVE_IDENTITY' and
                     seed['source_task']==original['task'] and
                     seed['source_certificate']==source['result']['certificate'] and
                     seed['source_id']==original['sources'][0] and seed['source_commit_id']==source.get('commit_id'),
                     'stored bridge source provenance changed',host)
            context=engine.seed_context(task,seeds,host,budget=common)
            inspection=engine.inspect_episode(task,state,receiving_budget(key),host,
                                              seed_records=seeds,context_budget=common)
            need(inspection['episode_id']==saved['native_id'] and inspection['record'] is not None,
                 'missing or changed live native context',host)
            native=inspection['record'];native_ids.append(saved['native_id'])
            prepared=inspection['seed_info']
            for row in bridge_rows(key,saved['native_id'],context,prepared):
                if row not in bridges:bridges.append(row)
            attempt=latest.get(saved['native_id'])
            need(attempt is not None and attempt['root_id']==key and attempt['context']==context,
                 'native context lacks matching acquisition attempt',host)
            need(attempt['seed_count']==native.get('seed_count',0),'saved bridge seed count changed',host)
            summary=attempt['native']
            need(attempt['origin']==data['origin'] and summary.get('episode_id')==saved['native_id'] and
                 summary.get('original_task_id')==key and summary.get('policy')=='residual',
                 'saved native attempt origin or binding changed',host)
            need(summary.get('seed_context')==context and summary.get('seed_count',0)==native.get('seed_count',0),
                 'saved native attempt seed context changed',host)
            for name in ('origins','candidates','skipped'):
                need(attempt['seed_info'].get(name,[])==prepared.get(name,[]),
                     'saved displayed seed provenance changed: '+name,host)
            refreshed={}
            for name,actual in (('totals',native['totals']),('library_count',len(native['library'])),
                                ('node_count',len(native['nodes'])),('edge_count',len(native['edges']))):
                if summary.get(name)!=actual:
                    refreshed[name]=[copy.deepcopy(summary.get(name)),copy.deepcopy(actual)]
                    summary[name]=copy.deepcopy(actual)
            if refreshed:
                # Another caller on this state advanced the shared native episode, for example a
                # standalone proof of the same question. inspect_episode just replayed that record,
                # so the outer summary follows it; stale counters are not evidence of tampering.
                attempt['native_refreshes']=(attempt.get('native_refreshes',[])+[refreshed])[-8:];advanced=True
            if data.get('result') and native.get('final_certificate'):
                need(native['final_certificate']==data['result']['certificate'],'outer/native original evidence differs',host)
    need(set(native_ids)==set(record['native_ids']) and len(native_ids)==len(set(native_ids)),
         'outer live native dependency set changed',host)
    need(sorted(bridges,key=host.canonical)==sorted(record['bridges'],key=host.canonical),
         'saved checked bridges do not reconstruct',host)
    return advanced

def _record(binding,identity,task,policy,gen):
    return dict(task_id=identity,kind='source_research_episode',schema='ember.source_episode.v1',
        task=copy.deepcopy(task),policy=policy,generation=gen,caps=dict(CAPS),
        roots={key:dict(origin=None,diagnostic=False,result=None,last=None,contexts=[]) for key in binding['roots']},
        native_ids=[],commit_order=[],bridges=[],attempts=[],action_count=0,
        accounts=dict(common=0,roots={key:0 for key in binding['roots']}),graph=dict(nodes={},edges=[]),stop='new episode')

def _validate(record,template,binding,host):
    need(type(record) is dict and set(record)==set(template),'source episode record fields',host)
    for name in ('task_id','kind','schema','task','policy','generation','caps'):
        need(record[name]==template[name],'source episode context changed',host)
    need(type(record['roots']) is dict and set(record['roots'])==set(binding['roots']),'source root set',host)
    accounts=record['accounts'];keys(accounts,('common','roots'),host)
    need(type(accounts['common']) is int and accounts['common']>=0 and type(accounts['roots']) is dict and set(accounts['roots'])==set(binding['roots']),
         'source work accounts',host)
    need(all(type(v) is int and v>=0 for v in accounts['roots'].values()),'source root work counts',host)
    for key,cap in (('native_ids',64),('commit_order',4),('bridges',8),('attempts',128)):
        need(type(record[key]) is list and len(record[key])<=cap,'source bounded '+key,host)
    need(type(record['action_count']) is int and 0<=record['action_count']<=64 and record['action_count']==len(record['attempts']),
         'source action count',host)
    need(len(set(record['native_ids']))==len(record['native_ids']) and len(set(record['commit_order']))==len(record['commit_order']),
         'duplicate source dependency',host)
    for identity,root in record['roots'].items():
        keys(root,('origin','diagnostic','result','last','contexts'),host,('commit_id',))
        need(root.get('origin') in (None,'episode_started','prior_continued','prior_replayed') and type(root.get('diagnostic')) is bool,
             'source root origin/status',host)
        need(type(root.get('contexts')) is list and len(root['contexts'])<=64,'source native contexts',host)
        if root.get('result'):
            need(identity in record['commit_order'] and root.get('commit_id')==host.digest(dict(task_id=identity,certificate=root['result'].get('certificate'))),
                 'source evidence commit identity',host)
    for index,attempt in enumerate(record['attempts']):
        need(type(attempt) is dict and attempt.get('index')==index and attempt.get('root_id') in binding['roots'] and
             type(attempt.get('work')) is int and attempt['work']>=0 and type(attempt.get('native')) is dict and
             type(attempt.get('native_id')) is str and type(attempt.get('seed_count')) is int and
             0<=attempt['seed_count']<=8,'source attempt binding',host)
        need(type(attempt.get('seed_info')) is dict and attempt.get('origin')==record['roots'][attempt['root_id']]['origin'],
             'source attempt provenance shape or origin',host)
    need(set(record['commit_order'])=={k for k,r in record['roots'].items() if r.get('result')},'source commit set',host)

def _answer(binding,record,status,reason,budget,accounts,baseline,started,executed,host,preserved=False):
    sources=[];roots=[]
    for source in binding['sources']:
        row=copy.deepcopy(source);result=record['roots'].get(source.get('task_id'),{}).get('result')
        if source['status']=='NOT_ADAPTED':row['assessment']='NOT_ADAPTED'
        elif not result:row['assessment']='UNKNOWN'
        elif source['claim']=='question':row['assessment']='ANSWERED'
        else:
            proof=result['status']=='CHECKED_RECURSIVE_IDENTITY'
            row['assessment']='SUPPORTED' if proof==(source['claim']=='holds') else 'CONTRADICTED'
        sources.append(row)
    for identity,root in binding['roots'].items():
        data=record['roots'][identity]
        roots.append(dict(task_id=identity,task=copy.deepcopy(root['task']),result=copy.deepcopy(data.get('result')),
                          origin=data['origin'],observed_fresh_this_call=identity in executed))
    invocation=dict(common=accounts['common']-baseline['common'],
                    roots={k:accounts['roots'][k]-baseline['roots'][k] for k in accounts['roots']})
    need(invocation['common']+sum(invocation['roots'].values())==budget.work,'internal disjoint work account mismatch',host)
    return dict(status=status,reason=reason,sources=sources,roots=roots,graph=copy.deepcopy(record['graph']),
        source_episode=dict(episode_id=record['task_id'],policy=record['policy'],generation=record['generation'],
            source_bytes=binding['source_bytes'],actions=record['action_count'],executed=executed,
            attempts=copy.deepcopy(record['attempts']),bridges=copy.deepcopy(record['bridges']),
            accounts=copy.deepcopy(accounts),persisted_accounts=copy.deepcopy(record['accounts']),checkpoint_preserved=preserved,
            unresolved=[key for key,r in record['roots'].items() if not r.get('result')]),
        work_accounts=invocation,work=budget.work,elapsed_ns=time.perf_counter_ns()-started)

def run(task,state_path,limit,host,policy='gap_bridge',steps=8):
    need(policy in POLICIES,'source policy',host)
    need(type(steps) is int and 1<=steps<=64,'source steps must be 1..64',host)
    need(type(limit) is int and limit>=0,'source work allowance',host)
    started=time.perf_counter_ns();budget=host.Budget(limit);binding=None;record=None;stable=None;executed=[];replayed=False
    checker=host.local_module('recursive_check');engine=host.local_module('recursive')
    try:
        binding=bind(task,budget,host);gen=generation()
        identity=charged_digest(dict(kind='source_research_episode',task=task,policy=policy,caps=CAPS,generation=gen),budget,host)
        intake_work=budget.work;state=host.read_state(state_path)
        template=_record(binding,identity,task,policy,gen)
        previous=next((o for o in state['observations'] if o['task_id']==identity),None)
        if previous is not None:_validate(previous,template,binding,host)
        record=copy.deepcopy(previous or template);stable=copy.deepcopy(record)
        accounts=copy.deepcopy(record['accounts']);baseline=copy.deepcopy(accounts)
        historical=accounts['common']+sum(accounts['roots'].values());accounts['common']+=intake_work
        budget.limit=min(limit,max(0,CAPS['root_work']*len(binding['roots'])-historical)) if binding['roots'] else limit
        budget.use(0);common=Account(budget,accounts,'common',host)
        def root_budget(key,cap=None):
            remaining=max(0,CAPS['root_work']-accounts['roots'][key])
            return Account(budget,accounts,key,host,min(remaining,cap) if cap is not None else remaining)
        # Reconstruct original mathematical evidence before trusting a saved outer result.
        for key in binding['roots']:
            data=record['roots'][key]
            if data.get('result'):data['result']=admit(binding['roots'][key]['task'],data['result'],root_budget(key),host)
        if previous is not None:
            advanced=replay_contexts(binding,record,state,common,root_budget,host)
            rebuilt=make_graph(binding,record,host,common)
            # The graph is derived from the replayed record; after validated outside progress it is rebuilt.
            if advanced:record['graph']=rebuilt
            else:need(rebuilt==record['graph'],'saved typed source graph does not reconstruct',host)
        replayed=True
        reason='bounded source steps complete'
        for _ in range(steps):
            unresolved=[key for key,data in record['roots'].items() if not data.get('result')]
            if not unresolved:reason='all adapted original obligations settled';break
            if record['action_count']>=CAPS['actions']:raise Capacity('source action cap')
            if budget.work>=budget.limit:raise host.Exhausted('shared source episode allowance exhausted')
            selection=select_next(binding,record,state,common,root_budget,host)
            if selection['selected'] is None:reason='no eligible changed seed context or larger allocation';break
            chosen=selection['eligible'][0];key=chosen['root_id'];seeds=chosen['seed_records'];context=chosen['context']
            phase=selection['phase'];allowance=chosen['allocation'];rank=chosen['ranking']
            original=binding['roots'][key];data=record['roots'][key]
            native_id=engine.episode_id(original['task'],host,seed_records=seeds,budget=common)
            snapshot,owners=protected(state,record,host)
            need(not (owners.get(native_id,set())-{identity}),'native episode ownership conflict',host)
            if data['origin'] is None:
                existing=next((o for o in state['observations'] if o['task_id']==native_id),None)
                data['origin']='prior_replayed' if existing and existing.get('final_certificate') else 'prior_continued' if existing else 'episode_started'
            candidate=copy.deepcopy(state);root_call=root_budget(key,allowance);allowance=root_call.limit;before=budget.work
            new_evidence=False
            try:
                result=engine.run(original['task'],candidate,None,root_call,host,policy='residual',
                                  steps=1 if phase=='diagnostic' else 64,seed_records=seeds,context_budget=common)
                if result['status'] in CLOSED.values():
                    admitted=admit(original['task'],result,root_call,host)
                    old=data.get('result')
                    if old and old['status']!=admitted['status']:raise host.Refused('opposite checked original verdicts')
                    data['result']=admitted;data['commit_id']=host.digest(dict(task_id=key,certificate=admitted['certificate']))
                    if key not in record['commit_order']:record['commit_order'].append(key)
                    if data['origin']=='episode_started':new_evidence=True
            except engine.SearchLimit as exc:result=dict(status='UNKNOWN',reason=str(exc))
            merge_check(candidate,snapshot,{identity,native_id},host)
            present=next((o for o in candidate['observations'] if o['task_id']==native_id),None)
            if present is not None:
                # Native run validated the owned record it produced. Keep its exact context for fresh replay.
                if native_id not in record['native_ids']:record['native_ids'].append(native_id)
                if not any(c['native_id']==native_id for c in data['contexts']):
                    data['contexts'].append(dict(native_id=native_id,seed_records=copy.deepcopy(seeds)))
            if phase=='diagnostic':data['diagnostic']=True
            data['last']=dict(phase=phase,context=context,allocation=allowance)
            info=result.get('recursive',{}).get('seed_info',{})
            for bridge in bridge_rows(key,native_id,context,info) if present is not None else []:
                if bridge not in record['bridges']:record['bridges'].append(bridge)
            if len(record['bridges'])>CAPS['candidates']:raise Capacity('outer checked bridge bound')
            attempt=dict(index=record['action_count'],root_id=key,phase=phase,status=result['status'],
                allocation=allowance,work=budget.work-before,context=context,ranking=rank,
                eligible_ranking=[dict(root_id=item['root_id'],**item['ranking']) for item in selection['eligible']],
                native_id=native_id,seed_count=result.get('recursive',{}).get('seed_count',0),
                seed_info={k:copy.deepcopy(info[k]) for k in ('origins','candidates','skipped','work','phase_work') if k in info},
                native=native_summary(result.get('recursive',{})),origin=data['origin'])
            record['attempts'].append(attempt);record['action_count']+=1
            record['stop']='bounded source steps complete';record['graph']=make_graph(binding,record,host,common)
            state=checkpoint(candidate,state_path,record,accounts,common,host)
            record=copy.deepcopy(next(o for o in state['observations'] if o['task_id']==identity))
            stable=copy.deepcopy(record)
            if new_evidence:executed.append(key)
        complete=bool(binding['sources']) and all(s['status']=='ADAPTED' for s in binding['sources']) and all(r.get('result') for r in record['roots'].values())
        if not binding['roots']:reason='no adapted original tasks'
        elif any(s['status']=='NOT_ADAPTED' for s in binding['sources']):reason='unsupported source remains an explicit format gap'
        record['stop']=reason;record['graph']=make_graph(binding,record,host,common)
        # Persist successful replay accounting and explicit no-work gaps atomically.
        state=checkpoint(state,state_path,record,accounts,common,host)
        record=copy.deepcopy(next(o for o in state['observations'] if o['task_id']==identity));stable=copy.deepcopy(record)
        return _answer(binding,record,'CHECKED_SOURCE_EPISODE' if complete else 'UNKNOWN',reason,budget,accounts,baseline,started,executed,host)
    except (host.Exhausted,checker.Limit,engine.SearchLimit,Capacity) as exc:
        if binding is None or record is None:
            return dict(status='UNKNOWN',reason=str(exc),sources=[] if binding is None else binding['sources'],roots=[],
                        graph=dict(nodes={},edges=[]),work_accounts=dict(common=budget.work,roots={}),
                        work=budget.work,elapsed_ns=time.perf_counter_ns()-started)
        response=copy.deepcopy(stable)
        if not replayed:
            for root in response['roots'].values():root['result']=None
            response['graph']=dict(nodes={},edges=[])
        return _answer(binding,response,'UNKNOWN',str(exc),budget,accounts,baseline,started,executed,host,True)
    except checker.Invalid as exc:raise host.Refused('invalid source/seed/native evidence: '+str(exc)) from exc
