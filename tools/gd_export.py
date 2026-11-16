"""Export decoded ANT GD.STRM data to docs/listings/*.tsv. Layout rules are the INFERRED ones in tools/gdstrm.py
(validated on: GUID resolution 4,157/4,157 transition endpoints; float offsets on PartProperty/InertiaTensorScale = 1.0).
Usage: python tools/gd_export.py   (reads unpacked_data/loose/{ant,common}.cbac.dec)"""
import sys, math, collections, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import gdstrm

R = pathlib.Path(__file__).resolve().parent.parent
OUT = R / 'docs' / 'listings'


def tsv(name, header, rows):
    with open(OUT / name, 'w', encoding='utf-8') as f:
        f.write('\t'.join(header) + '\n')
        for r in rows:
            f.write('\t'.join('' if x is None else str(x) for x in r) + '\n')
    print(name, len(rows), 'rows')


def g(v):
    return '%.6g' % v if isinstance(v, float) else v


def main():
    b = gdstrm.load(str(R / 'unpacked_data/loose/ant.cbac.dec'))
    cls = {c['hash']: c for c in gdstrm.classes(b)}
    bl = gdstrm.blocks(b)
    byg = {}
    for blk in bl:
        c = cls.get(blk[2])
        if c:
            gg = gdstrm.block_guid(b, c, blk)
            if gg:
                byg[gg] = (c, blk)

    def label(gg):
        t = byg.get(gg)
        if not t:
            return '?'
        return '%s:%s' % (t[0]['names'][0], gdstrm.block_name(b, t[0], t[1]))

    by_name = {c['names'][0]: c for c in cls.values() if c['names']}

    # 1. state-flow transitions with conditions
    tr = by_name['StateFlowTransitionAsset']
    rows = []
    for blk in [x for x in bl if x[2] == tr['hash']]:
        v = gdstrm.decode(b, tr, blk)
        fr = byg.get(gdstrm.ref_one(b, tr, blk, 'From'))
        to = byg.get(gdstrm.ref_one(b, tr, blk, 'To'))
        cond_t = [label(x) for x in gdstrm.ref_list(b, tr, blk, 'ConditionsRequiredTrue')]
        cond_f = [label(x) for x in gdstrm.ref_list(b, tr, blk, 'ConditionsRequiredFalse')]
        rows.append((gdstrm.block_name(b, *fr) if fr else None, gdstrm.block_name(b, *to) if to else None,
                     g(v.get('DestinationPhase', 0.0)), v.get('BranchInPhase'), v.get('BranchInAny'),
                     '|'.join(cond_t), '|'.join(cond_f)))
    tsv('animation_state_graph.tsv',
        ['from', 'to', 'destination_phase', 'branch_in_phase', 'branch_in_any', 'conditions_true', 'conditions_false'], rows)

    # 2. gestures
    gc = by_name['GestureAsset']
    rows = []
    for gb in [x for x in bl if x[2] == gc['hash']]:
        gname = gdstrm.block_name(b, gc, gb)
        for si, sg in enumerate(gdstrm.ref_list(b, gc, gb, 'Steps')):
            sc, sb = byg[sg]
            sv = gdstrm.decode(b, sc, sb)
            for mg in gdstrm.ref_list(b, sc, sb, 'Matchers'):
                mc, mb = byg[mg]
                mv = gdstrm.decode(b, mc, mb)
                p = {k: g(x) for k, x in mv.items() if not k.startswith('_')}
                if 'MinAngle' in p:
                    p['MinAngle_deg'] = '%.1f' % math.degrees(mv['MinAngle'])
                    p['MaxAngle_deg'] = '%.1f' % math.degrees(mv['MaxAngle'])
                rows.append((gname, si, g(sv.get('MinTicks')), g(sv.get('MaxTicks')), sv.get('KeepMatching'),
                             mc['names'][0], gdstrm.block_name(b, mc, mb), ';'.join('%s=%s' % kv for kv in p.items())))
    tsv('gestures.tsv', ['gesture', 'step', 'min_ticks', 'max_ticks', 'keep_matching', 'matcher_class', 'matcher_name', 'params'], rows)

    # 3. collision tags
    cc = by_name['CollisionTag']
    cnt = collections.Counter()
    for blk in [x for x in bl if x[2] == cc['hash']]:
        v = gdstrm.decode(b, cc, blk)
        cnt[(g(v['restitution']), g(v['forceMagnitude']), g(v['forceYaw']), g(v['forcePitch']), v['useForceAsBallOut'])] += 1
    tsv('collision_tags.tsv', ['restitution', 'forceMagnitude', 'forceYaw', 'forcePitch', 'useForceAsBallOut', 'instances'],
        [k + (n,) for k, n in cnt.most_common()])

    # 4. time-scale controllers
    tc = by_name['TimeScaleControllerAsset']
    rows = []
    for blk in [x for x in bl if x[2] == tc['hash']]:
        v = gdstrm.decode(b, tc, blk)
        rows.append((gdstrm.block_name(b, tc, blk),) + tuple(g(v.get(k)) for k in ('mMinScale', 'mMaxScale', 'mXMin', 'mXMax', 'mEndTime', 'mRepeatTime')))
    tsv('time_scales.tsv', ['name', 'minScale', 'maxScale', 'xMin', 'xMax', 'endTime', 'repeatTime'], rows)

    # 5. tackle tags
    tk = by_name['TackleTag']
    cnt = collections.Counter()
    for blk in [x for x in bl if x[2] == tk['hash']]:
        v = gdstrm.decode(b, tk, blk)
        cnt[v.get('Duration')] += 1
    tsv('tackle_tag_durations.tsv', ['Duration(raw u32)', 'instances'], cnt.most_common())

    # 6. common.cbac physics bodies
    c2 = gdstrm.load(str(R / 'unpacked_data/loose/common.cbac.dec'))
    cl2 = {c['hash']: c for c in gdstrm.classes(c2)}
    pp = next(c for c in cl2.values() if c['names'][:1] == ['PartProperty'])
    rows = []
    for blk in [x for x in gdstrm.blocks(c2) if x[2] == pp['hash']]:
        v = gdstrm.decode(c2, pp, blk)
        nm = gdstrm.block_name(c2, pp, blk)
        rows.append((nm,) + tuple(g(v[k]) for k in ('Mass', 'Density', 'MaxLinearVelocity', 'MaxAngularVelocity', 'Restitution',
                                                      'StaticFriction', 'DynamicFriction', 'LinearDragRate', 'AngularDragRate', 'InertiaTensorScale')))
    tsv('physics_part_properties.tsv', ['name', 'Mass', 'Density', 'MaxLinearVelocity', 'MaxAngularVelocity', 'Restitution', 'StaticFriction',
                                        'DynamicFriction', 'LinearDragRate', 'AngularDragRate', 'InertiaTensorScale'], rows)


if __name__ == '__main__':
    main()
