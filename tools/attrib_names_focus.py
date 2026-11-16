"""Focused Attrib-name search for the ball collection (4a881bff272a2d28): 1-4 words from a small ball-physics vocabulary,
CamelCase / lower / UPPER / underscore forms, matched against the keys of the gameplay vault. Appends to docs/listings/attrib_names.tsv."""
import sys, time, itertools, pathlib, csv
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import attrib_hash as H, attrib_slots as sl
from attrib_names_bruteforce import forms, V, VAULTS, R

FOCUS = """ball air ground floor pitch wall post net goal surface rolling sliding spin angular linear drag damping decay friction resistance
restitution bounce mass radius speed velocity max min threshold epsilon tolerance cutoff limit coefficient factor scale multiplier magnus lift
curve gravity stop rest sleep low high top back side kick pass shot dribble touch static dynamic roll skid grip turf concrete grass
amount rate time delay vertical horizontal normal tangent impact bounce loss energy keep retain per tick frame second""".split()
FOCUS = sorted(set(FOCUS))


def main():
    keys = {}
    recs, sk, cnt = sl.records(str(V / VAULTS['gameplay']))
    for ck, off, slots in recs:
        keys.setdefault(ck, 'collection')
        for (k, val, f) in slots:
            keys.setdefault(k, 'slot')
    have = {r['key_hash64'] for r in csv.DictReader(open(R / 'docs/listings/attrib_names.tsv'), delimiter='\t')}
    print(len(keys), 'target keys,', len(FOCUS), 'words', flush=True)
    found = {}
    t0 = time.time()
    n = 0
    for r in (1, 2, 3, 4):
        for combo in itertools.product(FOCUS, repeat=r):
            if len(set(combo)) < r:
                continue
            for f in forms(list(combo)):
                n += 1
                h = H.name_hash(f)
                if h in keys and '%016x' % h not in have:
                    found[h] = f
        print('words', r, 'hashes tried', n, 'new matches', len(found), round(time.time() - t0), 's', flush=True)
        with open(R / 'docs/listings/attrib_names_focus.tsv', 'w', encoding='utf-8', newline='') as fh:
            w = csv.writer(fh, delimiter='\t')
            w.writerow(['key_hash64', 'name', 'kind'])
            for h, nm in sorted(found.items(), key=lambda x: x[1]):
                w.writerow(['%016x' % h, nm, keys[h]])
    print('DONE', len(found), flush=True)


if __name__ == '__main__':
    main()
