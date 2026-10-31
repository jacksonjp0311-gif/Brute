"""Hard per-call cap for study BRUTE-0380-ENC-AUDIT-041 (experiments/BRUTE_PLAN_041.json; pre-run deviation #154 fixes it).
New file, host side only (brute/ stays host-agnostic: brute.encaudit16 takes a solver factory and never sees this module).

Why (Inferred from study-040): the pysat solver did not always honour the host interrupt promptly (GQB15 max 11.014 s > the
10.5 s bound). Here the solver runs in a child process that the host can kill:
  SolverServer   one child process per job (python -m experiments.solver_proxy_041 --serve, new session), hosting every
                 solver of the job by id; requests are length-prefixed pickles over stdin/stdout pipes, answered in order.
  SolverProxy    the solver interface brute.scalesearch10._capped_solve and brute.scalesearch14 use (add_clause, conf_budget,
                 solve_limited, interrupt, clear_interrupt, get_model, delete). Clauses are buffered, sent with the next
                 request and also kept in a flat log (array('i'), 0-terminated) for replay.
  HardHook       replaces TimerHook. arm(fn, s) (fn = proxy.interrupt) sets a SOFT deadline now + s, enforced in the child
                 (a timer thread calls solver.interrupt, as TimerHook did in-process), and a HARD deadline now + s + 1.0
                 (s <= QUERY_S14 = 9.0, so at most 10.0 s after the call starts). The host waits for each reply with select()
                 up to the hard deadline; on timeout it SIGKILLs the child and the solve returns None, so _capped_solve
                 returns capped (same label effect as any capped call). Every proxy of the job is then stale and replays
                 its clause log into a fresh child on its next use; that replay happens inside the next call and is
                 bounded by that call's own hard deadline. Learned clauses of the killed child are lost (recorded).
Clause order, clause content, budgets and assumptions are exactly what the in-process solver received, so SAT/UNSAT
verdicts are unchanged (tested); only wall time differs."""
from __future__ import annotations
import os,pickle,select,signal,struct,subprocess,sys,threading,time
from array import array
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HARD_GRACE=1.0
_H=struct.Struct('<Q')
__all__=['HARD_GRACE','SolverServer','SolverProxy','HardHook','Killed']


class Killed(Exception):pass


def _flat_clauses(flat):
    c=[]
    for x in flat:
        if x==0:yield c;c=[]
        else:c.append(x)


# ---------------------------------------------------------------- child side
def serve(inp=None,out=None,soft=True):
    from pysat.solvers import Solver
    inp=inp or sys.stdin.buffer;out=out or sys.stdout.buffer;S={}
    def rd(n):
        b=b''
        while len(b)<n:
            x=inp.read(n-len(b))
            if not x:raise EOFError
            b+=x
        return b
    def wr(o):p=pickle.dumps(o,protocol=pickle.HIGHEST_PROTOCOL);out.write(_H.pack(len(p))+p);out.flush()
    while True:
        try:msg=pickle.loads(rd(_H.unpack(rd(_H.size))[0]))
        except EOFError:return
        op=msg[0]
        if op=='exit':wr('bye');return
        if op=='new':
            _,sid,name,flat=msg;s=S[sid]=Solver(name=name)
            for c in _flat_clauses(array('i',flat)):s.add_clause(c)
            wr(True)
        elif op=='solve':
            _,sid,flat,budget,assume,soft_at=msg;s=S[sid]
            for c in _flat_clauses(array('i',flat)):s.add_clause(c)
            if budget is not None:s.conf_budget(budget)
            t=None
            if soft and soft_at is not None:t=threading.Timer(max(0.0,soft_at-time.monotonic()),s.interrupt);t.daemon=True;t.start()
            try:r=s.solve_limited(assumptions=assume,expect_interrupt=True)
            finally:
                if t is not None:t.cancel();t.join()
                s.clear_interrupt()
            wr(r)
        elif op=='model':_,sid,flat=msg;wr(S[sid].get_model())
        elif op=='del':
            s=S.pop(msg[1],None)
            if s is not None:s.delete()
            wr(True)
        else:wr(('error',op))


# ---------------------------------------------------------------- host side
class SolverServer:
    """One child process (started lazily, restarted lazily after a kill)."""
    def __init__(self,soft=True):
        self.p=None;self.gen=0;self.kills=0;self.starts=0;self.events=[];self.soft=soft;self._ids=0

    def _start(self):
        env=dict(os.environ);env['PYTHONPATH']=str(ROOT)+(os.pathsep+env['PYTHONPATH'] if env.get('PYTHONPATH') else '')
        args=[sys.executable,'-m','experiments.solver_proxy_041','--serve']+([] if self.soft else ['--no-soft'])
        self.p=subprocess.Popen(args,stdin=subprocess.PIPE,stdout=subprocess.PIPE,cwd=str(ROOT),env=env,start_new_session=True,bufsize=0)
        self.gen+=1;self.starts+=1

    def alive(self):return self.p is not None and self.p.poll() is None

    def ensure(self):
        if not self.alive():self.p=None;self._start()

    def new_id(self):self._ids+=1;return self._ids

    def kill(self,why):
        if self.p is not None:
            try:os.killpg(self.p.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            try:self.p.wait(5)
            except Exception:pass
            for f in (self.p.stdin,self.p.stdout):
                try:f.close()
                except Exception:pass
        self.p=None;self.kills+=1;self.events.append(why)

    def call(self,msg,hard_at=None):
        """Send msg and wait for its reply until hard_at (time.monotonic); on timeout kill the child and raise Killed."""
        p=pickle.dumps(msg,protocol=pickle.HIGHEST_PROTOCOL);data=_H.pack(len(p))+p;fo=self.p.stdin.fileno();fi=self.p.stdout.fileno()
        mv=memoryview(data);i=0;buf=bytearray();need=None
        while True:
            rem=None if hard_at is None else hard_at-time.monotonic()
            if rem is not None and rem<=0:self.kill('hard deadline');raise Killed()
            r,w,_=select.select([fi],[fo] if i<len(data) else [],[],rem)
            if w:
                try:i+=os.write(fo,mv[i:i+(1<<20)])
                except BrokenPipeError:self.kill('broken pipe');raise Killed()
            if r:
                x=os.read(fi,1<<20)
                if not x:self.kill('child exited');raise Killed()
                buf+=x
                if need is None and len(buf)>=_H.size:need=_H.size+_H.unpack(bytes(buf[:_H.size]))[0]
                if need is not None and len(buf)>=need:return pickle.loads(bytes(buf[_H.size:need]))

    def factory(self,name):return SolverProxy(self,name)

    def close(self):
        if self.alive():
            try:self.call(('exit',),time.monotonic()+5)
            except Killed:pass
            except Exception:self.kill('close')
            if self.p is not None:
                try:self.p.wait(5)
                except Exception:self.kill('close')
        if self.p is not None:
            for f in (self.p.stdin,self.p.stdout):
                try:f.close()
                except Exception:pass
        self.p=None


class SolverProxy:
    def __init__(self,server,name):
        self.srv=server;self.name=name;self.sid=server.new_id();self.log=array('i');self.pending_from=0;self.gen=None
        self.budget=None;self.soft_at=None;self.hard_at=None;self.n_clauses=0;self.replays=0;self.deleted=False

    def add_clause(self,c):self.log.extend(c);self.log.append(0);self.n_clauses+=1
    def conf_budget(self,b):self.budget=b
    def interrupt(self):pass
    def clear_interrupt(self):pass
    def arm(self,s):now=time.monotonic();self.soft_at=now+s;self.hard_at=now+s+HARD_GRACE
    def disarm(self):self.soft_at=None;self.hard_at=None

    def _sync(self):
        """Return the clauses not yet in the child (bytes); replay the whole log into a fresh child if stale."""
        if self.srv.alive() and self.gen==self.srv.gen:
            flat=self.log[self.pending_from:].tobytes()
        else:
            self.srv.ensure();self.replays+=(self.gen is not None)
            self.srv.call(('new',self.sid,self.name,self.log.tobytes()),self.hard_at);self.gen=self.srv.gen;flat=b''
        self.pending_from=len(self.log);return flat

    def solve_limited(self,assumptions=(),expect_interrupt=False):
        try:
            flat=self._sync();return self.srv.call(('solve',self.sid,flat,self.budget,list(assumptions),self.soft_at),self.hard_at)
        except Killed:return None

    def get_model(self):
        if not (self.srv.alive() and self.gen==self.srv.gen):raise AssertionError('get_model on a stale solver')
        flat=self.log[self.pending_from:].tobytes()
        if flat:raise AssertionError('get_model with unsent clauses')
        return self.srv.call(('model',self.sid,b''))

    def delete(self):
        if not self.deleted and self.srv.alive() and self.gen==self.srv.gen:
            try:self.srv.call(('del',self.sid),time.monotonic()+5)
            except Killed:pass
        self.deleted=True;self.log=array('i')


class HardHook:
    """arm(fn, s) with fn the bound interrupt of a SolverProxy: soft deadline now + s (in the child), hard kill at
    now + s + HARD_GRACE (host)."""
    def __init__(self):self.armed=0

    def arm(self,fn,s):p=fn.__self__;p.arm(max(0.0,s));self.armed+=1;return p

    def disarm(self,p):p.disarm()


if __name__=='__main__':
    if '--serve' in sys.argv:serve(soft='--no-soft' not in sys.argv)
