"""Study BRUTE-0730-RESUME-077 adapter (experiments/BRUTE_PLAN_077.json; same interface and rules as experiments/targets_073.py): unmodified CPython incremental decoders driven
through their PUBLIC interface only and WITHOUT RESETS. One codecs.getincrementaldecoder(codec)('replace') object is created in
__init__ and never replaced; there is no reset method. act(a) is one .decode(bytes([b])) call (final=False). The reading is 2 bits of
the str that call returned: (non-empty, contains U+FFFD); (0, 0) before the first action. read() returns the cached last reading.
No getstate, setstate, reset, buffer or private attribute is touched (GNORESET77 checks this file's AST). Never imports the truth."""
import codecs

TARGETS={'SJ':('shift_jis',(0x41,0x81,0x40)),'KR':('euc_kr',(0x41,0xA1,0xA1)),'B5':('big5',(0x41,0x81,0x40)),'U32':('utf-32-le',(0x41,0x00,0x11)),
         'U8S':('utf-8-sig',(0xEF,0xBB,0xBF)),'U16B':('utf-16-be',(0x00,0xD8,0xDC)),'EJ4':('euc_jis_2004',(0x41,0x8F,0xA1)),'HK':('big5hkscs',(0x41,0x81,0x40)),
         'HZ':('hz',(0x41,0x7E,0x7B)),'JO':('johab',(0x41,0x84,0x41))}
ALLOWED_ATTRS=('getincrementaldecoder','decode')


def reading(s):return (1 if len(s)>0 else 0,1 if '\ufffd' in s else 0)


class Target:
    def __init__(self,name):
        codec,bs=TARGETS[name];self.name=name;self.codec=codec;self.bs=bs;self.k=len(bs);self.steps=0
        self.dec=codecs.getincrementaldecoder(self.codec)('replace');self.decoder_objects=1;self.last=(0,0)

    def read(self):return self.last

    def act(self,a):
        if isinstance(a,bool) or not isinstance(a,int) or a not in range(self.k):raise ValueError('bad action')
        out=self.dec.decode(bytes([self.bs[a]]));self.steps+=1;self.last=reading(out);return self.last


def replay(name,actions):
    """Clean readings before and after each action of one reset-free action sequence on ONE fresh decoder (GFID76)."""
    t=Target(name);return [t.read()]+[t.act(a) for a in actions]
