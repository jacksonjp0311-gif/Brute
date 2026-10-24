import ast,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
STDLIB=set(sys.stdlib_module_names)


def imports(path):
    tree=ast.parse(path.read_text())
    for node in ast.walk(tree):
        if isinstance(node,ast.Import):
            for a in node.names:yield a.name,0
        elif isinstance(node,ast.ImportFrom):
            yield (node.module or ''),node.level


class AdapterBoundary(unittest.TestCase):
    def files(self,*dirs):
        out=[p for d in dirs for p in (ROOT/d).rglob('*.py')]
        self.assertTrue(out);return out

    def test_adapter_imports_only_api(self):
        for p in self.files('adapters'):
            for mod,level in imports(p):
                if level>0:continue  # relative import inside the adapter package
                top=mod.split('.')[0]
                ok=mod=='brute.api' or mod.startswith('brute.api.') or (top in STDLIB)
                self.assertTrue(ok,f'{p.relative_to(ROOT)} imports {mod}')
                for banned in ('bgr','brute.core','experiments','scripts','numpy'):
                    self.assertFalse(mod.startswith(banned),f'{p} imports {mod}')

    def test_core_never_imports_adapter(self):
        dirs=[d for d in ('bgr89','bgr90','brute','experiments','scripts') if (ROOT/d).exists()]
        for p in self.files(*dirs):
            for mod,level in imports(p):
                self.assertFalse(level==0 and mod.split('.')[0]=='adapters',f'{p.relative_to(ROOT)} imports {mod}')

    def test_adapter_has_no_side_channel(self):
        for p in self.files('adapters'):
            tree=ast.parse(p.read_text())
            for node in ast.walk(tree):
                if isinstance(node,ast.Name):self.assertNotIn(node.id,('open','__import__','eval','exec'),p)
                if isinstance(node,ast.Attribute):self.assertNotIn(node.attr,('environ','getenv','read_text','read_bytes'),p)
            for mod,_ in imports(p):self.assertNotIn(mod.split('.')[0],('os','importlib','pathlib','io','subprocess','socket'),p)


if __name__=='__main__':unittest.main()
