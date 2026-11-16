"""Brute-force guesses for Attrib attribute names: hash candidate CamelCase names (1-3 words from a physics/gameplay vocabulary)
with tools/attrib_hash.py and keep the ones equal to a key found in the gameplay/main/attribdb2 vaults.
Matches are hash collisions only if the name is nonsense; a 64-bit match on a plausible name is strong evidence. Writes docs/listings/attrib_names.tsv."""
import sys, re, time, itertools, pathlib, csv, collections
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import attrib_hash as H, attrib_slots as sl

R = pathlib.Path(__file__).resolve().parent.parent
V = R / 'unpacked_data/decoded/data0/data'
VAULTS = {'gameplay': 'attribdbgameplay/gameplayattribdb.big_x/data/attribdbgameplay/attribdb.vlt',
          'main': 'attribdb/attribdb.vlt', 'db2': 'attribdb2/attribdb.vlt'}

VOCAB = """ball pitch surface turf grass concrete wall post net goal floor ground air drag friction restitution bounce spin magnus lift
gravity mass radius velocity speed angular linear damping decay scale min max threshold multiplier coefficient factor rate time delay duration
height width length angle power force impulse kick shot pass cross volley header chip finesse curve swerve trap control touch dribble tackle
jostle shield skill flair combo buffer window static dynamic rolling slide skid stop stick roll pivot turn sprint jog run walk stand idle
accuracy error noise random bias offset range distance near far short long low high mid medium big small tiny strength balance weight
influence head hips foot leg arm body player keeper goalkeeper team defender attacker opponent ai cpu pressure mark cover support
user manual auto assist aim target zone area box circle line side end corner penalty free throw set play move group blend curve
contact collision impact hit block save dive reach catch punch clear intercept receive first second third power low drive lob
loose possession gain lose win success fail chance probability prob ratio fraction percent amount level tier rating attribute
x y z in out on off enable disable use apply start end begin finish peak top bottom left right front back forward backward
sidestep stepover nutmeg panna rainbow flick feint fake touch juggle trick style""".split()
VOCAB = sorted(set(VOCAB))
CORE = 'ball surface pitch wall friction restitution bounce spin drag air ground static dynamic rolling min max scale threshold multiplier factor speed angle velocity height radius time power force mass control touch dribble kick shot pass tackle jostle shield skill low high left right front back x y z'.split()


def forms(parts):
    seen = set()
    for sep in ('', '_'):
        for f in (sep.join(p.capitalize() for p in parts), parts[0] + sep.join(p.capitalize() for p in parts[1:]),
                  sep.join(parts), sep.join(p.upper() for p in parts)):
            if f not in seen:
                seen.add(f)
                yield f


def main():
    keys = {}
    for nm, v in VAULTS.items():
        recs, sk, cnt = sl.records(str(V / v))
        for ck, off, slots in recs:
            keys.setdefault(ck, ('collection', nm))
            for (k, val, f) in slots:
                keys.setdefault(k, ('slot', nm))
    print(len(keys), 'target keys,', len(VOCAB), 'vocabulary words', flush=True)
    found = {}
    t0 = time.time()
    n = 0
    for r in (1, 2, 3):
        for combo in itertools.product(CORE if r == 3 else VOCAB, repeat=r):
            if r == 3 and len(set(combo)) < 3:
                continue
            for f in forms(list(combo)):
                n += 1
                h = H.name_hash(f)
                if h in keys:
                    found[h] = f
        print('words', r, 'done', n, 'hashes', len(found), 'matches', round(time.time() - t0), 's', flush=True)
    with open(R / 'docs/listings/attrib_names.tsv', 'w', encoding='utf-8', newline='') as fh:
        w = csv.writer(fh, delimiter='\t')
        w.writerow(['key_hash64', 'name', 'kind', 'vault'])
        for h, nm in sorted(found.items(), key=lambda x: x[1]):
            w.writerow(['%016x' % h, nm, keys[h][0], keys[h][1]])
    print('DONE', len(found), flush=True)


if __name__ == '__main__':
    main()
