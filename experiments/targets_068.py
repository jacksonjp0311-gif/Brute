"""Study BRUTE-0640-REALDECODER-068 adapter (experiments/BRUTE_PLAN_068.json interface): unmodified CPython incremental decoders
driven through their PUBLIC interface only. Per job: one codecs.getincrementaldecoder(codec)('replace') object; per action one
.decode(bytes([b])) call (final=False). The reading is 2 bits of the str that call returned: (non-empty, contains U+FFFD); (0, 0)
before any call. read() re-reads the cached last reading and never calls the decoder (state-preserving re-reads). No getstate,
setstate, reset, buffer or private attribute is touched (GFID68 checks this file's AST). Never imports the ground truth."""
import codecs

TARGETS={'U3':('utf-8',(0x41,0x80,0xE1)),'U4':('utf-8',(0x41,0x80,0xF1)),'W16':('utf-16-le',(0x41,0xD8,0xDC))}
ALLOWED_ATTRS=('getincrementaldecoder','decode')


def reading(s):return (1 if len(s)>0 else 0,1 if '\ufffd' in s else 0)


class Target:
    def __init__(self,name):
        codec,bs=TARGETS[name];self.name=name;self.codec=codec;self.bs=bs;self.k=len(bs)
        self.dec=codecs.getincrementaldecoder(codec)('replace');self.last=(0,0);self.steps=0

    def read(self):return self.last

    def act(self,a):
        if isinstance(a,bool) or not isinstance(a,int) or a not in range(self.k):raise ValueError('bad action')
        out=self.dec.decode(bytes([self.bs[a]]));self.steps+=1;self.last=reading(out);return self.last


def replay(name,acts):
    """Clean readings of a fresh decoder fed acts (GFID68 a)."""
    t=Target(name);return [t.read()]+[t.act(a) for a in acts]
