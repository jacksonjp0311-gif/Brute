"""Study BRUTE-0650-RESETDECODER-069 adapter (experiments/BRUTE_PLAN_069.json interface): unmodified CPython incremental decoders
driven through their PUBLIC interface only. reset() makes a FRESH codecs.getincrementaldecoder(codec)('replace') object (no .reset()
call); act(a) is one .decode(bytes([b])) call (final=False). The reading is 2 bits of the str that call returned: (non-empty,
contains U+FFFD); (0, 0) for a fresh object. read() returns the cached last reading and never calls the decoder. No getstate,
setstate, reset method, buffer or private attribute is touched (GFID69 checks this file's AST). Never imports the ground truth."""
import codecs

TARGETS={'U3':('utf-8',(0x41,0x80,0xE1)),'U4':('utf-8',(0x41,0x80,0xF1)),'W16':('utf-16-le',(0x41,0xD8,0xDC)),
         'EJ':('euc_jp',(0x41,0x8F,0xA1)),'GB':('gb18030',(0x41,0x81,0x30))}
ALLOWED_ATTRS=('getincrementaldecoder','decode')


def reading(s):return (1 if len(s)>0 else 0,1 if '\ufffd' in s else 0)


class Target:
    def __init__(self,name):
        codec,bs=TARGETS[name];self.name=name;self.codec=codec;self.bs=bs;self.k=len(bs);self.steps=0;self.resets=0;self.dec=None
        self.last=(0,0)

    def reset(self):
        self.dec=codecs.getincrementaldecoder(self.codec)('replace');self.last=(0,0);self.resets+=1;return self.last

    def read(self):return self.last

    def act(self,a):
        if isinstance(a,bool) or not isinstance(a,int) or a not in range(self.k):raise ValueError('bad action')
        out=self.dec.decode(bytes([self.bs[a]]));self.steps+=1;self.last=reading(out);return self.last


def replay(name,word):
    """Clean readings after a fresh decoder and after each action of word (GFID69 a)."""
    t=Target(name);r=[t.reset()];return r+[t.act(a) for a in word]
