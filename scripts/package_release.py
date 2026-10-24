"""Assemble one full-root portable archive with unchanged historical baseline."""
import json,hashlib,zipfile
from pathlib import Path
from scripts.verify_release import ROOT,sha,listed,verify
TARGET=ROOT.parent/(ROOT.name+'.zip')

def pack():
    manifest=ROOT/'MANIFEST.sha256'
    if manifest.exists():raise RuntimeError('manifest exists; refuse overwriting earlier archive')
    paths=listed()
    manifest.write_text(''.join(f'{sha(p)}  {rel}\n' for rel,p in sorted(paths.items())))
    record=verify()
    if TARGET.exists():raise RuntimeError('release already exists; refuse overwrite')
    with zipfile.ZipFile(TARGET,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=7,allowZip64=True) as z:
        for rel,p in sorted({**paths,'MANIFEST.sha256':manifest}.items()):
            z.write(p,arcname=ROOT.name+'/'+rel)
    with zipfile.ZipFile(TARGET) as z:
        assert z.testzip() is None
        for rel,p in sorted({**paths,'MANIFEST.sha256':manifest}.items()):
            assert hashlib.sha256(z.read(ROOT.name+'/'+rel)).hexdigest()==sha(p)
    report={'schema':'bgr90.package-check.v1','status':'passed','name':TARGET.name,
            'sha256':sha(TARGET),'bytes':TARGET.stat().st_size,'files':len(paths)+1,
            'contained_root':ROOT.name+'/','manifest':'passed','zip_crc':'passed',
            'local_release_checks':record,'native_windows':'not tested'}
    (ROOT.parent/(ROOT.name+'-package-verification.json')).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    return report

if __name__=='__main__':pack()
