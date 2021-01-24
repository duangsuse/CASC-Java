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
def proj(s, deps, javac="1.8", plugins=["org.apache.maven.plugins:maven-compiler-plugin:3.8.1"], sep=","):
  root = E("project", E("modelVersion", "4.0.0")); gav(lambda: root, _cd(s))
  runUnlessEnv("packaging", "pom", lambda t,v: root.append(E(t,v)))
  runUnlessEnv("parent", "", lambda t,v: gav(lambda: also(root.append, E(t)), _cd(v)))
  runUnlessEnv("dependencyManagement", "",
               lambda t,v: root.append(E(t, listE("dependency", opOnEach(gavs, [s+getenv(t+"Suffix", ":pom:import") for s in v.split(sep*2)]))) ))
  deps = listE("dependency", opOnEach(gavs, deps))
  runUnlessEnv("plug", "", lambda t,v: plugins.extend(v.split(sep))) # dyload more
  plugs = listE("plugin", opOnEach(gav, map(_cd, plugins)) )
  plugs.getchildren()[0].append(E("configuration", E("source",javac), E("target",javac)) )
  for ee in deps, E("build", plugs): root.append(ee)
  def setsText(ae, x): ae().text = x
  runUnlessEnv("module", "", lambda t,s: root.append(listE(t, opOnEach(setsText, s.split(sep)))))
  return root

def addEnvironParse(ap, envs, helps):
  for name in envs: ap.add_argument("-"+name, help=helps.get(name) or "sets environ variable")
  cfg = ap.parse_args(); d = vars(cfg)
  for name in envs:
    if d[name] != None: environ[name] = d[name]
  return cfg
if __name__ == "__main__":
  from argparse import ArgumentParser
  ap = ArgumentParser("mvng", description="generate pom.xml", epilog="names are separated by ',' and first '-' in artifactId denotes group name (require , separated)")
  dm = "dependencyManagement"; names = ["packaging", "parent", "plug", "module", dm, dm+"Suffix"]
  helps = {"plug": "plugin coordinates", "module": "module names", dm: "special dependency in this tag, with default -Suffix"}
  ap.add_argument("coord", help="project g:a:v")
  ap.add_argument("deps", nargs="*", help="depend g:a:v[:type:scope] s")
  ap.add_argument("-o", help="write to dir")
  cfg = addEnvironParse(ap, names, helps)
  pom = etree.tostring(proj(cfg.coord, cfg.deps), pretty_print=1)
  if cfg.o == None: print(pom.decode())
  else: __import__("pathlib2").Path(cfg.o).joinpath("pom.xml").write_bytes(pom)
