"""For each file where git-blame attributes >=50% of lines to the user (from blame_ownership.tsv),
find upstream files (at the fork commit) with the same basename and report the fraction of the
file's non-blank, non-comment lines that appear verbatim (whitespace-stripped) in that upstream twin.
A high overlap means the file is a copy/move of upstream code, not original work.
Usage: python -I thesis-review/scripts/copy_check.py [FORK]"""
import subprocess, sys, os, collections
FORK = sys.argv[1] if len(sys.argv) > 1 else "9266caae9"
TSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blame_ownership.tsv")
def git(*a): return subprocess.run(["git", *a], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
def norm(text):
    out = []
    for l in text.splitlines():
        s = l.strip()
        if not s or s.startswith(("//", "/*", "*", "*/", "import ", "package ")): continue
        out.append(s)
    return out
by_name = collections.defaultdict(list)
for p in git("ls-tree", "-r", "--name-only", FORK).splitlines():
    by_name[os.path.basename(p)].append(p)
print("file\town_lines\tbest_upstream_twin\toverlap_pct")
for row in open(TSV, encoding="utf-8"):
    f, own, other, tot = row.rstrip("\n").split("\t")
    own, tot = int(own), int(tot)
    if tot == 0 or own / tot < 0.5 or own < 20: continue
    mine = norm(open(f, encoding="utf-8", errors="replace").read())
    if not mine: continue
    best, bestp = "-", 0.0
    for twin in by_name.get(os.path.basename(f), []):
        up = collections.Counter(norm(git("show", f"{FORK}:{twin}")))
        hit = sum(1 for l in mine if up[l] > 0)
        p = 100.0 * hit / len(mine)
        if p > bestp: best, bestp = twin, p
    print(f"{f}\t{own}\t{best}\t{bestp:.0f}")
