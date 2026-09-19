"""Bounded rational polynomial proposals and TPM-style guard search.

The checker is supplied by the owned runtime; this module does not admit its own
expanded coefficients as proof. No donor module, model or network is loaded.
"""
import ast
import copy
from fractions import Fraction as Q
import itertools
import math


def checked_size(poly,checker):
    out={e:q for e,q in poly.items() if q}
    if len(out)>2048: raise checker.Limit('sparse expansion term limit')
    for q in out.values(): checker.bounded(q)
    return out


def add(a,b,budget,checker):
    out=dict(a)
    for e,q in b.items(): budget.use(); out[e]=out.get(e,Q(0))+q
    return checked_size(out,checker)


def multiply(a,b,budget,checker):
    if len(a)*len(b)>100_000: raise checker.Limit('sparse product limit')
    out={}
    for e,q in a.items():
        for f,r in b.items():
            budget.use(2); key=tuple(x+y for x,y in zip(e,f))
            out[key]=out.get(key,Q(0))+q*r
    return checked_size(out,checker)


def expand(node,names,budget,checker):
    budget.use(); zero=(0,)*len(names)
    if type(node) is ast.Constant: return {zero:Q(node.value)} if node.value else {}
    if type(node) is ast.Name: return {tuple(int(node.id==v) for v in names):Q(1)}
    if type(node) is ast.UnaryOp:
        a=expand(node.operand,names,budget,checker)
        return {e:(-q if type(node.op) is ast.USub else q) for e,q in a.items()}
    a=expand(node.left,names,budget,checker)
    if type(node.op) is ast.Pow:
        result={zero:Q(1)}
        for _ in range(node.right.value): result=multiply(result,a,budget,checker)
        return result
    if type(node.op) is ast.Div:
        budget.use(len(a)); return checked_size({e:q/node.right.value for e,q in a.items()},checker)
    b=expand(node.right,names,budget,checker)
    if type(node.op) is ast.Add: return add(a,b,budget,checker)
    if type(node.op) is ast.Sub: return add(a,{e:-q for e,q in b.items()},budget,checker)
    if type(node.op) is ast.Mult: return multiply(a,b,budget,checker)
    raise checker.Invalid('unvalidated producer syntax')


def evaluate(poly,point,budget,checker):
    total=Q(0)
    for powers,c in poly.items():
        for exponent,x in zip(powers,point): budget.use(); c=checker.bounded(c*x**exponent)
        budget.use(); total=checker.bounded(total+c)
    return total


def encoded(poly):
    return [[list(e),[q.numerator,q.denominator]] for e,q in sorted(poly.items()) if q]


def point_data(point):
    return [[Q(x).numerator,Q(x).denominator] for x in point]


def affine_model(gs,n,budget,checker):
    """Parameterize only the affine subset; every proposed point is rechecked.

    Row operations are exact search arithmetic, not an admission certificate.
    A nonlinear equation is never discarded from original-task checking.
    """
    rows=[]; selected=[]; zero=(0,)*n
    for index,g in enumerate(gs):
        affine=True
        for e in g:
            budget.use()
            if sum(e)>1: affine=False; break
        if not affine: continue
        row=[g.get(tuple(int(i==j) for i in range(n)),Q(0)) for j in range(n)]
        row.append(-g.get(zero,Q(0)))
        budget.use(n+1)
        if any(row): rows.append(row); selected.append(index)
    rank=0; pivots=[]
    for column in range(n):
        found=None
        for i in range(rank,len(rows)):
            budget.use()
            if rows[i][column]: found=i; break
        if found is None: continue
        rows[rank],rows[found]=rows[found],rows[rank]
        scale=rows[rank][column]
        for j in range(column,n+1):
            budget.use(); rows[rank][j]=checker.bounded(rows[rank][j]/scale)
        for i,row in enumerate(rows):
            budget.use()
            if i==rank or not row[column]: continue
            factor=row[column]
            for j in range(column,n+1):
                budget.use(2); row[j]=checker.bounded(row[j]-factor*rows[rank][j])
        pivots.append(column); rank+=1
    inconsistent=False
    for row in rows:
        budget.use(n+1)
        if not any(row[:-1]) and row[-1]: inconsistent=True
    return {'rows':rows[:rank],'pivots':pivots,
        'free':[i for i in range(n) if i not in pivots],
        'rank':rank,'affine_indices':selected,'consistent':not inconsistent,
        'active':bool(selected)}


def probe_points(model,n,values,budget,checker):
    """Finite integer assignments to free variables reconstruct rational points."""
    if not model['consistent']: return
    if not model['active']:
        yield from itertools.product(values,repeat=n)
        return
    for free_values in itertools.product(values,repeat=len(model['free'])):
        point=[Q(0)]*n
        for i,q in zip(model['free'],free_values): point[i]=Q(q)
        for pivot,row in zip(model['pivots'],model['rows']):
            q=row[-1]
            for j in model['free']:
                budget.use(2); q=checker.bounded(q-row[j]*point[j])
            point[pivot]=checker.bounded(q)
        yield tuple(point)


def affine_substitute(poly,model,n,budget,checker):
    """Compose a proposal residual with an affine parameterization, without admission."""
    zero=(0,)*n; substitutions={}; cache={}
    for pivot,row in zip(model['pivots'],model['rows']):
        replacement={zero:row[-1]} if row[-1] else {}
        for i in model['free']:
            if row[i]: replacement[tuple(int(j==i) for j in range(n))]=-row[i]
        substitutions[pivot]=replacement
    for i in model['free']:
        substitutions[i]={tuple(int(j==i) for j in range(n)):Q(1)}
    def power(i,k):
        if (i,k) not in cache:
            value={zero:Q(1)}
            for _ in range(k): value=multiply(value,substitutions[i],budget,checker)
            cache[i,k]=value
        return cache[i,k]
    result={}
    for e,q in sorted(poly.items()):
        term={zero:q}
        for i,k in enumerate(e):
            if k: term=multiply(term,power(i,k),budget,checker)
        result=add(result,term,budget,checker)
    return result


def monomials(n,d):
    out=[(0,)*n]
    for k in range(1,d+1):
        for combo in itertools.combinations_with_replacement(range(n),k):
            e=[0]*n
            for i in combo: e[i]+=1
            out.append(tuple(e))
    return out


def combination(goal,gs,n,d,budget,checker,basis=None):
    if basis is None: basis=monomials(n,d)
    else:
        checker.need(type(basis) in (list,tuple) and len(basis)<=384,'explicit proposal basis bound')
        seen=set()
        for powers in basis:
            budget.use(n+1)
            checker.need(type(powers) in (list,tuple) and len(powers)==n and
                all(type(k) is int and 0<=k<=d for k in powers) and sum(powers)<=d,
                'explicit proposal monomial bounds')
            key=tuple(powers); checker.need(key not in seen,'duplicate explicit proposal monomial'); seen.add(key)
        basis=[tuple(powers) for powers in basis]
    columns=[]; labels=[]
    for i,g in enumerate(gs):
        for e in basis:
            budget.use(len(g)); columns.append({tuple(a+b for a,b in zip(e,m)):c for m,c in g.items()})
            labels.append((i,e))
    if len(columns)>384: raise checker.Limit('linear proposal column limit')
    rows=sorted(set(goal).union(*(set(p) for p in columns)))
    if len(rows)>512: raise checker.Limit('linear proposal row limit')
    pivots={}; width=len(columns)
    for monomial in rows:
        budget.use(width+1)
        row=[p.get(monomial,Q(0)) for p in columns]+[goal.get(monomial,Q(0))]
        for i,prior in sorted(pivots.items()):
            c=row[i]
            if c:
                for j in range(i,width+1):
                    budget.use(2); row[j]=checker.bounded(row[j]-c*prior[j])
        lead=next((i for i,q in enumerate(row[:-1]) if q),None)
        if lead is None:
            if row[-1]: return None
        else:
            c=row[lead]
            for j in range(lead,width+1): budget.use(); row[j]=checker.bounded(row[j]/c)
            pivots[lead]=row
    solution=[Q(0)]*width
    for i,row in sorted(pivots.items(),reverse=True):
        q=row[-1]
        for j in range(i+1,width): budget.use(2); q=checker.bounded(q-row[j]*solution[j])
        solution[i]=q
    result=[{} for _ in gs]
    for (i,e),q in zip(labels,solution):
        if q: result[i][e]=q
    return result


def consequence(task,budget,checker,require_support=False,proposal_policy='full'):
    checker.need(proposal_policy in ('full','target_sparse','cancellation_sparse'),'polynomial proposal policy')
    binding=checker.bind(task); names=binding['names']
    goal=expand(binding['goal'],names,budget,checker)
    gs=[expand(g,names,budget,checker) for g in binding['generators']]
    nz=[expand(g,names,budget,checker) for g in binding['nonzero']]
    values=[0]+[x for k in range(1,binding['radius']+1) for x in (k,-k)]
    model=affine_model(gs,len(names),budget,checker)
    search={'method':'affine_rref_free_integer_grid' if model['active'] else 'integer_grid',
        'affine_equations':len(model['affine_indices']),'affine_rank':model['rank'],
        'affine_consistent':model['consistent'],'free_variables':[names[i] for i in model['free']],
        'candidate_bound':len(values)**len(model['free']) if model['consistent'] else 0}
    support=None; probes=0
    # Observations eliminate conjectures; failure to find one proves nothing.
    for point in probe_points(model,len(names),values,budget,checker):
        probes+=1; budget.use()
        if any(evaluate(g,point,budget,checker)!=0 for g in gs): continue
        if any(evaluate(g,point,budget,checker)==0 for g in nz): continue
        if support is None: support=point_data(point)
        if evaluate(goal,point,budget,checker)!=0:
            cert={'kind':'rational_counterexample','task_id':binding['identity'],'point':point_data(point)}
            checked=checker.check(task,cert,budget)
            return {'status':'CHECKED_COUNTEREXAMPLE','certificate':cert,'check':checked,'probes':probes,
                'point_search':search}
    if require_support and support is None:
        return {'status':'UNKNOWN','reason':'no admissible support point within the finite probe grid',
            'probes':probes,'point_search':search}
    sparse=None
    if proposal_policy!='full':
        result,sparse=sparse_proposal(task,binding,goal,gs,support,budget,checker,proposal_policy)
        if result is not None:
            result.update(probes=probes,point_search=search); return result
    fallback_start=budget.work
    fallback_budget=(SparseBudget(budget,max(0,budget.limit-budget.work)) if sparse is not None else budget)
    try:
        result=None
        for d in range(binding['degree']+1):
            proposal=combination(goal,gs,len(names),d,fallback_budget,checker)
            if proposal is None: continue
            cert={'kind':'polynomial_combination','task_id':binding['identity'],
                'multipliers':[encoded(p) for p in proposal]}
            if support is not None: cert['support_point']=support
            checked=checker.check(task,cert,fallback_budget)
            result={'status':'CHECKED_IMPLICATION','certificate':cert,'check':checked,
                'multiplier_degree_used':d}
            break
        if result is None:
            result={'status':'UNKNOWN','reason':'bounded polynomial combination search failed; finite probes are not a proof'}
    except checker.Limit as exc:
        if sparse is None: raise
        result={'status':'UNKNOWN','reason':str(exc)}
    except SparseBudgetEnded:
        result={'status':'UNKNOWN','reason':'full fallback exhausted remaining work budget'}
    if sparse is not None:
        sparse['fallback']=True; sparse['fallback_work']=budget.work-fallback_start
        result['sparse_search']=sparse
    result.update(probes=probes,point_search=search)
    return result


class LemmaBudgetEnded(RuntimeError): pass


class LemmaBudget:
    """A charged slice of the caller's budget, retaining a direct fallback."""
    def __init__(self,parent,limit): self.parent=parent; self.limit=limit; self.work=0
    def use(self,amount=1):
        if self.work+amount>self.limit: raise LemmaBudgetEnded('reserved lemma search budget exhausted')
        self.parent.use(amount); self.work+=amount


class SparseBudgetEnded(RuntimeError): pass


class SparseBudget(LemmaBudget):
    def use(self,amount=1):
        if self.work+amount>self.limit: raise SparseBudgetEnded('reserved sparse proposal budget exhausted')
        self.parent.use(amount); self.work+=amount


SPARSE_PAIR_CAP=4096
SPARSE_BASIS_CAP=64
SPARSE_WORK_CAP=50_000


def sparse_basis(goal,gs,n,d,budget,checker,policy,report=None):
    """Bounded exponent differences propose a basis; missing terms prove nothing."""
    checker.need(policy in ('target_sparse','cancellation_sparse'),'sparse proposal policy')
    zero=(0,)*n; basis={zero}; generator_terms=set()
    cap=min(SPARSE_BASIS_CAP,384//max(1,len(gs)))
    if report is None: report={}
    report.update({'policy':policy,'pair_cap':SPARSE_PAIR_CAP,'basis_cap':cap,'pair_visits':0,
            'target_pair_visits':0,'cancellation_pair_visits':0,'truncated':False,
            'generation_complete':True,'duplicate_candidates':0,'candidates_added':0,
            'candidate_count':1,'maximum_columns':len(gs)})
    for g in gs:
        for powers in g: budget.use(); generator_terms.add(powers)
    terms=sorted(generator_terms); report['unique_generator_terms']=len(terms)
    def offer(p,q,phase):
        if report['pair_visits']>=SPARSE_PAIR_CAP:
            report.update(truncated=True,generation_complete=False,stop_reason='pair visit cap'); return False
        budget.use(n+1); report['pair_visits']+=1; report[phase+'_pair_visits']+=1
        delta=tuple(x-y for x,y in zip(p,q))
        if any(k<0 for k in delta) or sum(delta)>d: return True
        if delta in basis: report['duplicate_candidates']+=1; return True
        if len(basis)>=cap:
            report.update(truncated=True,generation_complete=False,stop_reason='candidate monomial cap'); return False
        basis.add(delta); report['candidates_added']+=1
        report.update(candidate_count=len(basis),maximum_columns=len(basis)*len(gs)); return True
    def finish():
        ordered=sorted(basis,key=lambda powers:(sum(powers),powers))
        report.update(candidate_count=len(ordered),basis=[list(p) for p in ordered],
                      maximum_columns=len(ordered)*len(gs))
        return ordered,report
    for p in sorted(goal):
        for q in terms:
            if not offer(p,q,'target'): return finish()
    if policy=='cancellation_sparse':
        for p in terms:
            for q in terms:
                if not offer(p,q,'cancellation'): return finish()
    return finish()


def sparse_proposal(task,binding,goal,gs,support,budget,checker,policy):
    allowance=min(SPARSE_WORK_CAP,max(0,(budget.limit-budget.work)//5))
    part=SparseBudget(budget,allowance)
    report={'policy':policy,'work_allowance':allowance,'work':0,'generation_work':0,
        'proposal_work':0,'checking_work':0,'failed_sparse_work':0,'fallback':False,
        'fallback_work':0,'attempts':[]}
    phase='generation'; started=0; result=None
    try:
        report['generation']={}
        basis,_=sparse_basis(goal,gs,len(binding['names']),binding['degree'],part,checker,policy,report['generation'])
        report['generation_work']=part.work
        for degree in range(binding['degree']+1):
            chosen=[p for p in basis if sum(p)<=degree]
            attempt={'degree':degree,'candidate_count':len(chosen),'columns':len(gs)*len(chosen),
                     'status':'started','work':0}
            report['attempts'].append(attempt); phase='proposal'; started=part.work
            proposal=combination(goal,gs,len(binding['names']),degree,part,checker,basis=chosen)
            attempt['work']=part.work-started; report['proposal_work']+=attempt['work']
            if proposal is None:
                attempt['status']='no_combination'; continue
            cert=flat_certificate(task,proposal,checker)
            if support is not None: cert['support_point']=support
            phase='checking'; started=part.work
            checked=checker.check(task,cert,part)
            report['checking_work']+=part.work-started; attempt['status']='checked'
            result={'status':'CHECKED_IMPLICATION','certificate':cert,'check':checked,
                    'multiplier_degree_used':degree,'proof_method':'sparse_polynomial_combination',
                    'sparse_search':report}
            break
    except (SparseBudgetEnded,checker.Limit) as exc:
        report['reason']=str(exc)
        if phase=='generation':
            report['generation_work']=part.work
            report['generation'].update(generation_complete=False,truncated=True,stop_reason=str(exc))
        elif phase=='proposal':
            report['attempts'][-1].update(status='interrupted',work=part.work-started)
            report['proposal_work']+=part.work-started
        else:
            report['attempts'][-1]['status']='check_interrupted'
            report['checking_work']+=part.work-started
    finally:
        report['work']=part.work
        report['failed_sparse_work']=(part.work if result is None else
            sum(a['work'] for a in report['attempts'] if a['status']!='checked'))
    return result,report


def renamed_expression(text,mapping,budget):
    class Rename(ast.NodeTransformer):
        def visit_Name(self,node):
            budget.use()
            return ast.copy_location(ast.Name(id=mapping[node.id],ctx=ast.Load()),node)
    tree=ast.parse(text,mode='eval')
    budget.use(sum(1 for _ in ast.walk(tree)))
    return ast.unparse(Rename().visit(tree).body)


def flat_certificate(task,multipliers,checker):
    return {'kind':'polynomial_combination','task_id':checker.bind(task)['identity'],
            'multipliers':[encoded(p) for p in multipliers]}


def fits_certificate(polys,d):
    return all(len(p)<=256 and all(sum(e)<=d for e in p) for p in polys)


def guarded_certificate(task,multipliers,nonzero_index,checker):
    return {'kind':'localized_polynomial_combination','task_id':checker.bind(task)['identity'],
            'nonzero_index':nonzero_index,'multipliers':[encoded(p) for p in multipliers]}


def receiving_guard_index(mapped_binding,receiving,index,budget,checker):
    """The first exact original guard AST match, never inferred nonzeroness."""
    wanted=ast.dump(mapped_binding['nonzero'][index],include_attributes=False)
    for position,node in enumerate(receiving['nonzero']):
        budget.use()
        if ast.dump(node,include_attributes=False)==wanted:return position
    raise checker.Invalid('mapped selected nonzero guard absent from original receiving task')


def transport_lemma(task,record,mapping,budget,checker,allow_guarded=False):
    """Produce a checked receiving-context lemma, never a new original axiom."""
    checker.need(type(allow_guarded) is bool,'guarded transport option must be Boolean')
    receiving=checker.bind(task); names=receiving['names']; n=len(names)
    checker.need(type(record) is dict and type(record.get('task')) is dict,'lemma requires original source task')
    source=record['task']; sb=checker.bind(source)
    checker.need(source['query']=='polynomial_consequence','source lemma must be a polynomial consequence')
    certificate=record.get('certificate')
    checker.need(type(certificate) is dict and (certificate.get('kind')=='polynomial_combination' or
        allow_guarded and certificate.get('kind')=='localized_polynomial_combination'),'flat polynomial lemma certificate required unless guarded transfer is enabled')
    guarded=certificate['kind']=='localized_polynomial_combination'
    graph_keys=('dependencies','dependency_ids','parents','proof_graph','lemmas','source_refs')
    checker.need(not any(record.get(key) or certificate.get(key) for key in graph_keys),
                 'proof graph references are unsupported; a self-contained flat proof is required')
    checker.need(type(mapping) is dict and set(mapping)==set(sb['names']) and
        all(type(v) is str and v in names for v in mapping.values()) and
        len(set(mapping.values()))==len(mapping),'injective complete variable binding required')
    source_check=checker.check(source,certificate,budget)
    # Reparse renamed syntax; coefficients and unused receiving variables retain QQ.
    mapped={k:copy.deepcopy(v) for k,v in source.items() if k not in ('name','family')}
    mapped['variables']=list(names)
    mapped['goal']=renamed_expression(source['goal'],mapping,budget)
    for key in ('assumptions','nonzero'):
        mapped[key]=[renamed_expression(s,mapping,budget) for s in source.get(key,[])]
    mb=checker.bind(mapped)
    nz={ast.dump(g,include_attributes=False) for g in receiving['nonzero']}
    checker.need(all(ast.dump(g,include_attributes=False) in nz for g in mb['nonzero']),
                 'mapped nonzero premise is not present in receiving task')
    renamed=[]
    for raw in certificate['multipliers']:
        polynomial={}
        for powers,q in checker.multiplier_read(raw,len(sb['names']),sb['degree']):
            budget.use(n); new=[0]*n
            for i,power in enumerate(powers): new[names.index(mapping[sb['names'][i]])]=power
            polynomial[tuple(new)]=q
        renamed.append(polynomial)
    receiver_index=(receiving_guard_index(mb,receiving,certificate['nonzero_index'],budget,checker) if guarded else None)
    mapped_certificate=(guarded_certificate(mapped,renamed,certificate['nonzero_index'],checker) if guarded else
                        flat_certificate(mapped,renamed,checker))
    if guarded and certificate.get('support_point') is not None:
        point=checker.point_read(certificate['support_point'],sb); transported=[Q(0)]*n
        for name,value in zip(sb['names'],point):budget.use();transported[names.index(mapping[name])]=value
        mapped_certificate['support_point']=point_data(transported)
    mapped_check=checker.check(mapped,mapped_certificate,budget)
    generators=[expand(g,names,budget,checker) for g in receiving['generators']]
    premises=[]; discharged=[]; zero=(0,)*n
    for expression,node in zip(mapped['assumptions'],mb['generators']):
        goal=expand(node,names,budget,checker); proposal=None
        # Exact generator correspondence avoids rebuilding an equivalent search.
        for j,g in enumerate(generators):
            budget.use()
            if g==goal:
                proposal=[{} for _ in generators]; proposal[j]={zero:Q(1)}; break
        if proposal is None:
            for d in range(receiving['degree']+1):
                proposal=combination(goal,generators,n,d,budget,checker)
                if proposal is not None: break
        if proposal is None: raise checker.Invalid('source equation was not proved from receiving equations')
        premise_task={**task,'goal':expression}
        premise_certificate=flat_certificate(premise_task,proposal,checker)
        checked=checker.check(premise_task,premise_certificate,budget)
        premises.append(proposal); discharged.append({'task':premise_task,'certificate':premise_certificate,'check':checked})
    flattened=[{} for _ in generators]
    for h,coefficients in zip(renamed,premises):
        for j,k in enumerate(coefficients):
            flattened[j]=add(flattened[j],multiply(h,k,budget,checker),budget,checker)
    checker.need(fits_certificate(flattened,receiving['degree']),'transported lemma exceeds original certificate bounds')
    lemma_task={**task,'goal':mapped['goal']}
    lemma_certificate=(guarded_certificate(lemma_task,flattened,receiver_index,checker) if guarded else
                       flat_certificate(lemma_task,flattened,checker))
    lemma_check=checker.check(lemma_task,lemma_certificate,budget)
    result={'polynomial':expand(mb['goal'],names,budget,checker),
            'source_task_id':sb['identity'],'mapping':dict(mapping),'source_check':source_check,
            'mapped_task':mapped,'mapped_certificate':mapped_certificate,'mapped_check':mapped_check,
            'premise_discharges':discharged,'task':lemma_task,'certificate':lemma_certificate,'check':lemma_check}
    if guarded:
        result.update(guarded_multipliers=flattened,receiving_nonzero_index=receiver_index,
            guard_polynomial=expand(receiving['nonzero'][receiver_index],names,budget,checker))
    else:result['multipliers']=flattened
    return result


def lemma_bindings(source_names,names):
    """Deterministic candidate order; mapping failure has no logical consequence."""
    if len(source_names)>len(names): return
    seen=set()
    if all(name in names for name in source_names):
        values=tuple(source_names); seen.add(values); yield dict(zip(source_names,values))
    for values in itertools.permutations(names,len(source_names)):
        if values not in seen:
            seen.add(values); yield dict(zip(source_names,values))


def reuse_lemma(task,records,budget,checker,diagnostics=None,allow_guarded=False):
    """One flat stored lemma per attempt; admission remains the original checker."""
    checker.need(type(allow_guarded) is bool,'guarded reuse option must be Boolean')
    b=checker.bind(task); names=b['names']; attempts=0
    if diagnostics is None: diagnostics=[]
    goal=expand(b['goal'],names,budget,checker)
    generators=[expand(g,names,budget,checker) for g in b['generators']]
    for record in list(records)[:8]:
        try:
            budget.use()
            checker.need(type(record) is dict and type(record.get('task')) is dict,'lemma source task missing')
            sb=checker.bind(record['task'])
            if sb['identity']==b['identity']: continue
            for mapping in lemma_bindings(sb['names'],names):
                if attempts>=16: return None,diagnostics
                attempts+=1
                entry={'source_task_id':sb['identity'],'mapping':mapping,'outcome':'started'}
                diagnostics.append(entry)
                try:
                    transported=transport_lemma(task,record,mapping,budget,checker,allow_guarded=allow_guarded)
                    guarded=transported['check']['kind']=='localized_polynomial_combination'
                    coefficients=transported['guarded_multipliers'] if guarded else transported['multipliers']
                    for basis_name,basis in [('lemma_only',[transported['polynomial']]),
                            ('lemma_and_original',[transported['polynomial'],*generators])]:
                        for degree in range(b['degree']+1):
                            outer=combination(goal,basis,len(names),degree,budget,checker)
                            if outer is None or not outer[0]: continue
                            if basis_name=='lemma_only': outer=outer+[{} for _ in generators]
                            flattened=[add(multiply(transported['guard_polynomial'],r,budget,checker) if guarded else r,
                                           multiply(outer[0],u,budget,checker),budget,checker)
                                       for r,u in zip(outer[1:],coefficients)]
                            if not fits_certificate(flattened,b['degree']):
                                entry['reason']='flattened target exceeds original certificate bounds'
                                continue
                            cert=(guarded_certificate(task,flattened,transported['receiving_nonzero_index'],checker) if guarded else
                                  flat_certificate(task,flattened,checker))
                            checked=checker.check(task,cert,budget)
                            entry['outcome']='used'
                            return {'status':'CHECKED_IMPLICATION','certificate':cert,'check':checked,
                                'proof_method':'transferred_guarded_lemma' if guarded else 'transferred_flat_lemma','lemma_reuse':{
                                    'used':True,'source_task_id':sb['identity'],'mapping':mapping,
                                    'transport':{k:v for k,v in transported.items() if k not in
                                        ('polynomial','multipliers','guarded_multipliers','guard_polynomial')},
                                    'target_basis':basis_name,'outer_multipliers':[encoded(p) for p in outer],
                                    'outer_multiplier_degree':degree,'attempts':attempts}},diagnostics
                    entry['outcome']='not_used'
                    entry.setdefault('reason','no bounded flattened target proof using this lemma')
                except (checker.Invalid,checker.Limit) as exc:
                    entry.update(outcome='rejected',reason=str(exc))
        except (checker.Invalid,checker.Limit,TypeError,KeyError) as exc:
            diagnostics.append({'reason':'unusable lemma record: '+str(exc)})
    return None,diagnostics


class LocalizationBudgetEnded(RuntimeError): pass


class LocalizationBudget(LemmaBudget):
    def use(self,amount=1):
        if self.work+amount>self.limit:
            raise LocalizationBudgetEnded('reserved localization budget exhausted')
        self.parent.use(amount); self.work+=amount


def localized_consequence(task,budget,checker,records=()):
    """Try one original nonzero factor, then unchanged auto with reserved work.

    Expanded products only propose multipliers. The distinct checker sees the
    original task and the exact selected guard, never a replacement theorem.
    No support point is inferred from a polynomial identity or nonzero syntax.
    """
    allowance=min(100_000,max(0,(budget.limit-budget.work)//4))
    report=dict(policy='localized_first',used=False,work_allowance=allowance,
        work=0,generation_work=0,shared_generation_work=0,proposal_work=0,checking_work=0,failed_work=0,
        guards=[],attempts=[],cap_exhausted=False,fallback=False,fallback_work=0)
    part=LocalizationBudget(budget,allowance); answer=None; active=None; attempt=None

    def charged(phase,operation):
        report['phase']=phase; started=part.work
        try: return operation()
        finally: report[phase+'_work']+=part.work-started

    def prepare():
        part.use()
        binding=checker.bind(task)
        checker.need(task['query']=='polynomial_consequence','localized polynomial consequence query')
        names=binding['names']
        goal=expand(binding['goal'],names,part,checker)
        generators=[expand(node,names,part,checker) for node in binding['generators']]
        return binding,goal,generators

    try:
        if allowance:
            binding,goal,generators=charged('generation',prepare)
            names=binding['names']; n=len(names)
            for index,node in enumerate(binding['nonzero']):
                active=dict(nonzero_index=index,status='trying',generation_work=0)
                report['guards'].append(active); started=part.work
                try:
                    def lift():
                        part.use()
                        guard=expand(node,names,part,checker)
                        return multiply(guard,goal,part,checker)
                    lifted=charged('generation',lift)
                except checker.Limit as exc:
                    active.update(status='generation_limit',reason=str(exc)); continue
                finally: active['generation_work']=part.work-started
                for degree in range(binding['degree']+1):
                    attempt=dict(nonzero_index=index,degree=degree,status='trying',work=0)
                    report['attempts'].append(attempt); started=part.work
                    try:
                        def propose():
                            part.use()
                            multipliers=combination(lifted,generators,n,degree,part,checker)
                            if multipliers is None: return None
                            part.use(sum((n+1)*len(poly) for poly in multipliers))
                            return dict(kind='localized_polynomial_combination',task_id=binding['identity'],
                                nonzero_index=index,multipliers=[encoded(poly) for poly in multipliers])
                        certificate=charged('proposal',propose)
                        if certificate is None:
                            attempt['status']='no_combination'; continue
                        checked=charged('checking',lambda: checker.check(task,certificate,part))
                        checker.need(checked.get('ok') is True,'localized checker did not admit')
                        checker.need(checker.result_status(checked)=='CHECKED_IMPLICATION',
                                     'localized proof must check as an implication')
                        attempt['status']='checked'; active['status']='checked'
                        report.update(used=True,selected_nonzero_index=index,multiplier_degree_used=degree)
                        answer=dict(status='CHECKED_IMPLICATION',certificate=certificate,check=checked,
                            proof_method='localized_original_nonzero_guard',trace=[
                                dict(direction='N',operation='multiply_goal_by_original_nonzero',nonzero_index=index),
                                dict(direction='S',operation='check_original_guarded_implication',nonzero_index=index)])
                        break
                    except (checker.Invalid,checker.Limit) as exc:
                        attempt.update(status='rejected',reason=str(exc))
                    finally: attempt['work']=part.work-started
                if answer is not None: break
                active['status']='no_checked_combination'
        else: report['reason']='no reserved localization work'
    except LocalizationBudgetEnded as exc:
        report.update(cap_exhausted=True,reason=str(exc))
        if active is not None: active['status']='interrupted'
        if attempt is not None and attempt['status']=='trying': attempt['status']='interrupted'
    except checker.Limit as exc:
        report['reason']=str(exc)
    except Exception as exc:
        # Preserve diagnostics for the host, but never swallow parent exhaustion.
        exc.localization=report
        raise
    finally:
        report['work']=part.work
        report['shared_generation_work']=report['generation_work']-sum(item['generation_work'] for item in report['guards'])
        report['failed_work']=(part.work if answer is None else
            sum(item['work'] for item in report['attempts'] if item['status']!='checked')+
            sum(item['generation_work'] for item in report['guards'] if item['status']!='checked'))
    if answer is not None:
        answer['localization']=report; return answer
    report['fallback']=True; started=budget.work
    try:
        result=proof_with_lemmas(task,budget,checker,records,'auto')
        result['localization']=report
        return result
    except Exception as exc:
        exc.localization=report
        raise
    finally: report['fallback_work']=budget.work-started


def proof_with_lemmas(task,budget,checker,records,policy):
    checker.need(policy in ('auto','direct','lemma_first','target_sparse','cancellation_sparse','localized_first'),'proof scheduling policy')
    if policy=='localized_first': return localized_consequence(task,budget,checker,records)
    if policy in ('target_sparse','cancellation_sparse'):
        return consequence(task,budget,checker,proposal_policy=policy)
    def direct():
        try: return consequence(task,budget,checker,proposal_policy='cancellation_sparse' if policy=='auto' else 'full')
        except checker.Limit as exc: return {'status':'UNKNOWN','reason':str(exc)}
    result=None
    if policy!='lemma_first':
        result=direct()
        if result['status']!='UNKNOWN' or policy=='direct': return result
    allowance=min(50_000,max(0,(budget.limit-budget.work)//5))
    search={'policy':policy,'work_allowance':allowance,'records_considered':min(8,len(records)),
            'diagnostics':[],'work':0}
    if records and allowance:
        portion=LemmaBudget(budget,allowance)
        try:
            answer,_=reuse_lemma(task,records,portion,checker,search['diagnostics'],allow_guarded=policy=='lemma_first')
            if answer is not None:
                search['work']=portion.work; answer['lemma_search']=search; return answer
        except LemmaBudgetEnded as exc: search['reason']=str(exc)
        except checker.Limit as exc: search['reason']=str(exc)
        finally:
            search['work']=portion.work
            search['attempts']=sum('mapping' in d for d in search['diagnostics'])
    if result is None: result=direct()
    if records: result['lemma_search']=search
    return result


def affine_key(coefficients,budget):
    """Primitive integer vector, or a bounded proposal-generation skip reason."""
    denominator=1
    for q in coefficients:
        budget.use(); denominator=math.lcm(denominator,q.denominator)
        if denominator.bit_length()>8192: return None,'normalization bit limit'
    integers=[]
    for q in coefficients:
        budget.use(); integers.append(q.numerator*(denominator//q.denominator))
    divisor=math.gcd(*integers)
    lead=next((v for v in integers[:-1] if v),None)
    if lead is None: return None,'constant coefficient slice'
    divisor*=1 if lead>0 else -1
    integers=tuple(v//divisor for v in integers)
    if any(abs(v)>10**9 for v in integers): return None,'integer literal limit'
    return integers,None


def affine_text(coefficients,names):
    terms=[]
    for name,c in zip(names,coefficients[:-1]):
        if c: terms.append((c,name if abs(c)==1 else f'{abs(c)}*{name}'))
    if coefficients[-1]: terms.append((coefficients[-1],str(abs(coefficients[-1]))))
    return ''.join(('+' if c>0 and i else '-' if c<0 else '')+term
        for i,(c,term) in enumerate(terms))


def guard_candidates(binding,budget,checker):
    """Return deterministic proposals and coverage; a slice never proves a guard."""
    names=binding['names']; n=len(names)
    grammar=binding.get('guard_grammar','pair_equalities')
    checker.need(grammar in ('pair_equalities','coefficient_slices','assumption_slices'),'guard grammar')
    start=getattr(budget,'work',None); candidates=[]; seen=set()
    for i,j in itertools.combinations(range(n),2):
        key=tuple(int(k==i)-int(k==j) for k in range(n))+(0,)
        seen.add(key)
        candidates.append({'guard':f'{names[i]}-{names[j]}',
            'origin':{'kind':'pair_equality','variables':[names[i],names[j]]}})
    report={'grammar':grammar,'pair_count':len(candidates),'added_slices':0,'slice_cap':64,
        'subsets_visited':0,'term_visits':0,'affine_groups':0,'duplicate_slices':0,
        'skipped_non_affine_groups':0,'skipped_constant_groups':0,
        'skipped_unrepresentable':0,'skip_reasons':{},'truncated':False,
        'generation_complete':True}
    def finish():
        if start is not None: report['generation_work']=budget.work-start
        return candidates,report
    if grammar=='pair_equalities': return finish()
    goal=expand(binding['goal'],names,budget,checker)
    sources=[('original_goal',goal)]
    if grammar=='assumption_slices':
        gs=[expand(g,names,budget,checker) for g in binding['generators']]
        model=affine_model(gs,n,budget,checker)
        reduction={'affine_indices':model['affine_indices'],'rank':model['rank'],
            'consistent':model['consistent'],'free_variables':[names[i] for i in model['free']],
            'original_terms':len(goal),'added_slices':0,'applied':False,
            'role':'proposal only; original assumptions and goal remain the admission task'}
        report['assumption_reduction']=reduction
        if model['active'] and model['consistent']:
            residual=affine_substitute(goal,model,n,budget,checker)
            reduction.update(applied=True,residual_terms=len(residual),residual=encoded(residual))
            if residual!=goal: sources.append(('affine_assumption_residual',residual))
    for source,poly in sources:
        terms=sorted(poly.items())
        for size in range(1,min(3,n)+1):
            for subset in itertools.combinations(range(n),size):
                report['subsets_visited']+=1
                outside=tuple(i for i in range(n) if i not in subset); groups={}
                for powers,q in terms:
                    budget.use(); report['term_visits']+=1
                    key=tuple(powers[i] for i in outside)
                    group=groups.setdefault(key,{'affine':True,'coefficients':[Q(0)]*(n+1)})
                    degree=sum(powers[i] for i in subset)
                    if degree>1: group['affine']=False; continue
                    position=next((i for i in subset if powers[i]),n)
                    group['coefficients'][position]+=q
                for outside_powers,group in sorted(groups.items()):
                    budget.use()
                    if not group['affine']:
                        report['skipped_non_affine_groups']+=1; continue
                    if not any(group['coefficients'][:-1]):
                        report['skipped_constant_groups']+=1; continue
                    report['affine_groups']+=1
                    key,reason=affine_key(group['coefficients'],budget)
                    if reason is None and key in seen:
                        report['duplicate_slices']+=1; continue
                    guard=None
                    if reason is None:
                        guard=affine_text(key,names)
                        try: checker.parse(guard,names)
                        except checker.Invalid as exc: reason=str(exc)
                    if reason is not None:
                        report['skipped_unrepresentable']+=1
                        report['skip_reasons'][reason]=report['skip_reasons'].get(reason,0)+1
                        continue
                    if report['added_slices']==report['slice_cap']:
                        report['truncated']=True; report['generation_complete']=False
                        return finish()
                    seen.add(key); report['added_slices']+=1
                    origin={'kind':'affine_coefficient_slice',
                        'variables':[names[i] for i in subset],
                        'outside_variables':[names[i] for i in outside],
                        'outside_powers':list(outside_powers)}
                    if source=='affine_assumption_residual':
                        origin['kind']='affine_assumption_residual_slice'
                        origin['affine_indices']=model['affine_indices']
                        reduction['added_slices']+=1
                    candidates.append({'guard':guard,'origin':origin})
    return finish()


def run(task,budget,checker,policy='residual_first',previous=None,lemma_records=(),proof_policy='auto'):
    binding=checker.bind(task)
    try:
        if task['query']=='polynomial_consequence':
            if type(previous) is dict and type(previous.get('certificate')) is dict:
                cert=previous['certificate']
                try:
                    checked=checker.check(task,cert,budget)
                    return {'status':checker.result_status(checked),
                        'certificate':cert,'check':checked,'reused_after_fresh_check':True}
                except checker.Invalid: pass
            return proof_with_lemmas(task,budget,checker,lemma_records,proof_policy)
        checker.need(policy in ('residual_first','enumerate_all'),'guard scheduling policy')
        base={**task,'query':'polynomial_consequence'}
        base.pop('guard_grammar',None)
        initial=consequence(base,budget,checker)
        witnesses=[]
        if initial['status']=='CHECKED_COUNTEREXAMPLE': witnesses.append(initial['certificate']['point'])
        proposals=[]; accepted=[]; filtered=0; searched=0
        candidates,generation=guard_candidates(binding,budget,checker)
        for candidate in candidates:
            guard=candidate['guard']
            augmented={**base,'assumptions':list(task.get('assumptions',[]))+[guard]}
            bb=checker.bind(augmented); result=None
            if policy=='residual_first':
                for point in witnesses:
                    parsed_point=checker.point_read(point,bb)
                    if checker.value(bb['generators'][-1],bb['names'],parsed_point,budget)!=0: continue
                    cert={'kind':'rational_counterexample','task_id':bb['identity'],'point':point}
                    result={'status':'CHECKED_COUNTEREXAMPLE','certificate':cert,
                        'check':checker.check(augmented,cert,budget),'replayed_residual':True}
                    filtered+=1; break
            if result is None:
                searched+=1
                result=consequence(augmented,budget,checker,require_support=True)
            if result['status']=='CHECKED_COUNTEREXAMPLE':
                point=result['certificate']['point']
                if point not in witnesses: witnesses.append(point)
            if result['status']=='CHECKED_IMPLICATION':
                accepted.append({**candidate,'task':augmented,'certificate':result['certificate'],'check':result['check']})
            proposals.append({**candidate,**result})
        # Compress only when the original assumptions prove both directions.
        classes=[]; equivalences=[]
        for item in accepted:
            merged=False
            for group in classes:
                representative=group['representative']
                forward_task={**base,'assumptions':list(task.get('assumptions',[]))+[representative],'goal':item['guard']}
                forward=consequence(forward_task,budget,checker,require_support=True)
                if forward['status']!='CHECKED_IMPLICATION': continue
                reverse_task={**base,'assumptions':list(task.get('assumptions',[]))+[item['guard']],'goal':representative}
                reverse=consequence(reverse_task,budget,checker,require_support=True)
                if reverse['status']!='CHECKED_IMPLICATION': continue
                group['members'].append(item['guard']); merged=True
                equivalences.append({'left':representative,'right':item['guard'],
                    'forward_task':forward_task,'forward_certificate':forward['certificate'],
                    'reverse_task':reverse_task,'reverse_certificate':reverse['certificate']})
                break
            if not merged: classes.append({'representative':item['guard'],'members':[item['guard']]})
        return {'status':'CHECKED_GUARDS' if accepted else 'UNKNOWN','task_id':binding['identity'],
            'base_result':initial,'policy':policy,
            'grammar':('one equality between each pair of distinct declared variables' if generation['grammar']=='pair_equalities'
                else 'pair equalities plus at most 64 unique affine coefficient slices over variable subsets of size 1 to 3'
                + (' including the residual after affine-assumption substitution' if generation['grammar']=='assumption_slices' else '')),
            'candidate_generation':generation,
            'accepted':accepted,'proposals':proposals,'filtered_by_checked_residual':filtered,
            'searched_candidates':searched,'candidate_count':len(proposals),
            'guard_equivalence_classes':classes,'checked_equivalences':equivalences,
            'trace':[{'direction':'N','operation':('generate_pair_equality_candidates' if generation['grammar']=='pair_equalities'
                    else 'generate_pair_equalities_and_affine_coefficient_slices'),
                    'candidate_count':len(candidates),'generation_complete':generation['generation_complete']},
                {'direction':'W','operation':'reject_with_original_task_counterexamples','count':sum(p['status']=='CHECKED_COUNTEREXAMPLE' for p in proposals)},
                {'direction':'S','operation':'check_polynomial_combination_and_support','count':len(accepted)},
                {'direction':'N','operation':'merge_mutually_proved_guard_forms','classes':len(classes)}],
            'limits':'Only the declared equality grammar was searched. Coefficient slices are proposals, not assumed factors. Checked sufficient guards are not a complete characterization or a new algebraic theorem.'}
    except checker.Limit as exc:
        return {'status':'UNKNOWN','reason':str(exc),'task_id':binding['identity']}


# Additive durable premise helpers; existing solver and transport code is unchanged.
import hashlib
import json

PREMISE_JSON_LIMIT = 262_144
PREMISE_GRAPH_KEYS = ('dependencies', 'dependency_ids', 'parents', 'proof_graph', 'lemmas', 'source_refs')


def premise_json(value, budget, checker):
    """Canonical bounded evidence serialization, charged to the original caller."""
    try:
        text = json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)
    except (TypeError, ValueError, RecursionError) as exc:
        raise checker.Invalid('premise evidence must be finite JSON data') from exc
    raw = text.encode('utf-8'); budget.use(len(raw))
    if len(raw) > PREMISE_JSON_LIMIT:
        raise checker.Limit('premise evidence exceeds 256 KiB')
    return raw


def sufficient_core(record, budget, checker, allow_guarded=False):
    """Check and retain a certificate-sufficient equation subset, never a minimum."""
    checker.need(type(allow_guarded) is bool,'guarded core option must be Boolean')
    budget.use()
    checker.need(type(record) is dict and type(record.get('task')) is dict,
                 'premise source requires its original task')
    source = record['task']; source_binding = checker.bind(source)
    checker.need(source['query'] == 'polynomial_consequence', 'premise source must be a polynomial consequence')
    certificate = record.get('certificate')
    checker.need(type(certificate) is dict and (certificate.get('kind') == 'polynomial_combination' or
                 allow_guarded and certificate.get('kind') == 'localized_polynomial_combination'),
                 'premise source requires a flat polynomial combination unless guarded transfer is enabled')
    guarded=certificate['kind']=='localized_polynomial_combination'
    checker.need(not any(record.get(key) or certificate.get(key) for key in PREMISE_GRAPH_KEYS),
                 'source proof graph references are unsupported')
    source_check = checker.check(source, certificate, budget)
    checker.need(source_check.get('ok') is True, 'source checker did not admit')
    retained = []; multipliers = []
    for index, raw in enumerate(certificate['multipliers']):
        terms = checker.multiplier_read(raw, len(source_binding['names']), source_binding['degree'])
        budget.use(len(terms) + 1)
        if terms:
            retained.append(index); multipliers.append(dict(terms))
    original = copy.deepcopy(source); original_certificate = copy.deepcopy(certificate)
    core = copy.deepcopy(source)
    core['assumptions'] = [source.get('assumptions', [])[index] for index in retained]
    core_certificate = (guarded_certificate(core,multipliers,certificate['nonzero_index'],checker) if guarded else
                        flat_certificate(core, multipliers, checker))
    if certificate.get('support_point') is not None:
        core_certificate['support_point'] = copy.deepcopy(certificate['support_point'])
    core_check = checker.check(core, core_certificate, budget)
    checker.need(core_check.get('ok') is True, 'core checker did not admit')
    source_proof = premise_json(dict(task=original, certificate=original_certificate), budget, checker)
    return dict(source_task=original, source_certificate=original_certificate,
        source_task_id=source_binding['identity'], source_proof_sha256=hashlib.sha256(source_proof).hexdigest(),
        source_check=source_check, core_task=core, core_certificate=core_certificate,
        core_task_id=checker.bind(core)['identity'], core_check=core_check,
        retained_generator_indices=retained)


def prepare_premise_planner(task, record, budget, checker, allow_guarded=False):
    """Privately check one source snapshot for this call's several bindings.

    The returned callable owns no persistent authority. It closes over the same
    budget/checker and never exposes its captured source, receiver or parsed
    coefficients. Each returned plan is independent ordinary JSON evidence.
    """
    checker.need(type(allow_guarded) is bool,'guarded planning option must be Boolean')
    checker.need(type(record) is dict and type(record.get('task')) is dict,
                 'premise source requires its original task')
    task = copy.deepcopy(task)
    record = {key: copy.deepcopy(record[key]) for key in
              ('task', 'certificate', *PREMISE_GRAPH_KEYS) if key in record}
    receiving = checker.bind(task); names = receiving['names']; n = len(names)
    checker.need(task['query'] == 'polynomial_consequence', 'premise receiver must be a polynomial consequence')
    core = sufficient_core(record, budget, checker, allow_guarded=allow_guarded)
    guarded=core['core_certificate']['kind']=='localized_polynomial_combination'
    source = core['core_task']; source_binding = checker.bind(source)
    source_names = tuple(source_binding['names'])
    multipliers = tuple(tuple(checker.multiplier_read(raw, len(source_names), source_binding['degree']))
                        for raw in core['core_certificate']['multipliers'])
    point = (tuple(checker.point_read(core['core_certificate']['support_point'], source_binding))
             if core['core_certificate'].get('support_point') is not None else None)
    nonzero = frozenset(ast.dump(node, include_attributes=False) for node in receiving['nonzero'])

    def plan_for(mapping):
        checker.need(type(mapping) is dict, 'injective complete premise variable binding required')
        mapping = dict(mapping)
        checker.need(set(mapping) == set(source_names) and
            all(type(value) is str and value in names for value in mapping.values()) and
            len(set(mapping.values())) == len(mapping), 'injective complete premise variable binding required')
        mapped = {key: copy.deepcopy(value) for key, value in source.items() if key not in ('name', 'family')}
        mapped['variables'] = list(names)
        mapped['goal'] = renamed_expression(source['goal'], mapping, budget)
        for field in ('assumptions', 'nonzero'):
            mapped[field] = [renamed_expression(expression, mapping, budget) for expression in source.get(field, [])]
        mapped_binding = checker.bind(mapped)
        budget.use(len(nonzero) + len(mapped_binding['nonzero']))
        checker.need(all(ast.dump(node, include_attributes=False) in nonzero for node in mapped_binding['nonzero']),
                     'mapped source nonzero guard absent from original receiving task')
        positions = [names.index(mapping[name]) for name in source_names]
        mapped_multipliers = []
        for terms in multipliers:
            polynomial = {}
            for powers, coefficient in terms:
                budget.use(n + len(positions)); exponent = [0] * n
                for i, power in enumerate(powers): exponent[positions[i]] = power
                polynomial[tuple(exponent)] = coefficient
            mapped_multipliers.append(polynomial)
        receiver_index=(receiving_guard_index(mapped_binding,receiving,core['core_certificate']['nonzero_index'],budget,checker)
                        if guarded else None)
        mapped_certificate = (guarded_certificate(mapped,mapped_multipliers,core['core_certificate']['nonzero_index'],checker)
                              if guarded else flat_certificate(mapped, mapped_multipliers, checker))
        if point is not None:
            transported = [Q(0)] * n
            for index, value in zip(positions, point): budget.use(); transported[index] = value
            mapped_certificate['support_point'] = point_data(transported)
        mapped_check = checker.check(mapped, mapped_certificate, budget)
        checker.need(mapped_check.get('ok') is True, 'mapped core checker did not admit')
        children = []
        for expression in mapped['assumptions']:
            child = copy.deepcopy(task); child['goal'] = expression
            checker.bind(child); children.append(child)
        plan = dict(schema='ember.premise_plan.v1', **copy.deepcopy(core),
            receiving_task_id=receiving['identity'], mapping=mapping,
            mapped_task=mapped, mapped_certificate=mapped_certificate,
            mapped_task_id=mapped_binding['identity'], mapped_check=mapped_check, children=children)
        if guarded:
            plan.update(schema='ember.premise_plan.v2',source_proof_kind='localized_polynomial_combination',
                source_nonzero_index=core['source_certificate']['nonzero_index'],
                mapped_nonzero_index=mapped_certificate['nonzero_index'],receiving_nonzero_index=receiver_index)
        raw = premise_json(plan, budget, checker)
        identifier_bytes = len(b',"plan_id":""') + 64
        budget.use(identifier_bytes)
        if len(raw) + identifier_bytes > PREMISE_JSON_LIMIT:
            raise checker.Limit('complete premise plan exceeds 256 KiB')
        plan['plan_id'] = hashlib.sha256(raw).hexdigest()
        return plan

    return plan_for


def plan_premises(task, record, mapping, budget, checker, allow_guarded=False):
    """Freshly check one source and binding; persisted plans confer no authority."""
    return prepare_premise_planner(task, record, budget, checker, allow_guarded=allow_guarded)(mapping)


def assemble_premises(task, plan, child_certificates, budget, checker, allow_guarded=False):
    """Rebuild dependencies, check children and flatten to the original generators."""
    checker.need(type(plan) is dict, 'premise plan object')
    rebuilt = plan_premises(task, dict(task=plan.get('source_task'), certificate=plan.get('source_certificate')),
                            plan.get('mapping'), budget, checker, allow_guarded=allow_guarded)
    checker.need(premise_json(plan, budget, checker) == premise_json(rebuilt, budget, checker),
                 'persisted premise plan differs from freshly rebuilt original evidence')
    children = rebuilt['children']
    checker.need(type(child_certificates) in (list, tuple) and len(child_certificates) == len(children),
                 'one ordered certificate per original premise child is required')
    receiving = checker.bind(task); names = receiving['names']; n = len(names)
    guarded=rebuilt['mapped_check']['kind']=='localized_polynomial_combination'
    details = dict(plan_id=rebuilt['plan_id'], source_task_id=rebuilt['source_task_id'],
        source_proof_sha256=rebuilt['source_proof_sha256'], retained_generator_indices=rebuilt['retained_generator_indices'],
        mapping=rebuilt['mapping'], child_task_ids=[checker.bind(child)['identity'] for child in children],
        children_checked=0, outer_attempts=0, failed_outer_attempts=[])
    if guarded:details.update(source_proof_kind=rebuilt['source_proof_kind'],
        source_nonzero_index=rebuilt['source_nonzero_index'],mapped_nonzero_index=rebuilt['mapped_nonzero_index'],
        receiving_nonzero_index=rebuilt['receiving_nonzero_index'])
    child_multipliers = []
    for index, (child, certificate) in enumerate(zip(children, child_certificates)):
        checked = checker.check(child, certificate, budget)
        checker.need(checked.get('ok') is True, 'child checker did not admit')
        details['children_checked'] += 1
        if checked['kind'] == 'rational_counterexample':
            details['blocked_child_index'] = index
            return dict(status='UNKNOWN', reason='a checked child counterexample does not discharge this premise; parent is not refuted',
                        premise_assembly=details)
        checker.need(checked['kind'] == 'polynomial_combination',
                     'localized child proof is unsupported by flat premise assembly')
        child_multipliers.append([dict(checker.multiplier_read(raw, n, receiving['degree']))
                                  for raw in certificate['multipliers']])
    try:
        mapped_binding = checker.bind(rebuilt['mapped_task'])
        source_multipliers = [dict(checker.multiplier_read(raw, n, mapped_binding['degree']))
                              for raw in rebuilt['mapped_certificate']['multipliers']]
        generators = [expand(node, names, budget, checker) for node in receiving['generators']]
        lemma_multipliers = [{} for _ in generators]
        for source_multiplier, coefficients in zip(source_multipliers, child_multipliers):
            for index, coefficient in enumerate(coefficients):
                lemma_multipliers[index] = add(lemma_multipliers[index],
                    multiply(source_multiplier, coefficient, budget, checker), budget, checker)
        lemma = expand(mapped_binding['goal'], names, budget, checker)
        goal = expand(receiving['goal'], names, budget, checker)
        guard=(expand(receiving['nonzero'][rebuilt['receiving_nonzero_index']],names,budget,checker) if guarded else None)
        for basis_name, basis in [('lemma_only', [lemma]), ('lemma_and_original', [lemma, *generators])]:
            for degree in range(receiving['degree'] + 1):
                details['outer_attempts'] += 1
                try:
                    outer = combination(goal, basis, n, degree, budget, checker)
                    if outer is None or not outer[0]:
                        continue
                    if basis_name == 'lemma_only': outer = outer + [{} for _ in generators]
                    flattened = [add(multiply(guard,direct,budget,checker) if guarded else direct,
                                     multiply(outer[0], transported, budget, checker), budget, checker)
                                 for direct, transported in zip(outer[1:], lemma_multipliers)]
                    if not fits_certificate(flattened, receiving['degree']):
                        details['failed_outer_attempts'].append(dict(basis=basis_name, degree=degree,
                            reason='flattened multiplier exceeds original receiving certificate bounds'))
                        continue
                    certificate = (guarded_certificate(task,flattened,rebuilt['receiving_nonzero_index'],checker) if guarded else
                                   flat_certificate(task, flattened, checker))
                    checked = checker.check(task, certificate, budget)
                    checker.need(checked.get('ok') is True, 'original parent checker did not admit')
                    details.update(target_basis=basis_name, outer_multiplier_degree=degree,
                                   outer_multipliers=[encoded(poly) for poly in outer])
                    return dict(status='CHECKED_IMPLICATION', certificate=certificate, check=checked,
                        proof_method='assembled_original_guarded_premise_proofs' if guarded else 'assembled_original_premise_proofs', premise_assembly=details, trace=[
                            dict(direction='S', operation='rebuild_checked_source_core_and_mapped_plan', plan_id=rebuilt['plan_id']),
                            dict(direction='S', operation='check_premises_against_original_receiving_equations', count=len(children)),
                            dict(direction='N', operation='flatten_child_and_source_multipliers', original_generator_count=len(generators)),
                            dict(direction='S', operation='check_original_parent_certificate', accepted=True)])
                except (checker.Invalid, checker.Limit) as exc:
                    details['failed_outer_attempts'].append(dict(basis=basis_name, degree=degree, reason=str(exc)))
        return dict(status='UNKNOWN', reason='no bounded original-generator proof assembled from the checked premises',
                    premise_assembly=details)
    except checker.Limit as exc:
        return dict(status='UNKNOWN', reason=str(exc), premise_assembly=details)
