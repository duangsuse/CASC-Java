#!python
from lxml import etree, builder; E=builder.E
def also(op, x): op(x); return x
def _noun2(s): return s[:-1]+"ies" if s[-1]=="y" else s+"s"
def listE(tag, op): e=E(_noun2(tag)); op(lambda: also(e.append, E(tag)) ); return e
def _cd(s): return s.split(":") # Maven "coord"
def gav(ae, cd, GAV=_cd("groupId:artifactId:version:type:scope")): e=ae(); [e.append(E(t,v)) for (t,v) in zip(GAV, cd) if v!=""]
def _gavAName(g, a): return a.replace("-", g[g.rfind(".")+1:], 1) # expand org.g:-a to :g-a
def gavs(ae, s, sep=","): cd=_cd(s); (g,a)=cd[:2]; [gav(ae, (g,_gavAName(g,aa))+tuple(cd[2:])) for aa in a.split(sep) if aa!=""] if sep in a else gav(ae,cd)

from os import getenv, environ
def runUnlessEnv(name, deft, op): v=getenv(name, deft); None if v==deft else op(name, v)
opOnEach = lambda op, xs: lambda ae: [op(ae, x) for x in xs]
opSets = lambda name: lambda ae, x: ae().set(name, x) # exposed eval() API
opSetsChild = lambda name: lambda ae, x: ae().append(E(name, x))
opSetsText = lambda ae, x: setattr(ae(), "text", x)
def proj(s, deps, sep=","):
  (javac, compilerV) = getenv("compilerVer", "1.8,3.8.1").split(sep)
  plugins = ["org.apache.maven.plugins:maven-compiler-plugin:"+compilerV]
  root = E("project", E("modelVersion", "4.0.0")); gav(lambda: root, _cd(s))
  runUnlessEnv("packaging", "pom", lambda t,v: root.append(E(t,v)))
  runUnlessEnv("parent", "", lambda t,v: gav(lambda: also(root.append, E(t)), _cd(v)))
  runUnlessEnv("dependencyManagement", "",
               lambda t,v: root.append(E(t, listE("dependency", opOnEach(gavs, [s+getenv(t+"Suffix", ":pom:import") for s in v.split(sep*2)]))) ))
  deps = listE("dependency", opOnEach(gavs, deps))
  runUnlessEnv("plug", "", lambda t,v: plugins.extend(v.split(sep*2))) # dyload more
  plugs = listE("plugin", opOnEach(gav, map(_cd, plugins)) )
  plugs.getchildren()[0].append(E("configuration", E("source",javac), E("target",javac)) )
  for ee in deps, E("build", plugs): root.append(ee)
  runUnlessEnv("module", "", lambda t,s: root.append(listE(t, opOnEach(opSetsText, s.split(sep)))))
  return root

def addEnvironParse(ap, envs, helps):
  for name in envs: ap.add_argument("-"+name, help=helps.get(name) or "sets environ variable")
  cfg = ap.parse_args(); d = vars(cfg)
  for name in envs:
    if d[name] != None: environ[name] = d[name]
  return cfg

xmlp = etree.XMLParser(no_network=False, recover=True)
tagFlat = "__flat__"
def postprocessXml(root, actions):
  for (act, idx) in actions:
    (path,expr) = act.split("=", 1)
    es = root.xpath(path)
    (mode,code) = expr.split(":", 1)
    if mode=="file": ee=etree.parse(code, xmlp).getroot()
    elif mode=="read": ee=etree.fromstring(code, xmlp)
    elif mode=="eval": ee=eval(code, globals())
    elif mode=="text": ee=E(*code.split(":"))
    elif mode=="new": ee=E(code)
    if idx != None: es = [es[idx]]
    if ee.tag == tagFlat:
      for e in es:
        for ee1 in ee.getchildren(): e.append(ee1)
    else:
      for e in es: e.append(ee)
from argparse import ArgumentParser, Action
class CollectArg(Action): # for postprocess
  def __init__(self, option_strings, dest, copyname="", **kwargs): super(CollectArg,self).__init__(option_strings, dest, **kwargs); self._cpname=copyname
  def __call__(self, parser, cfg, values, option_string=None):
    d = vars(cfg)
    getOrPut(d, self.dest, list).append((values, d[self._cpname]))
def getOrPut(d, k, op_init):
  v = d.get(k)
  if v != None: return v
  else: v1=op_init(); d[k]=v1; return v1

if __name__ == "__main__":
  def _parse(dm="dependencyManagement"):
    ap = ArgumentParser("mvng", description="generate pom.xml", epilog="names are separated by ',' and first '-' in artifactId denotes group name (require , separated)", fromfile_prefix_chars="@")
    arg = ap.add_argument
    arg("coord", help="project g:a:v")
    arg("deps", nargs="*", help="depend g:a:v[:type:scope] s")
    arg("-o", help="write to dir")
    arg("-coding", default="UTF-8")
    arg("-fat", default=False, action="store_true", help="add unnecessary attributes")
    arg("-x", action=CollectArg, copyname="xi", help="add equations (xpath=file/read/text/new/eval:)")
    arg("-xi", type=int, help="adds only at selector result[i]")
    names = ["packaging", "parent", "plug", "module", dm, dm+"Suffix", "compilerVer"]
    helps = {"plug": "plugin coordinates", "module": "module names", dm: "special dependency in this tag, with default -Suffix", "compilerVer": "javac and maven.compiler"}
    return addEnvironParse(ap, names, helps)
  cfg = _parse()
  root = proj(cfg.coord, cfg.deps)
  postprocessXml(root, cfg.x or [])
  if cfg.fat:
    root.set("xmlns", "http://maven.apache.org/POM/4.0.0")
    a = [(None,"http://www.w3.org/2001/XMLSchema-instance"), ("schemaLocation","http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd")]
    for i in range(1, len(a)): (k,v)=a[i]; root.set(etree.QName(a[i-1][1],k), v)
  pom = etree.tostring(root, pretty_print=1, encoding=cfg.coding, xml_declaration=cfg.fat)
  if cfg.o == None: print(pom.decode(cfg.coding))
  else: __import__("pathlib").Path(cfg.o).joinpath("pom.xml").write_bytes(pom)
