from pathlib import Path
from shutil import copy2, rmtree
from os import getenv

def copies(mode, src, dest, glob):
  if mode == "clean": rmtree(Path(dest)); return
  (a,b) = (dest,src) if mode == "into" else (src,dest)
  fpB = Path(b); fpB.mkdir(parents=True, exist_ok=True)
  for fp in Path(a).glob(glob): copy2(fp, fpB)
def run(mode, rels):
  glob = getenv("glob", "*.java")
  for (fp,fpD) in rels: copies(mode, fp, fpD, glob)

from sys import argv
if __name__ == "__main__":
  mode = (argv[1:] or ["from"])[0]
  run(mode, [("", "src/main/java"), ("tests", "src/test/java")])
