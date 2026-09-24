"""Standard-library process client for the owned offline Ember task API.

No shell, network, model or donor program is used. A wall timeout bounds how long
the client waits; it is not an OS CPU/memory limit. Captured child files are read
only up to the response bound; the bound is not a child disk quota. Instances
sharing a state path require caller-side serialization (the runtime has one writer).
"""
import argparse
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import time

API_VERSION='ember.helper.v1'
RUNTIME_API='ember.task.v1'
INPUT_LIMIT=1_048_576
CLOSED={'EXACT_DIRECT','CHECKED_EXACT','CHECKED_COUNTEREXAMPLE',
        'CHECKED_IMPLICATION','CHECKED_GUARDS','CHECKED_WORD_IDENTITY',
        'CHECKED_WORD_COUNTEREXAMPLE','CHECKED_CAMPAIGN','CHECKED_RECURRENCE','CHECKED_INVARIANT',
        'CHECKED_RECURSIVE_IDENTITY','CHECKED_RECURSIVE_COUNTEREXAMPLE','CHECKED_SOURCE_EPISODE',
        'CHECKED_ORBIT_EXCLUSION','CHECKED_ORBIT_REACHES','CHECKED_GENERATING_FUNCTION',
        'CHECKED_MINIMAL_RECURRENCE'}
# Exact answers can exceed Python's default 4300-digit decimal conversion limit.
INT_DIGITS=100_000


class ClientError(ValueError): pass


def decode_json(raw):
    def pairs(items):
        result={}
        for key,value in items:
            if key in result: raise ClientError('duplicate JSON key')
            result[key]=value
        return result
    def constant(value): raise ClientError('nonfinite JSON value')
    try: return json.loads(raw.decode('utf-8'),object_pairs_hook=pairs,parse_constant=constant)
    except (UnicodeError,json.JSONDecodeError,RecursionError) as exc:
        raise ClientError('invalid UTF-8 JSON response or input') from exc


class EmberClient:
    """call(task) returns a JSON-compatible receipt, including unresolved outcomes."""
    def __init__(self,root=None,state=None,work=10_000_000,timeout=30,max_response=16_777_216):
        self.root=Path(root).resolve() if root is not None else Path(__file__).resolve().parents[1]
        self.runtime=self.root/'ember.py'
        self.state=Path(state).resolve() if state is not None else None
        if type(work) is not int or work<0: raise ClientError('nonnegative integer work budget required')
        if type(timeout) not in (int,float) or not math.isfinite(timeout) or timeout<=0:
            raise ClientError('finite positive timeout required')
        if type(max_response) is not int or not 1<=max_response<=67_108_864:
            raise ClientError('response read bound must be between 1 and 67108864 bytes')
        self.work=work; self.timeout=timeout; self.max_response=max_response
        self._capabilities=None

    def _invoke(self,arguments):
        if not self.runtime.is_file(): raise ClientError('owned Ember runtime is missing from the selected root')
        command=[sys.executable,'-I','-B','-X','utf8',str(self.runtime),*arguments]
        try:
            with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
                proc=subprocess.run(command,stdin=subprocess.DEVNULL,stdout=out,stderr=err,
                    cwd=self.root,timeout=self.timeout,shell=False,
                    creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
                out.seek(0); raw=out.read(self.max_response+1)
                err.seek(0); diagnostic=err.read(16_385)
            if len(raw)>self.max_response: raise ClientError('child JSON response exceeds configured read bound')
            if not raw:
                raise ClientError('child returned no JSON; exit '+str(proc.returncode)
                    +('; '+diagnostic[:16_384].decode('utf-8',errors='replace') if diagnostic else ''))
            result=decode_json(raw)
            if type(result) is not dict: raise ClientError('child JSON must be an object')
            return proc.returncode,result
        except subprocess.TimeoutExpired as exc:
            raise ClientError('child wall timeout; no mathematical outcome was received; inspect retained state before resuming') from exc
        except OSError as exc: raise ClientError('child process or local file failure: '+str(exc)) from exc

    def capabilities(self):
        if self._capabilities is None:
            code,capabilities=self._invoke(['--capabilities'])
            if code!=0 or capabilities.get('status')!='CAPABILITIES':
                raise ClientError('runtime capability request failed')
            if capabilities.get('api_version')!=RUNTIME_API:
                raise ClientError('incompatible runtime API version')
            queries=capabilities.get('queries')
            if type(queries) is not list or not queries or any(type(q) is not str for q in queries):
                raise ClientError('runtime capability query list is invalid')
            if type(capabilities.get('runtime_version')) is not str:
                raise ClientError('runtime version is missing')
            self._capabilities=capabilities
        # A caller cannot alter the client's validated metadata through the return.
        return json.loads(json.dumps(self._capabilities))

    def _receipt(self,status,outcome,code,started,**fields):
        return {'api_version':API_VERSION,'runtime_api_version':RUNTIME_API,
            'runtime_version':self._capabilities.get('runtime_version') if self._capabilities else None,
            'status':status,'outcome':outcome,'exit_code':code,
            'elapsed_ns':time.perf_counter_ns()-started,**fields}

    def call(self,task,work=None,proof_policy='auto',obligation_steps=4,
             recursive_policy='residual',recursive_steps=4,source_policy='gap_bridge',source_steps=8,layer='direct'):
        started=time.perf_counter_ns()
        try:
            limit=self.work if work is None else work
            if type(limit) is not int or limit<0: raise ClientError('nonnegative integer work budget required')
            if proof_policy not in ('auto','direct','lemma_first','target_sparse','cancellation_sparse','obligations','localized_first'):
                raise ClientError('unsupported proof policy')
            if type(obligation_steps) is not int or not 1<=obligation_steps<=64:
                raise ClientError('obligation steps must be 1..64')
            if recursive_policy not in ('direct','enumerate','residual'):
                raise ClientError('unsupported recursive identity policy')
            if type(recursive_steps) is not int or not 1<=recursive_steps<=64:
                raise ClientError('recursive steps must be 1..64')
            if source_policy not in ('native_isolated','graph_isolated','fixed_bridge','gap_bridge'):
                raise ClientError('unsupported source episode policy')
            if type(source_steps) is not int or not 1<=source_steps<=64:
                raise ClientError('source steps must be 1..64')
            if layer not in ('direct','apex'): raise ClientError('unsupported reasoning layer')
            self.capabilities()
            try: raw=json.dumps(task,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')
            except (TypeError,ValueError,RecursionError) as exc: raise ClientError('task is not finite serializable JSON') from exc
            if len(raw)>INPUT_LIMIT: raise ClientError('task JSON exceeds 1 MiB')
            with tempfile.TemporaryDirectory(prefix='ember-helper-') as temporary:
                path=Path(temporary)/'task.json'; path.write_bytes(raw)
                args=[str(path),'--work',str(limit)]
                if proof_policy!='auto':args+=['--proof-policy',proof_policy]
                if obligation_steps!=4:args+=['--obligation-steps',str(obligation_steps)]
                if recursive_policy!='residual':args+=['--recursive-policy',recursive_policy]
                if recursive_steps!=4:args+=['--recursive-steps',str(recursive_steps)]
                if source_policy!='gap_bridge':args+=['--source-policy',source_policy]
                if source_steps!=8:args+=['--source-steps',str(source_steps)]
                if layer!='direct':args+=['--layer',layer]
                if self.state is not None: args+=['--state',str(self.state)]
                code,result=self._invoke(args)
            status=result.get('status')
            if type(status) is not str: raise ClientError('runtime result status must be text')
            if code==0 and status in CLOSED: outcome='closed'
            elif code==2 and status=='REFUSED': outcome='refused'
            elif code==3 and status=='UNKNOWN': outcome='unknown'
            else: raise ClientError('runtime exit code and result status do not match the task API')
            return self._receipt(status,outcome,code,started,result=result)
        except (ClientError,OSError) as exc:
            return self._receipt('CLIENT_ERROR','client_error',4,started,reason=str(exc))

    def call_file(self,path,work=None,proof_policy='auto',obligation_steps=4,
                  recursive_policy='residual',recursive_steps=4,source_policy='gap_bridge',source_steps=8,layer='direct'):
        started=time.perf_counter_ns()
        try:
            with Path(path).open('rb') as handle: raw=handle.read(INPUT_LIMIT+1)
            if len(raw)>INPUT_LIMIT: raise ClientError('task JSON exceeds 1 MiB')
            result=self.call(decode_json(raw),work=work,proof_policy=proof_policy,obligation_steps=obligation_steps,
                             recursive_policy=recursive_policy,recursive_steps=recursive_steps,
                             source_policy=source_policy,source_steps=source_steps,layer=layer)
            result['elapsed_ns']=time.perf_counter_ns()-started
            return result
        except (ClientError,OSError) as exc:
            return self._receipt('CLIENT_ERROR','client_error',4,started,reason=str(exc))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('task',nargs='?',type=Path)
    parser.add_argument('--root',type=Path)
    parser.add_argument('--state',type=Path)
    parser.add_argument('--work',type=int,default=10_000_000)
    parser.add_argument('--proof-policy',choices=['auto','direct','lemma_first','target_sparse','cancellation_sparse','obligations','localized_first'],default='auto')
    parser.add_argument('--obligation-steps',type=int,default=4)
    parser.add_argument('--recursive-policy',choices=['direct','enumerate','residual'],default='residual')
    parser.add_argument('--recursive-steps',type=int,default=4)
    parser.add_argument('--source-policy',choices=['native_isolated','graph_isolated','fixed_bridge','gap_bridge'],default='gap_bridge')
    parser.add_argument('--source-steps',type=int,default=8)
    parser.add_argument('--layer',choices=['direct','apex'],default='direct')
    parser.add_argument('--timeout',type=float,default=30)
    parser.add_argument('--max-response',type=int,default=16_777_216)
    parser.add_argument('--capabilities',action='store_true')
    args=parser.parse_args(); started=time.perf_counter_ns()
    if hasattr(sys,'set_int_max_str_digits'): sys.set_int_max_str_digits(INT_DIGITS)
    try:
        client=EmberClient(args.root,args.state,args.work,args.timeout,args.max_response)
        if args.capabilities:
            result=client._receipt('CAPABILITIES','metadata',0,started,capabilities=client.capabilities())
        elif args.task is None: raise ClientError('a task JSON file or --capabilities is required')
        else: result=client.call_file(args.task,proof_policy=args.proof_policy,obligation_steps=args.obligation_steps,
                                      recursive_policy=args.recursive_policy,recursive_steps=args.recursive_steps,
                                      source_policy=args.source_policy,source_steps=args.source_steps,layer=args.layer)
    except (ClientError,OSError) as exc:
        result={'api_version':API_VERSION,'status':'CLIENT_ERROR','outcome':'client_error',
                'exit_code':4,'reason':str(exc)}
    print(json.dumps(result,indent=2,allow_nan=False))
    return result['exit_code']


if __name__=='__main__': raise SystemExit(main())
