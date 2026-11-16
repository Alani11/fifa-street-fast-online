# Physics and simulation constants — what the workspace actually contains

Source of every number: the file and key named in the "Source" column, read from `unpacked_data/decoded/data0/` (the decoded copy of `engine_data/Game/data0.big`). `tools/verify_all.py` and the QC script in section 8 re-read these values.
No textbook physics is filled in. Where the data is absent, this document says so.

## 1. Requested vs. found

| Requested item | Status |
|---|---|
| Ball friction coefficients | **Not extracted.** The physics asset schema (`PartProperty`: Restitution, StaticFriction, DynamicFriction, drag rates) is located (section 7) but its instances are not decoded; the hashed gameplay-vault values (section 5) are the other candidate |
| Turf vs. concrete bounce restitution | **Not found in readable form** (same caveat) |
| Spin / Magnus force curves | **Not found in readable form** (same caveat) |
| Wall-rebound dampening | **Not found in readable form** (same caveat) |
| Pitch walls, nets, goal and penalty areas | **Found** (section 2) |
| Player-contact radii and fall threshold | **Found** (section 3) |
| AI shot-aim target zones | **Found** (section 4) |
| Gameplay tuning vault (hashed keys) | **Found but anonymous** (section 5) |
| Decision neural nets (pass, shot, tackle, dribble) | **Found** (section 6) |
| Be A Pro performance deltas | **Found** (section 9) |

What was searched: all 28 MB of decoded and nested files, case-insensitive for `restitut`, `friction`, `magnus`, `bounce`, `spin`, `gravity`, `drag`, `elastic`, `collision`, `rebound`, `wall`. The only hits are rendering (`pitchBounce` is a shader texture name in `ball.lua`/`player.lua`, `debugpitchbounce`/`debugcollision` are debug render passes in `initialize.lua`), audio (`BallBounce`, `BALLHIT_STADIUM_SELECTOR` with surface tags `CONCRETE`, `GLASS`, `STAD_POST`, `STAD_NET`, `ADBOARDS`, `VIDEO_SCREEN`), and the `streetdefault.ini` keys below. Audio surface tags show the engine distinguishes surfaces for sound; they carry no restitution numbers.
The physics classes exist as attribute collections (`ClassRefSpec_physics`, `_collision`, `_physical_play`, `_kick_pass`, `_kick_shot`, `_kick_error`, `_locomotion`, `_defense` in `attribdb.bin`), but their attribute names are stored as 64-bit hashes that cannot be reversed here (section 5).

## 2. Pitch, goals and rules (`streetdefault.ini`)

Units are as commented in the file ("full-pitch = … (feet)"); the street values are in the engine's own units.

| Key | Value | Comment in file |
|---|---|---|
| `AI_PITCH_WALLS_ENABLED` | 1 | |
| `AI_ADD_WALL_LOCATORS_AROUND_PITCH` | 0 | |
| `AI_AD_BOARD_SIDELINE_DIST` | 100 | full-pitch = 13.1 (feet) |
| `AI_AD_BOARD_ENDLINE_DIST` | 100 | full-pitch = 12.3 (feet) |
| `AI_NET_WIDTH` | 15 | full-pitch = 24 (feet) |
| `AI_NET_HEIGHT` | 5 | full-pitch = 8 (feet) |
| `AI_NET_DEPTH_TOP` | 1 | full-pitch = 7.5 |
| `AI_NET_DEPTH_BOTTOM` | 3 | valid values: 5 (for box), 7.5, 10 |
| `AI_NET_SHAPE` | 1 | SHAPE_TRI; default 0 = SHAPE_BOX |
| `AI_NET_NUM_SUPPORTS` | 0 | |
| `AI_PENALTY_BOX_WIDTH` / `LENGTH` | 45 / 18 | "smaller box length than 18 breaks goal kick" |
| `AI_GOAL_BOX_WIDTH` / `LENGTH` | 45 / 18 | |
| `AI_PENALTY_SPOT_DIST` | 18 | |
| `AI_CENTER_CIRCLE_RADIUS` | 15 | |
| `AI_PENALTY_ARC_RADIUS` | 0 | |
| `USER_ALLOW_WALL_PASS` | 0 | |
| `AI_NO_SLIDE_TACKLE` | 1 | |
| `AI_FORCE_TACKLE_OFF` | 1 | |
| `IGNORE_OFFSIDE` | 1 | |
| `DISABLE_KNOCK_ON` | 1 | |
| `AI_PREVENT_CLEARANCE` | 1 | |
| `AI_PREVENT_DOUBLETEAM` | 1 | |

These files give wall existence and distances only; a rebound parameter, if one exists, is not named here.

## 3. Player contact, jostle and falls (`streetdefault.ini`)

| Key | Value |
|---|---|
| `ENABLE_ANTPHYSICS` | 1 |
| `LOWER_LEG_RADIUS_SCALE` | 0.02 |
| `FOOT_RADIUS_SCALE` | 0.01 |
| `JOSTLE_FAR_DISTANCE_AT_TOP_SPEED` | 4 |
| `[PHYSICS] FS4_FALL_THRESHOLD` | 0.6 |
| `[PHYSICS] FS4_IGNORE_AI_FALL_REQUEST` | 1 |
| `CONTEXTUAL_JOCKEY_DIST` | 28.0 |
| `MIN_CHECK_DIST_TO_LINE_FOR_OPPONENT_COVERING_DIR_TO_GOAL` | 6.0 |
| `AUTO_HIGH_RES_OPP_MIN_DIST_THRESHOLD` / `MAX` | 8 / 25 |
| `SKILLMOVES_BALL_CHECK_TOLERANCE` | 1.0 |
| `EVASIVE_DRIBBLING_ESTIMATE_TIME` | 6.0 |
| `PACE_CONTROL_MAX_INTENSITY` | 0.6875 |

`heroperf.ini` also has `COMPETING_THRESHOLD = 1.35` (comment: "meters").
How `FS4_FALL_THRESHOLD` and the leg radii enter the duel is **not recoverable here**: no formula text exists in the workspace.

## 4. `[AISHOOT]` table (`streetdefault.ini`)

Comments in the file say these are for net sizes (big = Futsal, med = 6v6/5v5, small = panna) and for "Finesse" shots (`F` prefix). Semantics of the numbers (fraction of what) are not stated.

| Net | LOW | MLO | MID | MHI | HI |
|---|---|---|---|---|---|
| BIG | 0.40 | 0.50 | 0.55 | 0.60 | 0.70 |
| MED | 0.40 | 0.45 | 0.50 | 0.55 | 0.60 |
| SMALL | 0.25 | 0.30 | 0.35 | 0.45 | 0.50 |
| FBIG | 0.40 | 0.45 | 0.50 | 0.55 | 0.60 |
| FMED | 0.35 | 0.40 | 0.45 | 0.50 | 0.55 |
| FSMALL | 0.25 | 0.30 | 0.35 | 0.40 | 0.45 |

## 5. Gameplay attribute vault (hashed)

`data/attribdbgameplay/gameplayattribdb.big` holds 103 collections, all of class key `ad303b8f42b3307e`. Under the inferred record layout (`binary_formats.md` section 3.3) 91 records parse into 1,505 slots, of which 837 carry the float flag (`0x4000`); frequent values are 1, 0, 0.5, 200, 2, 0.8, 0.6 and 10 (`docs/listings/gameplay_attrib_slots.csv`). One slot run in record `a98a5fe84eae4c56` is `3.0, 28.0, 120.0, 5.0, 5.0, 10.3` and others hold values such as 0.094 or 45, so tuning numbers are present, but:

* the 64-bit key hash is not reversed (known-answer test with FNV and Jenkins lookup8 variants: no match), so no value can be labelled "friction" or "restitution";
* 12 of 103 gameplay records (and about 30% of the main vault's records) do not fit the layout and were not read;
* slots with flags other than `0x4000` (about 45%) were not decoded;
* the vault does not say which class (physics, collision, kick, …) a collection belongs to: the class names live in `attribdb.bin` and the mapping between them and the 64-bit keys is unresolved.

## 6. Decision neural networks (`data/neuralnet`)

Topologies are verified (see `binary_formats.md` section 4): pass 15-15-15-15-1, shot 8-15-15-15-1, tackle 7-10-10-1, dribble 10-10-7-1. These are the only data-driven decision models in the workspace; a tackle model exists but its inputs, output scale, activation and any duel math around it are **unknown**.

## 7. Engine code: what the lifted C++ gives us

**Pipeline (done on the user's machine, from the user's own extracted game files):** ReXGlue recompiled `default.xex`, `fifadllzf.xex.dll` and `FootballCompEngzf.xex.dll` into C++ (`generated/.../fifastreet_recomp.*.cpp`, 158,942 functions named by guest address, each line commented with the original PowerPC instruction; a copy is at `C:\src\sim_recomp\generated_snapshot`, not part of this workspace). The build used VS 2022 Build Tools, clang 23 and ReXGlue `c94f5ebd` with the project patch and no source shims. The earlier statement in this document that the XEX was unreadable is superseded: the recompiler decodes it.
**Image dump:** a research hook in `Installer/recomp-template/src/fifastreet_app.h` (`OnPostLoadXexImage`, inert unless `FIFASTREET_DUMP_DIR` is set) wrote committed guest memory to `C:\src\sim_recomp\dump\`. `pass0_modules.bin` (76 MB, taken 60 s after load) has regions `0x82300000` (26.4 MB), `0x83C60000` (2.4 MB) and `0x83EC0000` (47 MB). `pass1_heap.bin` (7.5 MB) and `pass1_modules.bin` (1.6 MB) were taken at 240 s with the game at the menus and are **incomplete**: `ClassRefSpec_physics` is not in them. Reader: `tools/gdump.py`.

**Tools built on those two inputs (all heuristic linear scans of the instruction comments):**

| Tool | What it does | Output |
|---|---|---|
| `tools/string_xrefs.py` | `lis` + `addi`/`ori` pairs that land on NUL-terminated ASCII in the image | `docs/listings/string_xrefs.tsv`: 70,560 refs, 20,131 functions, 40,634 strings |
| `tools/showfn.py` | prints one function's PowerPC listing | stdout |
| `tools/fconsts.py` | resolves `lis` + `lfs/lwz/stw...` addresses in one function and reads the value from the dump | stdout |
| `tools/dataxref.py` | finds code that touches given data addresses | stdout |
| `tools/config_keys.py` | INI key to function, getter, default in `f1`, destination global | `docs/listings/config_keys.tsv`: 28 keys located, all calling the same getter `0x82627038` |

**Config reads:** every located key goes through `sub_82627038` (name in `r3`, default in `f1`, flag in `r5`). The caller caches the result in a global guarded by a bit flag. In `sub_830615D0` the result goes through `fctiwz` and `fcfid`, so the stored value is an **integer-truncated float**, stored at `0x83E2BF10..0x83E2BF1C`. Defaults and destinations are in `config_keys.tsv`. The code default and the shipped INI differ: for the four nutmeg keys the code default is 8000 / 10000 and the INI sets 6 / -16 / 24 / 16. The `default_guess` and `dest_global_guess` columns of that file come from a heuristic register tracker; the nutmeg rows were confirmed by hand against the listing, the others were not.
The first worked formula is the nutmeg ramp in `state_machine.md` section 8. It is derived from lifted code and **not runtime-verified**.

**Physics anchors found, no ball values:**
* The strings `Mass, Density, Inertia, MaxLinearVelocity, MaxAngularVelocity, Restitution, StaticFriction, DynamicFriction, LinearDragRate, AngularDragRate` (the field list of an asset class `PartProperty`, referenced by `sub_835E92E8`), `Gravity`, `MaxContacts`, `MaxIterations`, `FreezingThreshold` (world setup, `sub_835EA070` and `sub_835EA300`), `PlayerCollisionObject`, `CollisionWrapperAsset`, `WallChargeTag`, `BATTLE_COLLISION_FACE_TO_FACE_ANGLE` (`sub_82D8B310`, `sub_82DA5080`) and `MAX_WALL_MOVE_DELAY` (`sub_83095970`) are schema or key names. The numeric values live in asset data. `common.cbac` holds `PartProperty`; its 14 instances are now decoded (section 10) and they are **character body parts**, not the ball.
* No function was identified as ball integration, bounce, Magnus or wall rebound, and **no ball friction, restitution or spin value was extracted**. The only physics-asset instances found describe the character's body (section 10). The ball solver itself was found in the lifted code and partly traced (section 11); its material values are not yet identified.

## 8. Verification
Run `python tools/verify_all.py` for the structure checks. `tools/verify_docs.py` re-reads every `| KEY | value |` row of sections 2–3 and the `[AISHOOT]` table of this file, plus the `heroperf.ini` constants quoted in section 9, and fails on any mismatch (75 values checked, 0 mismatches).

## 9. `heroperf.ini` is a performance rating, not duel physics

`[HERO_PERF_CONST]`: `COMPETING_THRESHOLD = 1.35` (meters), `INITIAL_PERFORMANCE = 0.2` ("-1.0f to 1.0f, example: 0.2 is equivalent to a 60%", which matches `(p+1)/2 = 0.6`), `NUM_PASSES_THRESHOLD = 3`, `THREAT_POSSESSOR_THRESHOLD = 40` game seconds, `INP_THRESHOLD_NON_POSSESSOR_NOT_DEFENDER = 90`, `INP_THRESHOLD_NON_POSSESSOR_DEFENDER = 60`, `OOP_THRESHOLD_TEAMMATE_IS_POSSESSOR = 90`, `OOP_THRESHOLD_TEAMMATE_IS_NOT_POSSESSOR = 60`.
Role sections `[HERO_PERF_DEFENDER]`, `[HERO_PERF_MIDFIELDER]`, `[HERO_PERF_STRIKER]` and `[HERO_PERF_UNLOCKED]` (identical to the midfielder values for the keys checked) give per-event additive deltas to that rating, with `INP` = in possession and `OOP` = out of possession. Selected defender values: `TACKLE_THREAT_SUCCESSFUL_INP = 0.3`, `TACKLE_THREAT_SUCCESSFUL_OOP = 0.2`, `TACKLE_THREAT_UNSUCCESSFUL_INP = -0.06`, `TACKLE_LOST = -0.1`, `TACKLE_AVOIDED = 0.04`, `GOAL = 0.6`, `GOAL_OWN = -0.3`, `LOST_CHALLENGE_INP = -0.09`, `WON_CHALLENGE_INP_NON_DEFENDING_3RD = 0.15`. Midfielder and striker sections use the same keys with smaller deltas (e.g. striker `TACKLE_AVOIDED = 0.08`, midfielder `TACKLE_AVOIDED = 0.06`).
Clamping, decay and how the rating feeds into the match are not in the file. This is not a 1v1 attacker/defender resolution formula.

## 10. Character physics bodies (decoded from `common.cbac`)

`docs/listings/physics_part_properties.tsv`: the 14 `PartProperty` instances (fields and offsets in `binary_formats.md` section 9). Every instance has `Density` 1, `MaxLinearVelocity` 1e+32 (a "no limit" sentinel), `MaxAngularVelocity` 100, `Restitution` 0, `LinearDragRate` 0, `AngularDragRate` 0 and `InertiaTensorScale` 1.

| Body part | Mass | Static / dynamic friction |
|---|---|---|
| `part_LeftUpLeg`, `part_RightUpLeg` | 7.6 | 0.25 / 0.25 |
| `part_LeftLeg`, `part_RightLeg` | 3.5 | 0.4 / 0.4 |
| `part_LeftFoot`, `part_RightFoot` | 0.6 | 0 / 0 |
| `part_Hips`, `part_Spine3` | 22 | 0.6 / 0.6 |
| `part_Head` | 7 | 0.6 / 0.6 |
| `part_LeftArm`, `part_RightArm` | 2.8 | 0 / 0 |
| `part_LeftForeArm`, `part_RightForeArm` | 2 | 0 / 0 |
| `part_AITrajectory` | 1 | 0.6 / 0.6 |

Units (the masses look like kilograms) are not stated in the file. The related `CapsuleVolumeProperty` (11 instances, `HalfHeight`) and `BoxVolumeProperty` (3, `Dimensions`) were found but not exported. `BallOffsetsAsset` (1 instance, `Rotations` and `Translations` as vec4) was found and not interpreted. Animation-attached collision reactions (restitution 0 or 0.4, force vectors) are in `state_machine.md` section 11.

## 11. Ball solver trace (lifted code, partial, not runtime-verified)

**What was found.** The ball is simulated by EA's `fizix::BallSolver`, identified from allocation-tag strings in the image: `fizix::BallSolver::CreateBall` (`sub_82F72240`), `CreateField` (`sub_82F72328`), `CreateWalls` (`sub_82F74898`), `CreateEnvironment` (`sub_82F75AF0`, `sub_82F75BC8`), `CreateSoccerposts` (`sub_82F723E8`), `CreateEATechSoccernet` (`sub_82F7F610`), `CreateFlag`, `CreateRigidDoll`, and the solver constructor with its `mAirflow` member (`sub_82F742A8`). Gameplay code reaches it through `Action::BallTrajectory::mBallSolver` (`sub_82DB2008`, called from `sub_82DBA610` and `sub_82DBCC68`) and `Action::BallPrescriptor::mBallSolver` (`sub_82D91EA0`).

**Verified from code and image values** (constants read from `pass0_modules.bin`, scalar and vector loads resolved by `tools/fconsts.py`):
* In `sub_82DB2008` the solver is given a gravity vector of `(0, -9.81, 0)` (`-9.81` at `0x823BDE58`). The code multiplies it by `3.2808` (`0x8230684C`, metres to feet) and by `1/60` (`0x82310C44`, 0.0166667) twice, which gives about `-0.00894` feet per tick squared. The pitch values in `streetdefault.ini` are commented in feet, so the solver's length unit is feet and its tick is 1/60 s. This function then steps the solver in a loop with a step of `f31` (the product of two floats from its parameter struct, `80(r11)` and `84(r11)`), a number of sub-steps taken from `68(r29)` and a main count `lfs 64(r29) / f31` truncated to an integer.
* The solver keeps a 600-entry history ring buffer of ball state (`sub_82D92C50`, `sub_82D929E0`, element stride 16 bytes, modulo 600): a trajectory log, not physics.

**Default ball parameter struct** (`sub_82F69360`, which fills the ball info at `144(r1)` before `CreateBall`; the ball constructor `sub_82F6A870` only copies it). The vector-load constants it reads are:

| Image address | Value |
|---|---|
| `0x82305B98` | 0.2 |
| `0x823070E8` | 0.01 |
| `0x82302BE0` | 0.0 |
| `0x823CE5A4` | 0.454 |
| `0x823CE5A8` | 0.365 |
| `0x823CE5AC` | 0.1968 |
| `0x823CE5B0` | 167.32 |
| `0x82367BB4` | 0.8 |

They are splatted into the info struct at offsets 16, 32, 48 and 64 (0.365 and 0.454 splatted separately, 0.8 splatted, 0.2 and 0.01 permuted together). The constructor `sub_82F6A870` copies info `+16/+32/+48/+64` to object `+32/+48/+64/+80`; object `+112` is the position, `+128` the orientation quaternion, `+144` the linear velocity and `+160` the angular velocity (from `sub_82F663C8`, below). **Which field is mass, radius, restitution or drag is not confirmed**, and the next paragraph shows `0.365` is not specific to the ball.

**Other tables and candidates (unlabeled):**
* `sub_82F66368` and `sub_82F66480` copy per-index rows from mutable tables at `0x83E17F10` (32-byte rows), `0x83E17DB0` (64-byte rows) and two float arrays at `0x83E17CCC` and `0x83E17CD8`. At 60 s after launch these hold 1.0 multipliers and zeros, with one row of 0.005 and 0.0001, so they are not fixed physical constants.
* `sub_82F6A2D0` (359 instructions, vector math: `vrsqrtefp` normalizations, dot products, comparisons) uses `3.2808`, `0.3048`, `60`, `pi`, `1.442695` (log2 e), `12150`, `-2.39e-05`, `-0.000142`, `-8.22e-05`, `0.35`, `0.1`, `3e-06`, `2e-06`, `0.675` and `0.0333`. It looks like a geometric or aerodynamic evaluation, but what it computes is **not established**.
* `sub_82F8F148` (5,512 instructions, 836 floating-point operations) is the largest function in the solver range and the most likely main step; `sub_82F6FB78`, `sub_82F7D1D8`, `sub_82F71858` and `sub_82F74B90` (constants 0.75, 0.14, 0.08, next to `CreateWalls`) are the next largest. None was read in full.

**Field and wall default structs** (read the same way; the first element of each vector load is the scalar used):
* `sub_82F6CFC0` (fills the field info at `240(r1)` before `CreateField`) reads `0.5` (`0x823CF88C`), `0.05` (`0x82302CDC`), `0.0`, `0.6` (`0x823D4534`; the next three values in that row are 15.75, 31.5 and 18.9), `0.1` (`0x82312730`), `100.0` (`0x82304700`) and `pi/2` (`0x823CE43C`; the next two are 0.785398 and 1.414214).
* `sub_82F6D278` (fills the wall info at `384(r1)` before `CreateWalls`) reads `0.5` (`0x823CF88C`), `5.0` (`0x823CE494`), `-1`, `1` and the doubles `-1.875` and `1.875` (`0x82304188`, `0x82302D48`).

These are the values the solver is *initialised with*; whether `0.6` is a surface friction, `0.5` a restitution or `5.0` a wall height is **not established**, and the same constants (0.5, 0.6, 100) are shared with unrelated code. The values could also be overwritten by the caller before the solver runs (`sub_82DB2008` copies fields `72(r29)`, `76(r29)`, `80(r29)`, `88(r29)` and `92(r29)` into the structs). Read them as leads, not as the game's friction or restitution.

**Method table and roles (read, partly inferred from the instruction pattern):**
* `sub_82F663C8` looks like the integrator: `pos(+112) += vel(+144) * dt` (`vmaddfp`), then a quaternion update of `+128` from the angular velocity at `+160` with a factor of 0.5 and a renormalization (`vrsqrtefp`, two Newton steps). Inference from the operations, not from a name.
* `sub_82F6DC90` adds a vector from its argument (`+80`) to the position when its squared length is positive.
* `sub_82F6AE50` computes a parametric crossing (`(y - y1) / (y2 - y1)`) of a segment against a level, with degree/radian constants (`0.017453`, `57.29578`).
* `sub_82F6A930` (244 instructions) has the shape of an impulse contact solver: dot products of relative velocity with a normal (`vmsum3fp128`), reciprocal terms, a clamp on a tangential part scaled by the `obj+32` lanes, and updates of `+144` and `+160`. It reads one constant from a mutable table (`0.55` ×4 at `0x83E17FE0`) and `FLT_MAX` (`0x823CE424`). Its role as the surface-contact response, and the meaning of `0.55`, are **not confirmed**.

**Runtime evidence (heap dump `pass1_heap.bin`, taken at the menus, 240 s after launch):** two objects with the info layout exist at `0x7019ACB0` and `0x7019BD00` (guessed object bases; the `0.365` splat sits at base `+32`). The second one holds vertices at about `(-62.99, 4.76, +-7.64)` feet and `(+62.99, 0, 0)` next to it, i.e. a goal-line position with half-width about 7.6 ft and height about 4.8 ft, which matches the INI net (`AI_NET_WIDTH` 15, `AI_NET_HEIGHT` 5). So that struct is a **post or net shape**, and `0.365` is a generic radius used there too. This **weakens** the earlier reading of `0.365` as the ball's radius: the ball's own object was not located in the dump, and the dump was taken at the menus.

**Still open:** ball restitution on turf versus concrete, friction, spin/Magnus and wall-rebound damping. To close them: (1) dump guest memory again while a match is running, with the flag-file trigger idea (the ball object will then exist, and its `+32..+96` values show which defaults were overridden); (2) read `sub_82F8F148` (5,512 instructions) for the step order; (3) trace the caller of `sub_82DB2008` to see which fields `72(r29)`..`92(r29)` set.

## 12. Gameplay vault ball attributes (names recovered by hashing; file values)

The name hash was recovered from the lifted code: `sub_8269C930(str)` calls `sub_8269C508(str, len, 0xABCDEF0011223344)`, which is Jenkins `lookup8` (`tools/attrib_hash.py`). All 38 `ClassRefSpec` class names hash exactly to their vault collection keys (verified), and CamelCase attribute names found by vocabulary search (`tools/attrib_names_bruteforce.py`, `tools/attrib_names_focus.py`; 64-bit exact matches) are in `docs/listings/attrib_names.tsv` and `attrib_names_focus.tsv`.
Values below are read from `gameplayattribdb` collection `4a881bff272a2d28` (27 slots; slot layout inferred, `binary_formats.md` section 3.3):

| Attribute | Slot | Value |
|---|---|---|
| `BallLinearDrag` | 5 | 0.003 |
| `BallAngularDrag` | 0 | 0.0015 |
| `BallDynamicFriction` | 4 | 0.6 |
| `BallRestitution` | 8 | 0.9 |
| `BallStaticFriction` | 11 | 0.72 |
| `MagnusCoefficient` | 22 | 0.4 |
| `MagnusDragMultiplier` | 23 | 31.3 |

Other named attributes (other collections): `Restitution` 0.0625, `ImpulseHead` 0.35, `ImpulseHips` 1.2, `InfluenceHead` 0.5, `InfluenceHips` 1.0, `StopAngle` 55, `StopRadius` 1.5, `BalanceThreshold` 0.8. The remaining 16 slots of the ball collection are unnamed (values include 0.998, 0.972, 0.994, 100, 100, 10, 15, 0.01, 0.2, 0.72, 0.8, 0.82, 2e+06, 1, 0.03).
**Runtime check (running game, at the menus, `tools/procmem.py`):** the game's guest memory is mapped at host base `0x100000000` (the image string `fizix::BallSolver::CreateBall` sits at host `0x1823CE61C` = base + guest `0x823CE61C`). The ball collection is resident as a table of 27 sixteen-byte slots (`u64 key`, `u32 big-endian float`, `u32 tag`) at guest `0xB2336670` to `0xB2336820`, a range (`0xA0000000` and up) that my earlier guest dumps did not cover. In memory the slots are in a different order than in the file, but **all 27 values equal the file values (27 of 27)**, so the game loads these numbers unchanged: restitution 0.9, static friction 0.72, dynamic friction 0.6, linear drag 0.003, angular drag 0.0015, Magnus coefficient 0.4, Magnus drag multiplier 31.3, and the 20 other slots listed above. A second structure at guest `0xB22DC400` (stride 0x120 bytes: key, a type hash `e22228fbb3c209d8`, pointers) is the attribute schema table, not the values.
**Usage tracing attempts (all negative):** `tools/watch_reads.py` sets x86-64 hardware read/write watchpoints through the Windows debug API (validated on a test process: 5,028 hits on a known read). Four sessions on the live game saw **zero accesses** to the values of `BallRestitution`, `BallLinearDrag`, `BallStaticFriction` and `MagnusCoefficient` (one 20 s in play; one 150 s while restarting a match; one 150 s on all four host mirrors of `BallRestitution` while restarting a match; one attached 1 s after launch for 150 s). A scan of the live process for 16-byte splat copies of 0.9, 0.72, 0.6, 0.003, 0.0015 and 0.4 found no group of three or more of these constants together (0.72 and 0.0015 had no splat at all). So within what was observed, the game does not read these exact addresses after attach and does not keep a vectorized copy; the consumption most likely happens in loading before attach, or through another representation (scalar copies, or a copy into the solver struct under different values). Open.
**Not mapped to formulas:** no code site that uses these constants was identified (the `Ball*` keys do not appear as immediates in the lifted code, so the generated attribute class reads by slot layout), so the drag form, units and Magnus formula remain untraced. The 16 unnamed slots keep their values but not their roles.

## 13. Live `Ball` objects (runtime, running match, `tools/procmem.py`)
Scanning the running game for the `Ball` vtable pointer (`0x823CE5D4`) finds 24 distinct `Ball` objects (each visible at four host mirrors; spacing 0x160 bytes, so an array of bodies) and, for `0x823CE6C8`, the `BallSolver` objects. Layout, confirmed on live data:

| Offset | Content | Live value |
|---|---|---|
| `+0` | vtable pointer | `0x823CE5D4` |
| `+32` | scalar splat (x4) | **0.365**, equal on all 24 objects |
| `+48` | scalar splat (x4) | **0.454** |
| `+64` | scalar splat (x4) | **0.65** (the constructor default `0.8` from `sub_82F69360` is overridden at creation) |
| `+80` | vec3 + pad | (0.1, 0.01, 0.009, 0) |
| `+112` | position (feet) | e.g. (55.5, 5.71, -7.60) |
| `+128` | orientation quaternion | unit length (e.g. 0.067, -0.628, 0.523, 0.573) |
| `+144` | linear velocity (feet per 1/60 s tick) | e.g. (0.585, -0.297, -0.075) |
| `+160` | angular velocity (radians per tick) | e.g. (0.0018, -0.0172, 0.0143) |

**Verified:** balls resting on the floor sit at `y = 0.365` or `0.371`, so `+32` (0.365 ft, about 0.111 m) **is the ball radius**. The quaternion norm is about 1 and the position/velocity fields match the integrator `sub_82F663C8` (`pos += vel * dt`, `quat` updated from angular velocity).
**Source of the numbers:** the vault has a collection `22ebadd1eb0a5999` (gameplay vault, also present in the main and attribdb2 vaults) with 3 slots: `a9cdef6a901331dd` = 0.454, `5af80006a82256ae` (non-float, flags `0x200`) and `fb95494f91ca0cce` = 0.365 (key names not recovered). `0.65` occurs in several other collections; which one feeds `+64` was not determined.
**Not measured:** the three moving balls sampled (about 50 Hz for 4 s) repeat the same few states every 0.78 s, so they are AI trajectory-prediction instances re-simulated from a fixed start each frame, not the live match ball (the game was not in active play during the sample). No real decay, bounce or Magnus curve was obtained, and the vault values `BallRestitution` 0.9 / friction / drag (section 12) were not seen to act on these objects.


## 14. Contact response `sub_82F6A930` decoded (static, lifted code; not runtime-verified)

`sub_82F6A930` (244 PPC instructions, `fifastreet_recomp.261.cpp`) is reached only by a tail-branch (`b 0x82f6a930`) from `sub_82F6DC90` (`fifastreet_recomp.103.cpp`). That wrapper first does `A.pos(+112) += C.vec(+80)` when `|C.vec(+80)|^2 > 0` (penetration correction), then runs the impulse step. `A = r3` is the ball-like body, `C = r4` is a contact record. Field use read from the instructions:

| Operand | Use |
|---|---|
| `C+48` | contact normal `n` |
| `C+144` | velocity of the other body, `vB`; `vB.n = dot(C+144, n)` |
| `A+144` | `vA`; `vA.n = dot(A+144, n)` |
| `A+48`, `C+128` | masses (per-lane) `m1`, `m2` |
| `C+16` | restitution `e` (per-lane) |
| `C+32` lanes 0/1/2 | friction coefficient `mu` (lane 0) and two further coefficients (lanes 1, 2) that scale the tangential and spin responses |
| `A+32` | radius lanes used for the spin (`n x omega * r`) coupling |
| `A+160` | angular velocity `omega` |
| `0x83E17FE0` | constant `0.55` (x4), used as `k` and `1/k` (about 1.818) |

Normal part (second path, when the bodies approach), one-dimensional collision with restitution:

```
vn' = (m1*vA.n + m2*vB.n + e*m2*(vB.n - vA.n)) / (m1 + m2)
dv  = vn' - vA.n
```

When the bodies separate, a clamped variant is used (`max`/`min` against 0). Tangential part:

```
vt = (vA - n*(vA.n)) + (n x omega)*r        # surface speed at the contact point
if |vt|^2 > threshold:  t = vt/|vt|; friction impulse = t * (0.55 * mu * dv) # opposes vt, capped by Coulomb
A.vel   += n*dv - friction impulse * (1/0.55)   # linear part
A.omega += (cross terms) * (1/0.55 - 1)          # spin part
```

Last step: if any `|component|` of the new `A+144` or `A+160` exceeds the float limit constant, the vector is zeroed (overflow guard).

**Confidence:** operand roles read from vector ops (`vmsum3fp128` dots, `vpermwi128` cross products, Newton-refined `vrefp`/`vrsqrtefp`). The momentum-exchange formula is exact in form; which gameplay-vault values (`BallRestitution` 0.9, friction) fill `C+16`/`C+32` is **not** traced (the contact records are built by the virtual caller of `sub_82F6DC90`, not yet found), and the meaning of 0.55 (I suspect a solid-sphere inertia factor) is unconfirmed.

**Correction to section 11:** `sub_82F8F148` was named as the likely main step. Its reads (`80(r31) - 76(r31)`, `-8284(r19)`, many `vmsum3fp128` and `fsel`) include a start/end pair subtracted to a duration and four helper calls that look like transform/animation work; it is not the ball integrator. Treat it as unidentified.

### 14.1 Measured ball motion (live, demo scene, `tools/ball_track.py`, ~30 Hz samples = 2 physics ticks each)

Ball object `0x1ac306440` (one free ball, speed 0.2 ft/tick) from `docs/listings/_ball_track2.json` (scratch, not shipped):

* Position step matches velocity: `vx = -0.20` per tick moves the ball `-0.40` ft per 2-tick sample.
* Gravity: `vy` falls by `0.0175..0.018` per sample, i.e. about **0.009 ft/tick^2 = 32.4 ft/s^2** at 60 ticks/s (real-world 32.17). A ball at rest holds `vy = -0.018` (gravity added each sample, floor contact removes it).
* One bounce: `vy` goes from about `-0.042` (before contact, extrapolated) to `+0.023`, an effective restitution of roughly **0.55** off the floor. One event only: treat as an estimate, not a constant. It is the same number as the `0.55` table value in `sub_82F6A930`, which may be a coincidence.
* Horizontal speed on that bounce drops `-0.198 -> -0.185` (about 6.5 %), the friction term; later samples decay about 0.8 %/sample while rolling.
* Ball y never goes below `0.300` while squashed against geometry (`0.365` rest, radius) and parks at `y = 99.9` for one sample when the object is re-spawned.
Not measured: Magnus/spin curves, wall rebound, drag in the air at speed.
