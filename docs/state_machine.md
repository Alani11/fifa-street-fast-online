# Locomotion, skill-move and duel logic — what the workspace actually contains

All values come from `unpacked_data/decoded/data0/` (decoded `data0.big`); file and key are named for each item.
The animation state graph is in `Game/data/ant.cbac` (70.6 MB decoded, `GD.STRM`) and is **decoded** (sections 9 and 10): 1,048 named states, 4,157 transitions, 135 input gestures with tick windows. Only the layout rules in `binary_formats.md` section 9 are inferred; each one is cross-checked in `tools/verify_all.py`. So this document lists the states and transitions the INI files prove exist, and marks everything else as missing. Nothing here is reconstructed from memory of other games. Section 8 is derived from the lifted C++ and is marked as not runtime-verified.

## 1. Requested vs. found

| Requested | Status |
|---|---|
| Input buffer windows (frame counts, seconds) | **Partly found.** Gesture steps carry `MinTicks`/`MaxTicks` windows (section 10), e.g. 0-15, 0-5, 0-12 ticks. The unit (game ticks) and the separate `InputBufferDoubleTapHold` signal value (`common.cbac`) are not confirmed. |
| Skill-move combo chains | **Found as a state graph** (section 9): e.g. `Rainbow_Variation_Jog_base` -> `..._success_flick_R/L`, `..._fail_1/2/3`, `Idle`. Which gesture triggers which edge is not resolved (most edges carry no condition, section 9). The `ESIA` sequence bodies remain undecoded. |
| Animation blend durations | **Partly found.** `BlendCurveAsset` (1,099 instances) has only a curve type and a phase-sync flag; no duration field was seen. Playback-rate limits are in `time_scales.tsv` (section 11). |
| Flair / style scoring multipliers | **Not in workspace.** `AI_FORCE_FLAIR = 1` and the keyboard "flair" key are the only hits. |
| 1v1 attacker/defender duel resolution | **Not in workspace as a formula.** The nearest data are the `nnettackle`/`nnetdribble` network topologies and the Be A Pro rating deltas (`physics_spec.md` sections 6 and 9). |

## 2. Locomotion states and transitions proven by `streetdefault.ini`

Names below are quoted from the keys; a state's internals are unknown.

| Item | Source key | Value |
|---|---|---|
| Locomotion controller asset | `LOCO_ASSET_NAME` | `FS4_LocoController` |
| Databases the controller reads | `RUN_CURVE_DATABASE_NAME`, `MOVE_GROUP_DATABASE_NAME`, `TURN_DATABASE_NAME`, `PASS_SHOT_DATABASE_NAME`, `TRAP_DATABASE_NAME`, `REACTIONS_DATABASE_NAME`, `DRIBBLE_TURN_DATABASE_NAME`, `STUMBLE_TURN_DATABASE_NAME` | `FS4_RunCurveDatabase`, `FS4_MoveGroupDatabase`, `FS4_TurnContextDatabase`, `FS4_PassShotContinuousContacts`, `FS4_TrapContinuousContacts`, `FS4_ReactionsDatabase`, `FS4_DribbleTurnDatabase`, `FS4_Turns_from_tackle_pose` |
| State-flow exit nodes | `STATE_FLOW_EXIT_NODES` | `FS4_ExitToFifa`, `FS4_Loco` |
| Pace shielding | `PACE_SHIELDING_ENABLED` / `PACE_SHIELDING_BREAKS_OUT_TO_FIFA` | 1 / 1 |

Transitions enabled by flag (all `1` in the file):

| From → to | Key |
|---|---|
| Stand → Stand (interrupt) | `ENABLE_STAND_TO_STAND_INTERRUPT` |
| Stand → Micro-stop (interrupt) | `ENABLE_STAND_TO_MICROSTOP_INTERRUPT` |
| Stand → Pace / FIFA (interrupt) | `ENABLE_STAND_TO_PACEANDFIFA_INTERRUPT` |
| Pace shielding → FIFA locomotion (break-out) | `PACE_SHIELDING_BREAKS_OUT_TO_FIFA` |
| Skill move → regular move when the ball-contact test fails | `SKILL_MOVES_DEFER_TO_MOVE_WHEN_CONTACT_TEST_FAILS` |

Switches that are off: `ENABLE_SLOW_DRIBBLE = 0`, `ENABLE_BUTTON_TRIGGERED_HIGH_RES_DRIBBLE = 0`, `ENABLE_SKILL_MOVE_TIME_SCALE = 0`, `ENABLE_PLAYER_OFFENSIVE_RUNS = 0`, `EARLY_PASS_ENABLED = 0`, `PLAYER_RELATIVE_RIGHT_STICK = 0` (comment: "0 = Street Fighter").

## 3. Timing and tuning numbers

| Key | Value | Comment in file |
|---|---|---|
| `STAND_TIME_SCALE` | 1.0 | |
| `STAND_FIFA_EXIT_TIME_SCALE` | 1.2 | |
| `PACE_CONTROL_TIME_SCALE` | 1.0 | |
| `PACE_CONTROL_MAX_INTENSITY` | 0.6875 | |
| `SNAP_MG_MIN_PLAYBACK_RATE` / `MAX` | 1.0 / 1.6 | |
| `SKILLMOVES_PACE_ENABLED` | 1 | |
| `SKILLMOVES_ALWAYS_ENABLE_QUERY` | 1 | |
| `FIRST_TIME_SKILL_MOVES_MUST_HAPPEN_IN_STRIDE` | 1 | |
| `SKILLMOVES_BALL_CHECK_TOLERANCE` | 1.0 | |
| `JUEGO_FANTASTICO_USES_SKILL_MOVES` | 1 | |
| `SKILL_EP_FEEDBACK_ANIM_TIME_ARENA` | 6000 | no unit stated |
| `MIN_NUTMEG_ELAPSED_TIME_ZERO_PROB` / `MAX_…` | 6.0 / -16.0 | |
| `MIN_NUTMEG_ELAPSED_TIME_FULL_PROB` / `MAX_…` | 24.0 / 16.0 | |
| `MIN_MARK_URGENCY_RAMP_UP_START_RATIO` / `MAX_…` | 0.3 / 0.5 | |
| `MIN_MARK_URGENCY_RAMP_UP_END_RATIO` | 0.0 and 0.25 | key appears twice in the file with these values |
| `CONTEXTUAL_JOCKEY` / `ENABLE_CONTEXTUAL_JOCKEY` | 1 / 1 | |
| `CONTEXTUAL_JOCKEY_DIST` | 28.0 | |
| `MAX_ASSIST_TICKS_MANUAL_SWITCH` | 0.0 | |
| `DEFENDING_MANUAL_TACKLE_PROTOTYPE` | 1 | |
| `DEFENDING_BLOCK_PROTOTYPE` | 1 | |
| `AI_FORCE_FLAIR` | 1 | |

The nutmeg keys are now explained by lifted code in section 8. The mark-urgency pair is still inference from names. How elapsed time maps to probability (linear or not) and what the `MAX_` values (negative, 16) mean is not stated anywhere in the workspace. No curve is invented here.

## 4. Inputs

`buttondata.ini` (Xbox 360 pad) and `buttondatakeyboardmouse.ini` map physical inputs to virtual buttons; gameplay uses the `VB_AI_*` set, menus use `VB_FE_*`.

| Virtual button | Xbox 360 pad | Keyboard |
|---|---|---|
| `VB_AI_LS_*` (move) | left stick | arrow keys |
| `VB_AI_RS_*` (right stick) | right stick | numpad 8/2/4/6 |
| `VB_AI_A` / `B` / `X` / `Y` | A / B / X / Y | A / D / S / W |
| `VB_AI_LB` / `RB` | left / right shoulder | Q / E |
| `VB_AI_LT` / `RT` | left / right trigger | Z / C |
| `VB_AI_R3` | right stick click | Tab |
| `VB_AI_LDPAD_*` | D-pad | Home / PageUp / End / PageDown |

The launcher help string (`ui/lang.js`) names the keyboard roles: Shift sprint, Space "Street Ball Control (hold)", Q "flair (hold)", E "juggle". That text is launcher UI. The INI proves only the key-to-button mapping (Q→`VB_AI_LB`, E→`VB_AI_RB`); that the launcher's "flair" and "juggle" labels refer to those buttons is **not verified** in the engine data.
The buffering window, stick-gesture recognition for skill moves, and combo timing are not in these files.

## 5. Skill-move AI sequences

`data/skillmoveai` has `generic` (227 sequences), `messi` (42) and single-sequence folders for `cronaldo`, `davidvilla`, `ribery`, `robinho`. The index and file-id relationship is verified, so a sequence can be looked up by id. What a sequence encodes (steps, durations, success checks) is **unknown**, so no state transition table can be extracted from them yet.

## 6. Scoring-adjacent data
`accomplishments.ini` (400 entries) uses trigger codes plus reward-string names such as `vpskillmoves2..5`, `vpstandingtackle1/2`, `vpslidingtackle1/2`. It shows that skill moves and tackles are counted for progression; it has no flair multiplier.

## 7. What would close the gaps
1. Decrypted game code (XEX) or symbols, see `physics_spec.md` section 7.
2. The animation assets `FS4_*` (not present).
3. A name dictionary for the 64-bit Attrib hash, to label the 805 gameplay tuning keys.
Until one of these exists, the duel, combo and buffer maths cannot be written down without guessing.

## 8. Nutmeg attempt probability (from lifted code, not runtime-verified)

Function `sub_830615D0` (`fifadllzf`) reads the four `*_NUTMEG_ELAPSED_TIME_*` keys through the config getter `sub_82627038` and caches each as an integer-truncated float:

| Key | Global | Code default | Shipped INI |
|---|---|---|---|
| `MIN_NUTMEG_ELAPSED_TIME_ZERO_PROB` | `0x83E2BF1C` | 8000 | 6.0 |
| `MAX_NUTMEG_ELAPSED_TIME_ZERO_PROB` | `0x83E2BF18` | 8000 | -16.0 |
| `MIN_NUTMEG_ELAPSED_TIME_FULL_PROB` | `0x83E2BF14` | 10000 | 24.0 |
| `MAX_NUTMEG_ELAPSED_TIME_FULL_PROB` | `0x83E2BF10` | 10000 | 16.0 |

The listing (`python tools/showfn.py sub_830615D0`, from the loads of those four globals onward) contains an `fsel` / `fmadds` / `fdivs` sequence. `0.0` is loaded from `0x82302BE0` and `1.0` from `0x82301EB4` (values read from the pass-0 image dump). It computes:

```
t = clamp(x, 0, 1)                           # x = the function's float argument (f1 at entry, kept in f30)
Z = MIN_ZERO + t * (MAX_ZERO - MIN_ZERO)     # lerp of the two ZERO_PROB bounds
F = MIN_FULL + t * (MAX_FULL - MIN_FULL)     # lerp of the two FULL_PROB bounds
p = clamp((e - Z) / (F - Z), 0, 1)           # e = float returned by sub_82EAD0D0(this->field_424)
```

`sub_82D64840(f1 = 0.0, f2 = 1.0)` is called earlier and its result is kept in `f27`. The code then compares `f27 < p`, and in a second branch gated by a flag `f27 < f26`, where `f26` is read through a pointer argument. That `sub_82D64840(0, 1)` is a random draw in [0, 1) is **inferred** from its arguments and use, not verified. If so, a nutmeg is attempted when the draw is below `p`.
With the INI values: `t = 0` ramps 6 to 24 (p = 0 at e <= 6, 1/3 at 12, 1 at 24); `t = 1` ramps -16 to 16 (p = 0.5 at e = 0, 1 at e >= 16); `t = 0.5` ramps -5 to 20. The units of `e` and the meaning of `x` are **unknown**: `e` comes from `sub_82EAD0D0` and `x` from this function's caller, and neither was followed.
Verification gap: the constants come from the code and the image 60 s after launch. The four globals read 0 in the dump because they initialize lazily on first use, so the INI overrides were not read back from a running game.

## 9. Animation state graph (decoded from `ant.cbac`)

`docs/listings/animation_state_graph.tsv` lists every `StateFlowTransitionAsset` (4,157) as `from -> to` with destination phase, branch flags and condition names. Nodes are `StateFlowNodeControllerAsset` blocks (1,108 instances, 1,048 distinct names), including many `*_conduit` hub nodes. Counts from the file: all 4,157 transitions resolve both endpoints; every `DestinationPhase` is 0 and every `BranchInAny` is 0; **282** transitions carry explicit conditions, all others are plain edges selected by other mechanisms (branch windows, tags) that were not decoded. The most-used conditions are the booleans `FS4_LT_HOLD` (55), `FS4_RT_HOLD` (54), `FS4_Drb_ShouldStand` (44), `FS4_Drb_ShouldWallShield` (19), `FS4_Drb_ShouldWallStop` (11), `FS4_Juggling_Requested` (10), `FS4_Drb_Stand_Shield` (10) and `FS4_RB_Juggling_HOLD` (6).
Most fan-out: `Node_END_conduit` 71, `Node_VP_END_conduit` 52, `Stand_skill_conduit` 49, `3rdman_conduit` 47, `Jog_skill_conduit` 42, `FS4_SKILL_Goundmove_0_Conduit` 34, `FS4_SKILL_Groundmove_45_Conduit` 29, `FS4_SKILL_Groundmove_135_Conduit` 27.
Example (all from the TSV): `Rainbow_Variation_Jog_base` has edges to `Rainbow_Variation_Jog_success_flick_R`, `..._success_flick_L`, `..._fail_1`, `..._fail_2`, `..._fail_3` and `Idle`; none of those six edges has a condition, so the choice between them is made elsewhere (probably the gesture signals and branch windows of section 10).
This is the engine's real combo/skill graph, **not runtime-verified**: the game was not traced to confirm these edges are taken in this form.

## 10. Input gestures and tick windows (decoded from `ant.cbac`)

`docs/listings/gestures.tsv`: 135 `GestureAsset` entries, 467 step-matcher rows. A gesture is an ordered list of steps; each step has `MinTicks`, `MaxTicks` (a window in game ticks, unit not confirmed), `KeepMatching`, and one or more matchers: `AnalogStickGestureMatchAsset` (370 rows) or `GamepadButtonsMatchAsset` (97 rows). Step windows seen (min-max ticks): 0-15 (118 steps), 0-0 (79), 0-5 (56), 0-10 (45), 0-12 (33), 0-20 (32), 0-30 (16), 0-50 (16); a few use 1073741824 (about 2^30) as "unbounded".
A stick matcher has `MatchType` (1, 2 or 3; meaning not confirmed), a sector `MinAngle`..`MaxAngle` in radians (a sector with min above max wraps through 0, e.g. 315-45 degrees; negative angles also occur), `MinMagnitude`/`MaxMagnitude` (stick deflection), plus `AngularVelocity`, `MagnitudeVelocity`, `OffsetAngle`, `AngleRangeMin/Max` and an `Options` word. Examples from the file:

| Gesture | Step | Ticks | Matcher |
|---|---|---|---|
| `FS4_RS_180_TOUCH Matcher` | 0 | 0-0 | right stick, MatchType 1, 240.0-300.0 deg, magnitude 0.45-1.0 |
| `FS4_LS_180_HOLD (Drag back) Matcher` | 0 | 0-15 | left stick, MatchType 2, 240.0-300.0 deg, magnitude 0.5-1.0 |
| `FS4_LS_180_HOLD (Drag back) Matcher` | 1 | 0-5 | left stick, MatchType 2, 255.0-285.0 deg, magnitude 0.5-1.0 |
| `FS4_B_TOUCH Matcher` | 0 | 0-0 | button 6 (B per the pad map), MatchType 1, value 0.1-1.1 |

The mapping of gesture to signal to state edge (`GestureToSignalMappingAsset`, 205 instances) was **not** followed, so the link from a gesture to a specific skill-move state is open. 707 of 740 angles are multiples of 5 degrees; the rest are arbitrary values such as 318.29.

## 11. Collision reactions, tackle and playback tags (decoded from `ant.cbac`)

* `CollisionTag` (546): `restitution`, `forceMagnitude`, `forceYaw`, `forcePitch`, `useForceAsBallOut`. Restitution is 0 on 505 tags and 0.4 on 41; `forceMagnitude` is 0 on 509 and 0.1-0.5 on the rest; yaw/pitch give a direction (e.g. 0/0, +-20, 90/60, 140/0 degrees); 4 tags set `useForceAsBallOut`. `docs/listings/collision_tags.tsv`. These are animation-attached collision reactions of the character, not the ball's bounce.
* `TackleTag` (333): `Duration` is a small integer: 3 (78), 4 (72), 2 (64), 5 (42), 6 (29), 1 (14), 8 (9), 7 (8), 11 (3), 12 (3). Unit not stated.
* `TimeScaleControllerAsset` (694): playback-rate limits per cycle, `minScale`/`maxScale` 0.5/1.5 on 619, 0.5/3 on 29, 0.3/1.5 on 23, 0.3/3 on 11, 0.3/2 on 9, 0.8/1.25 on 1 (`docs/listings/time_scales.tsv`).
* `SkillMoveInfoTag` (351) has no data fields, only the name that marks an animation as a skill move.

## 12. Test scenarios (`data7.big`, `data/testinggame`, plain XML)

406 `.tg` files (`TestingGameData`, 2,941 `Step` elements) in folders such as `skillmoves`, `skills`, `panna`, `pace_control`, `pace_shielding`, `juggling`, `tackle_avoid`, `trap`, `fake_shot`, `defense` and `continuous/ballnetphysics`. A step carries `mType` (`USER_PADINPUT` 1,684, `INGAMEAI` 615, `FREEMOVE` 175, `DRIBBLE_TRAP` 77, `STAND_TACKLE` 32, `SHOT` 23, `PASS` 14, `SLIDE_TACKLE` 1, and numeric codes), stick angles and magnitudes, trigger magnitudes, buttons, `mStepEndTrigger` and `mStepEndDelay`. They are recorded inputs for engine tests, not the engine's own timing constants, but they give real input sequences per skill. They were surveyed, not analyzed scenario by scenario.
