"""TPM specialization: exact coefficient dependencies guide invariant proposals.

This map is search data, never admission evidence. Its edges come from the
owned producer's exact residual columns; the original-AST checker proves results.
"""
import hashlib
import json


class MapLimit(ValueError):
    pass


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)


def build(binding,basis,columns,budget):
    if len(basis)!=len(columns) or not 1<=len(basis)<=128:
        raise MapLimit('dependency map column bound')
    rows={}; edge_count=0
    for index,column in enumerate(columns):
        budget.use()
        for exponent,coefficient in sorted(column.items()):
            budget.use()
            if not coefficient:continue
            rows.setdefault(exponent,[]).append((index,coefficient));edge_count+=1
            if len(rows)>4096 or edge_count>16384:
                raise MapLimit('complete dependency map size bound')
    # Shared coefficient equations, not merely shared variable names, connect
    # unknowns. The constant residual row is load-bearing for x+1,y-1.
    parent=list(range(len(basis)))
    def find(index):
        while parent[index]!=index:
            budget.use();parent[index]=parent[parent[index]];index=parent[index]
        return index
    for entries in rows.values():
        first=entries[0][0]
        for index,_ in entries[1:]:
            budget.use();a=find(first);b=find(index)
            if a!=b:parent[max(a,b)]=min(a,b)
    groups={}
    for index in range(len(basis)):
        budget.use();groups.setdefault(find(index),[]).append(index)
    components=sorted(groups.values(),key=lambda indices:indices[0])
    candidate_monomials=[];equation_monomials=[];edges=[]
    for index,exponent in enumerate(basis):
        budget.use(len(exponent)+1)
        candidate_monomials.append(list(exponent))
    for row_index,(exponent,entries) in enumerate(sorted(rows.items())):
        budget.use(len(exponent)+1);equation_monomials.append(list(exponent))
        for column_index,coefficient in entries:
            budget.use()
            edges.append([column_index,row_index,[coefficient.numerator,coefficient.denominator]])
    # Include the original binding and exact column values, not just the topology.
    # A changed input/checker never inherits an accepted result from this digest.
    source=dict(task_id=binding['identity'],basis=[list(e) for e in basis],
        columns=[[[list(e),[q.numerator,q.denominator]] for e,q in sorted(c.items()) if q]
                 for c in columns])
    raw=canonical(source).encode('utf-8');budget.use(len(raw))
    result=dict(schema='ember.tpm.coefficient_dependencies.v2',task_id=binding['identity'],
        source_digest=hashlib.sha256(raw).hexdigest(),variables=list(binding['names']),focus=list(binding['focus']),
        node_types=['CandidateCoefficient','ResidualEquation'],edge_type='CoefficientContribution',
        candidate_monomials=candidate_monomials,equation_monomials=equation_monomials,contributions=edges,
        components=components,edge_count=len(edges),complete=True,
        origin='Typed source-bound synthesis specialized to exact coefficient equations',
        guard='Components require complete basis coverage and disjoint residual-row incidence',
        scope='Proposal decomposition only; every invariant requires original-task checking')
    size=len(canonical(result).encode('utf-8'));budget.use(size)
    if size>262144:raise MapLimit('serialized complete dependency map exceeds 256 KiB')
    return result


def components(binding,basis,columns,budget):
    return build(binding,basis,columns,budget)['components']
