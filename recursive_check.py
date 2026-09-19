"""Owned bounded equality/structural-induction checker for Nat and List(Nat).

The original declarations are data, never imported programs. Search is not
imported. Every lemma and root is replayed against the original typed theory.
"""
import copy
import hashlib
import json
import re

MAX_DEFINITIONS=16
MAX_ARITY=4
MAX_VARIABLES=16
INPUT_NODES=1024
INPUT_DEPTH=64
TERM_NODES=4096
TERM_DEPTH=128
MAX_LEMMAS=16
CERTIFICATE_BYTES=262144
PROOF_NODES=128
SIDE_STEPS=2048
TOTAL_STEPS=10000
SORTS=('Nat','List')
CONSTRUCTORS={'zero':((),'Nat'),'succ':(('Nat',),'Nat'),
              'nil':((),'List'),'cons':(('Nat','List'),'List')}
IDENTIFIER=re.compile(r'[A-Za-z_][A-Za-z_0-9]{0,63}\Z')

class Invalid(ValueError):pass
class Limit(RuntimeError):pass
class _NoBudget:
    def use(self,amount=1):pass

def need(condition,message):
    if not condition:raise Invalid(message)

def _keys(obj,required,optional=()):
    need(type(obj) is dict and set(required)<=set(obj)<=set(required)|set(optional),'object fields differ from recursive certificate grammar')

def _identifier(name):
    need(type(name) is str and IDENTIFIER.fullmatch(name) is not None,'identifier must be ASCII, length1..64')

def _bytes(value,budget,limit):
    # Refuse oversized scalar/container inputs before a full JSON serialization.
    pending=[value];lower=0
    while pending:
        item=pending.pop();budget.use();lower+=1
        if type(item) is dict:
            need(all(type(k) is str for k in item),'JSON keys must be strings')
            if len(item)>limit:raise Limit('JSON object exceeds byte envelope')
            pending.extend(item.keys());pending.extend(item.values())
        elif type(item) is list:
            if len(item)>limit:raise Limit('JSON list exceeds byte envelope')
            pending.extend(item)
        elif type(item) is str:
            if len(item)>limit:raise Limit('JSON string exceeds byte envelope')
            lower+=len(item.encode('utf-8'))
        else:need(item is None or type(item) in (int,bool),'only finite JSON data is supported')
        if lower>limit or len(pending)>limit:raise Limit('JSON data exceeds byte envelope')
    try:raw=json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')
    except (ValueError,TypeError,RecursionError,OverflowError) as exc:raise Invalid('recursive JSON serialization failed') from exc
    budget.use(len(raw))
    if len(raw)>limit:raise Limit('recursive JSON byte limit')
    return raw

def _parse(data,signature,budget,max_nodes=INPUT_NODES,max_depth=INPUT_DEPTH):
    count=0
    def walk(value,depth):
        nonlocal count
        budget.use();count+=1
        if count>max_nodes or depth>max_depth:raise Limit('recursive term input limit')
        if type(value) is dict:
            _keys(value,('v','sort'));_identifier(value['v']);need(value['sort'] in SORTS,'unknown variable sort')
            return ('v',value['v'],value['sort']),value['sort']
        need(type(value) is list and bool(value),'term must be a typed variable or application')
        name=value[0];_identifier(name);need(name in signature,'unknown recursive function symbol')
        inputs,output=signature[name];need(len(value)==len(inputs)+1,'application arity mismatch')
        children=[]
        for arg,expected in zip(value[1:],inputs):
            child,actual=walk(arg,depth+1);need(actual==expected,'application argument sort mismatch');children.append(child)
        return ('f',name,tuple(children)),output
    return walk(data,0)[0]

def _data(term):
    return {'v':term[1],'sort':term[2]} if term[0]=='v' else [term[1],*(_data(child) for child in term[2])]

def _variables(terms,budget):
    result={};pending=list(terms)
    while pending:
        term=pending.pop();budget.use()
        if term[0]=='v':
            need(term[1] not in result or result[term[1]]==term[2],'one variable name has conflicting sorts')
            result[term[1]]=term[2]
            if len(result)>MAX_VARIABLES:raise Limit('too many equation variables')
        else:pending.extend(term[2])
    return result

def _sort(term,signature):return term[2] if term[0]=='v' else signature[term[1]][1]

def _bounded(term,signature,budget,scope=None):
    pending=[(term,0)];count=0
    while pending:
        node,depth=pending.pop();budget.use();count+=1
        if count>TERM_NODES or depth>TERM_DEPTH:raise Limit('recursive intermediate term limit')
        if node[0]=='v':
            if scope is not None:need(scope.get(node[1])==node[2],'out-of-scope recursive variable')
        else:
            inputs,_=signature[node[1]];need(len(inputs)==len(node[2]),'internal term arity')
            for child,expected in zip(node[2],inputs):
                need(_sort(child,signature)==expected,'replacement changed recursive sort')
                pending.append((child,depth+1))
    return term

def _substitute(term,env,signature,budget,scope=None):
    def walk(node):
        budget.use()
        if node[0]=='v':return env.get(node[1],node)  # simultaneous, never recurse into inserted terms
        return ('f',node[1],tuple(walk(child) for child in node[2]))
    return _bounded(walk(term),signature,budget,scope)

def _equation(data,signature,budget):
    _keys(data,('lhs','rhs'))
    pair=(_parse(data['lhs'],signature,budget),_parse(data['rhs'],signature,budget))
    need(_sort(pair[0],signature)==_sort(pair[1],signature),'equality sides have different sorts')
    _variables(pair,budget);return pair

def _subterms(term,budget):
    pending=[term]
    while pending:
        node=pending.pop();budget.use();yield node
        if node[0]=='f':pending.extend(node[2])

class _Theory:
    def __init__(self,definitions,budget):
        need(type(definitions) is list,'definitions must be an ordered list')
        if len(definitions)>MAX_DEFINITIONS:raise Limit('too many recursive definitions')
        self.signature=dict(CONSTRUCTORS);self.rules={};self.recursion={};self.by_constructor={}
        for declaration in definitions:
            budget.use();_keys(declaration,('name','inputs','output','recursion','equations'))
            name=declaration['name'];_identifier(name);need(name not in self.signature,'duplicate function or constructor redefinition')
            inputs=declaration['inputs'];output=declaration['output'];index=declaration['recursion']
            need(type(inputs) is list and 1<=len(inputs)<=MAX_ARITY and all(s in SORTS for s in inputs) and output in SORTS,'function signature')
            need(type(index) is int and 0<=index<len(inputs),'structural recursion argument index')
            equations=declaration['equations'];need(type(equations) is list,'definition equations list')
            need(len(equations)==2,'complete definition equation count')
            signature={**self.signature,name:(tuple(inputs),output)};rules=[];covered={}
            for case,raw in enumerate(equations):
                pair=_equation(raw,signature,budget);left,right=pair
                need(left[0]=='f' and left[1]==name,'definition left head is not the declared function')
                binders=[];smaller=[];constructor=None
                for position,argument in enumerate(left[2]):
                    if position!=index:
                        need(argument[0]=='v','non-recursive patterns must be variables');binders.append(argument)
                    else:
                        need(argument[0]=='f' and argument[1] in CONSTRUCTORS,'recursion pattern must be a constructor')
                        constructor=argument[1];need(CONSTRUCTORS[constructor][1]==inputs[index],'wrong recursion constructor sort')
                        need(constructor not in covered,'overlapping constructor cases')
                        need(all(x[0]=='v' for x in argument[2]),'nested constructor patterns are unsupported')
                        binders.extend(argument[2]);smaller=[x for x in argument[2] if x[2]==inputs[index]]
                need(len({x[1] for x in binders})==len(binders),'definition pattern repeats a binder')
                quantified={x[1]:x[2] for x in binders}
                need(all(quantified.get(k)==v for k,v in _variables((right,),budget).items()),'unbound right-side definition variable')
                for node in _subterms(right,budget):
                    if node[0]=='f' and node[1]==name:
                        need(index is not None and node[2][index] in smaller,'recursive call does not use a direct strict substructure')
                rules.append((left,right,quantified))
                if constructor is not None:covered[constructor]=case
            if index is not None:
                required={name for name,(_,sort) in CONSTRUCTORS.items() if sort==inputs[index]}
                need(set(covered)==required,'missing original constructor case')
            self.signature=signature;self.rules[name]=tuple(rules);self.recursion[name]=index;self.by_constructor[name]=covered

def bind(task,budget=None):
    budget=_NoBudget() if budget is None else budget
    _keys(task,('query','domain','definitions','goal'))
    need(task['query']=='prove_recursive_identity' and task['domain']=='NatList','recursive query/domain mismatch')
    original={key:task[key] for key in ('query','domain','definitions','goal')}
    raw=_bytes(original,budget,1048576)
    theory=_Theory(task['definitions'],budget);goal=_equation(task['goal'],theory.signature,budget)
    return dict(identity=hashlib.sha256(raw).hexdigest(),theory=theory,goal=goal,scope=_variables(goal,budget),
                goal_data=copy.deepcopy(task['goal']),definitions=copy.deepcopy(task['definitions']))

def _equal(left,right,budget):
    pending=[(left,right)]
    while pending:
        a,b=pending.pop();budget.use()
        if a[0]!=b[0] or a[1]!=b[1]:return False
        if a[0]=='v':
            if a[2]!=b[2]:return False
        else:
            if len(a[2])!=len(b[2]):return False
            pending.extend(zip(a[2],b[2]))
    return True

def _rewrite(term,step,scope,theory,lemmas,ih,budget,counts):
    _keys(step,('source','direction','at','subst'))
    source=step['source'];need(type(source) is dict and type(source.get('kind')) is str,'rewrite source namespace')
    if source['kind']=='definition':
        _keys(source,('kind','name','case'));name=source['name'];index=source['case']
        need(type(name) is str and name in theory.rules and type(index) is int and 0<=index<len(theory.rules[name]),'unknown definition rule')
        rule=theory.rules[name][index]
    elif source['kind']=='lemma':
        _keys(source,('kind','index'));index=source['index']
        need(type(index) is int and 0<=index<len(lemmas),'unknown, cyclic or forward lemma reference');rule=lemmas[index]
    elif source['kind']=='ih':
        _keys(source,('kind',));need(ih is not None,'induction hypothesis outside recursive constructor case');rule=ih
    else:raise Invalid('unknown rewrite source kind')
    direction=step['direction'];need(type(direction) is int and direction in (-1,1),'rewrite direction')
    raw=step['subst'];need(type(raw) is dict and set(raw)==set(rule[2]),'rewrite substitution domain')
    env={}
    for name,sort in rule[2].items():
        value=_parse(raw[name],theory.signature,budget,TERM_NODES,TERM_DEPTH)
        need(_sort(value,theory.signature)==sort,'rewrite substitution sort')
        env[name]=_bounded(value,theory.signature,budget,scope)
    left,right=rule[:2]
    if direction==-1:left,right=right,left
    left=_substitute(left,env,theory.signature,budget,scope);right=_substitute(right,env,theory.signature,budget,scope)
    path=step['at'];need(type(path) is list and len(path)<=TERM_DEPTH,'rewrite position')
    current=term;parents=[]
    for index in path:
        budget.use();need(type(index) is int and current[0]=='f' and 0<=index<len(current[2]),'invalid rewrite position')
        parents.append((current,index));current=current[2][index]
    need(_equal(current,left,budget),'rewrite does not match the original occurrence')
    need(_sort(left,theory.signature)==_sort(right,theory.signature),'rewrite changes term sort')
    result=right
    for parent,index in reversed(parents):
        budget.use();children=list(parent[2]);children[index]=result;result=('f',parent[1],tuple(children))
    counts['rewrite_steps']+=1
    if counts['rewrite_steps']>TOTAL_STEPS:raise Limit('global recursive rewrite step limit')
    return _bounded(result,theory.signature,budget,scope)

def _verify(goal,proof,scope,theory,lemmas,ih,budget,counts,induction_allowed=True):
    budget.use();counts['proof_nodes']+=1
    if counts['proof_nodes']>PROOF_NODES:raise Limit('recursive proof node limit')
    need(type(proof) is dict,'recursive proof node')
    for term in goal:_bounded(term,theory.signature,budget,scope)
    if proof.get('rule')=='join':
        _keys(proof,('rule','left','right'));results=[]
        for term,side in zip(goal,('left','right')):
            steps=proof[side];need(type(steps) is list,'join requires explicit rewrite traces')
            if len(steps)>SIDE_STEPS:raise Limit('recursive join side step limit')
            for step in steps:term=_rewrite(term,step,scope,theory,lemmas,ih,budget,counts)
            results.append(term)
        need(_equal(results[0],results[1],budget),'recursive equality traces do not join');return
    need(proof.get('rule')=='induction','unsupported recursive proof constructor')
    _keys(proof,('rule','variable','cases'));need(induction_allowed and ih is None,'nested structural induction is unsupported')
    name=proof['variable'];need(type(name) is str and name in scope,'induction variable is not in original goal')
    sort=scope[name];expected={key:inputs for key,(inputs,result) in CONSTRUCTORS.items() if result==sort}
    cases=proof['cases'];need(type(cases) is dict and set(cases)==set(expected),'structural induction constructor coverage')
    quantified={key:value for key,value in scope.items() if key!=name}
    for constructor,inputs in expected.items():
        case=cases[constructor];_keys(case,('binders','proof'));raw=case['binders']
        need(type(raw) is list and len(raw)==len(inputs),'induction constructor binders')
        binders=[];local_scope=dict(quantified)
        for value,required in zip(raw,inputs):
            binder=_parse(value,theory.signature,budget)
            need(binder[0]=='v' and binder[2]==required,'induction binder sort')
            need(binder[1] not in scope and binder[1] not in local_scope,'induction eigenvariable is not fresh')
            binders.append(binder);local_scope[binder[1]]=required
        replacement=('f',constructor,tuple(binders))
        case_goal=tuple(_substitute(term,{name:replacement},theory.signature,budget,local_scope) for term in goal)
        smaller=[binder for binder in binders if binder[2]==sort];need(len(smaller)<=1,'unsupported branching recursive datatype')
        hypothesis=None
        if smaller:
            equation=tuple(_substitute(term,{name:smaller[0]},theory.signature,budget,local_scope) for term in goal)
            hypothesis=(*equation,dict(quantified))
        _verify(case_goal,case['proof'],local_scope,theory,lemmas,hypothesis,budget,counts,False)

def _evaluate(term,theory,budget):
    operations=[('visit',term)];values=[]
    while operations:
        budget.use()
        if len(operations)>TERM_NODES or len(values)>TERM_NODES:raise Limit('closed evaluation frontier limit')
        operation=operations.pop()
        if operation[0]=='visit':
            node=operation[1];need(node[0]=='f','cannot evaluate open recursive term')
            operations.append(('finish',node[1],len(node[2])))
            operations.extend(('visit',child) for child in reversed(node[2]));continue
        _,name,arity=operation;arguments=values[-arity:] if arity else []
        if arity:del values[-arity:]
        if name in CONSTRUCTORS:
            values.append(_bounded(('f',name,tuple(arguments)),theory.signature,budget,{}));continue
        index=theory.recursion[name]
        case=0 if index is None else theory.by_constructor[name].get(arguments[index][1])
        need(case is not None,'closed original definition coverage failure')
        left,right,_=theory.rules[name][case];env={}
        for position,(pattern,value) in enumerate(zip(left[2],arguments)):
            if position==index:
                need(pattern[1]==value[1],'closed recursive pattern mismatch')
                for variable,field in zip(pattern[2],value[2]):env[variable[1]]=field
            else:env[pattern[1]]=value
        reduced=_substitute(right,env,theory.signature,budget,{})
        operations.append(('visit',reduced))
    need(len(values)==1,'closed evaluation stack shape');return values[0]

def check(task,certificate,budget):
    binding=bind(task,budget);theory=binding['theory'];goal=binding['goal'];scope=binding['scope']
    _bytes(certificate,budget,CERTIFICATE_BYTES)
    need(type(certificate) is dict and certificate.get('task_id')==binding['identity'],'recursive certificate original task binding')
    kind=certificate.get('kind');counts=dict(rewrite_steps=0,proof_nodes=0)
    if kind=='recursive_identity':
        _keys(certificate,('kind','task_id','lemmas','proof'));items=certificate['lemmas']
        need(type(items) is list,'ordered recursive lemma proofs')
        if len(items)>MAX_LEMMAS:raise Limit('recursive lemma count limit')
        lemmas=[]
        for item in items:
            _keys(item,('goal','proof'));equation=_equation(item['goal'],theory.signature,budget);variables=_variables(equation,budget)
            _verify(equation,item['proof'],variables,theory,lemmas,None,budget,counts)
            lemmas.append((*equation,variables))
        _verify(goal,certificate['proof'],scope,theory,lemmas,None,budget,counts)
        return dict(ok=True,kind=kind,task_id=binding['identity'],lemma_count=len(lemmas),**counts,
                    scope='All finite original Nat/List constructor values under validated definitions; bounded explicit proof replay.')
    need(kind=='recursive_counterexample','unknown recursive certificate kind')
    _keys(certificate,('kind','task_id','point'));point=certificate['point']
    need(type(point) is dict and set(point)==set(scope),'counterexample requires every original goal variable')
    env={}
    for name,sort in scope.items():
        value=_parse(point[name],theory.signature,budget,TERM_NODES,TERM_DEPTH)
        need(_sort(value,theory.signature)==sort,'counterexample value sort')
        need(all(t[0]=='f' and t[1] in CONSTRUCTORS for t in _subterms(value,budget)),'counterexample requires closed constructor values')
        env[name]=value
    instantiated=tuple(_substitute(term,env,theory.signature,budget,{}) for term in goal)
    values=tuple(_evaluate(term,theory,budget) for term in instantiated)
    need(not _equal(values[0],values[1],budget),'counterexample has equal original normal forms')
    return dict(ok=True,kind=kind,task_id=binding['identity'],lemma_count=0,**counts,
                left_value=_data(values[0]),right_value=_data(values[1]),scope='One original ground Nat/List counterexample.')

def result_status(checked):
    need(type(checked) is dict and checked.get('ok') is True,'recursive check did not admit')
    statuses={'recursive_identity':'CHECKED_RECURSIVE_IDENTITY','recursive_counterexample':'CHECKED_RECURSIVE_COUNTEREXAMPLE'}
    need(checked.get('kind') in statuses,'unsupported recursive checked kind');return statuses[checked['kind']]
