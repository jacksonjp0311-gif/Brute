"""Host-side wall guard for brute.api.certify16d (study 047). New file; lives in experiments/ because it uses a thread
(the API itself starts none). TimerHook.arm(interrupt, seconds) starts a threading.Timer that calls interrupt() after the
guard; disarm(token) cancels it and returns True if the guard had fired (certify16d then flags the call 'wall_guard')."""
from __future__ import annotations
import threading

__all__=['TimerHook']


class _Tok:
    __slots__=('timer','fired')

    def __init__(self):self.timer=None;self.fired=False


class TimerHook:
    def __init__(self):self.arms=0;self.fires=0

    def arm(self,interrupt,seconds):
        t=_Tok();self.arms+=1

        def fire():
            t.fired=True;self.fires+=1;interrupt()
        t.timer=threading.Timer(seconds,fire);t.timer.daemon=True;t.timer.start();return t

    def disarm(self,tok):
        if tok is None:return False
        tok.timer.cancel();tok.timer.join();return tok.fired
