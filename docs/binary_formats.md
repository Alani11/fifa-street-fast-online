# Binary formats found in this workspace

Every layout below was checked against the real files with `tools/verify_all.py` (run it; it prints the evidence).
Each claim is marked **verified** (a test passes on all samples), **inferred** (consistent with samples, meaning is a guess), or **unknown**.
Unpacked output lives in `unpacked_data/` (raw archive members) and `unpacked_data/decoded/` (after chunk/RefPack decoding and nested-archive unpacking).

## 0. Scope: what was asked vs. what exists

| Requested | Result |
|---|---|
| Magic bytes `BIGF`, `BIG4`, `RX3`, `AST`, `.dat`, `.bin` | `BIG4` (8 outer archives) and `BIGF` (124 nested) found. `chunklzx` / `chunkzip` containers, RefPack, `ESIA`, `StrE`/`Vers` vault files, `DB\0\x08` t3db found. The user's own `Game` folder (outside this workspace's original files) also holds `data1`..`data7.big`, which list 56 ball and 14 pitch-line `.rx3` files (`data3.big`) and 65 stadium `.rx3` containers (`data2.big`): `RX3` files exist but were **not extracted or parsed**. No `AST`, `.skl`, `.anm` or `.msh` name was seen in any listing (`docs/listings/Game_data*.big.txt`). |
| Skeletal rig parser | **Not written.** Rig and animation data are inside the ANT `GD.STRM` bundles `ant.cbac` and `common.cbac` (section 9), whose records are not decoded; `ant.ini` only holds ANT memory budgets (e.g. `MaxNumRigs = 8`, `NumPlayers = 25`). |
| Animation curve parser | **Not written.** Candidates: `ant.cbac` records (section 9) and the `ESIA` skill-move AI sequences (section 5), whose bodies are not decoded. |
| Arena collision bounds parser | **Not written.** Stadium containers are `data2.big` `stadium_*_container_*.rx3`; `streetdefault.ini` names `STADIUM_COLLISION_AND_LOCATORS` only in commented-out lines. The `RX3` container format was not analyzed. |
| Endianness | Mixed, see each section. |

The game executable is an Xbox 360 recompile. Its lifted code and the image dump are covered in `physics_spec.md` section 7.

## 1. Outer archive: `BIG4` (and nested `BIGF`) — verified

Files: `engine_data/Game/data0.big`, `data4.big`, `data/loc/locale*.big`, `crest.big` x2, `2dheads.big`. Parser: `tools/big4.py`.

| Offset | Size | Type | Meaning |
|---|---|---|---|
| 0x00 | 4 | ASCII | `BIG4` (outer) or `BIGF` (nested, same layout) |
| 0x04 | 4 | u32 **little-endian** | total file size. Matches the real size on all 8 outer files |
| 0x08 | 4 | u32 big-endian | entry count (data0: 0x10b = 267; data4: 1; locale: 11) |
| 0x0C | 4 | u32 big-endian | header end (table + optional 8-byte trailer). Member data starts at the next 64-byte boundary after this value (verified on all 8: e.g. data4 0x45 → 0x80, locale 0x157 → 0x180, data0 0x33c0 → 0x33c0) |
| 0x10 | … | entries | repeated: `u32 BE offset`, `u32 BE size`, NUL-terminated name |

* The entry table ends at `tocend`. `header_end - tocend` is 0 in `data0.big`, `data4.big` and both `locale_ptbr.big`, and 8 in `locale.big`, both `crest.big` and `2dheads.big`. Those 8 bytes are `4c 32 38 36 15 05 00 00` in `locale.big` and `4c 32 37 37 15 05 00 00` in the other three (ASCII `L286` / `L277` plus `15 05 00 00`): a version-like tag, **meaning unknown**.
* All 13,525 outer entry offsets are multiples of 64 (or equal the header end).
* Names use `/` in `data0` and `\` inside nested archives (e.g. `data\skillmoveai\...`).
* Entries are stored uncompressed in the archive, but most members are themselves `chunklzx` (section 2).
* Nested `BIGF` archives (124 of 129 nested archives; the other 5 are `BIG4`) use the same table layout but their size field is **file size minus 16** on all 124 (the last 16 bytes are not described by the header; their content looks random, **unknown**). Nested `BIG4` size fields equal the real size. Example: `ui/game/screens/blank.big` starts `BIGF e0 00 00 00`.

Directory listings of every archive: `docs/listings/engine_data_*.txt`. `data0.big` contains 267 entries: Lua boot scripts, `.ini` files, `attribdb*` vaults, neural nets, a t3db database, cameras, fonts, UI `.big`, and 52 `.dat`.
`data4.big` holds one member, `audiodata/crowdlogic/reactions/reactions.sbs`, starting with `SBKS` at offset 0x80 (sound bank, not analyzed).

## 2. `chunklzx` / `chunkzip` container — verified (decode succeeds and sizes assert on 253 files)

Parser: `tools/chunkdec.py` (a Python port of `port_code/Tools/ReStreetAssetScan/Program.cs` `DecodeChunk` and `ThirdParty/LzxDecoder.cs`).

| Offset | Type | Meaning |
|---|---|---|
| 0x00 | 8 ASCII | `chunklzx` (Xbox LZX), `chunkzip` (raw deflate) or `chunkref` (RefPack chunks) |
| 0x08 | u32 BE | version, must be 2 (checked by the project's code) |
| 0x0C | u32 BE | uncompressed size |
| 0x10 | u32 BE | chunk size (0x40000 in the samples) |
| 0x14 | u32 BE | equals `ceil(full / chunk)` on all 253 files: **inferred** = chunk count |
| 0x18 | u32 BE | 16 on all 253 files: **inferred** = record alignment |
| 0x1C–0x27 | | zero in the samples |
| 0x28… | chunk records | for each chunk: position `p = ((p+7)//16)*16 + 8`; `u32 BE n`, `u32 BE kind`, then `n` bytes |

Chunk `kind`: 1 = raw deflate, 2 = RefPack (`chunkref`; each chunk decodes to exactly the chunk size, asserted), 3 = Xbox LZX, 4 = stored. LZX chunks are a sequence of frames. Each frame is `u16 BE inSize` (output 32768 bytes), or `0xFF, u16 outSize, u16 inSize` for a short frame. The decoder is reset for every chunk: 17-bit window, 16-bit little-endian bit reads, MSB first, block types verbatim (1), aligned (2). Uncompressed LZX blocks (type 3) are implemented in `chunkdec.py` (pad to 16 bits, three little-endian repeat offsets, raw bytes, odd-length pad byte); five `data7` members use them. The `chunkref` and uncompressed-block paths are exercised by the 2,277 `data7` members and 1,843 `GD.STRM` size checks, which all pass.

After the chunk layer, many members are **RefPack** (`10 FB`, 24-bit big-endian length, then the opcode stream in `DecodeRefPack`). 456 nested members were RefPack-decoded.

## 3. EA Attrib "vault" databases (`attribdb*.vlt` / `.bin` / `.opt`)

Files: `data/attribdb`, `data/attribdb2`, and nested `data/attribdbgameplay/gameplayattribdb.big`. Tools: `tools/attribdb_dump.py`, `tools/attrib_slots.py`.

### 3.1 `.vlt` chunk walk — verified
Chunks, each `tag(4 ASCII) + u32 BE total size (including the 8 header bytes)`: `Vers`(16) `StrN`(16) `DepN`(80) `DatN` `ExpN` `PtrN` `EndC`(16). The sizes sum exactly to the file size in all three vaults (gameplay vault 48,768 bytes; main 706,064; attribdb2 170,112).
`Vers` is 16 bytes: tag, size, 8 payload bytes. The payload is `aa8a0ef8 54dfa950` in the main and gameplay vaults and `59d37d39 1c02448e` in `attribdb2` (a schema/version hash, **meaning inferred**). `DepN` names a dependency (`attribdb.vlt`, `attribdb.bin`).

### 3.2 `ExpN` export table — verified
`tag, u32 size, u32 0, u32 count`, then `count` 24-byte records, all big-endian: `u64 collectionKey`, `u64 classKey`, **`u32 size`, `u32 offset`** (in that order). Offsets are absolute positions in the `.vlt`. Sorted by offset, the records **tile `DatN` with no gaps** in all three vaults: the first offset is 120 (= `DatN` start 112 + 8), each offset equals the previous offset plus size, and the last record ends 8 bytes before `DatN` ends (trailing pad). `ExpN` size = `16 + 24*count` in `attribdb2.vlt` and that plus 8 in the other two (also trailing pad).

| Vault | Exports | Class keys |
|---|---|---|
| attribdbgameplay | 103 | `ad303b8f42b3307e` x103 |
| attribdb (main) | 3687 | `ad303b8f42b3307e` x3648, `2a7895ac4a876152` x38, `0b38846845e9c175` x1 |
| attribdb2 | 890 | `ad303b8f42b3307e` x859, `2a7895ac4a876152` x30, `0b38846845e9c175` x1 |

**Inferred:** class `2a7895ac4a876152` marks `ClassRefSpec` records, because the `.bin` string pool holds 38 (main) and 30 (attribdb2) `Attrib::Gen::ClassRefSpec_*` names, equal to those counts.
**Key hashing is not understood.** A known-answer test hashed 1,848 strings from `attribdb.bin` (with case and prefix variants, 6,182 inputs) with FNV-1, FNV-1a and Jenkins lookup8 (both byte orders) against all 64-bit keys: zero matches. Other algorithms were not tried, so this says "none of these", not "unhashable".

### 3.3 Record layout — inferred
A record (at its `offset`, length `size`) starts with `u64 id`, `u64 hash` (the same hash in the two records inspected), zeros, then `u32 n` at +24 and again at +32, `u16 1|2` twice at +36/+38. A 16-byte header slot sits at +48 and `n` 16-byte slots follow from +64. `size == 64 + 16*n` and the two `n` agree for 91 of 103 gameplay records, 2,584 of 3,687 main records and 715 of 890 `attribdb2` records. The rest (40- and 48-byte records with n = 0, records 16 bytes longer, a few with different n at +24 and +32) were **not decoded**.
Slot = `u64 key hash`, `u32 value`, `u32 flags`. Flag `0x00004000` (837 of 1,505 gameplay slots) marks a big-endian float32 value (e.g. 1.5, 0.5, 2, 10); other flags (`0x200` 319 slots, `0x10000`, `0x10200`, `0x14000`, `0`) were **not decoded**. `tools/attrib_slots.py` writes `docs/listings/gameplay_attrib_slots.csv` (1,505 slots, 1,207 distinct key hashes). Earlier versions of these tools had the size and offset fields swapped; this version is the one that passes the tiling test.

### 3.4 `.bin` files
* `attribdb.bin` (245,600 bytes decoded) starts with a `StrE` chunk (size 8208 = 0x2010; a string pool of stadium/lighting names, `.fx` shader names, audio bus and tag names), then `EndC`, then a reflection table at 0x2020 starting `EA::Reflection::Int64 …`, then `Attrib::*` type names and `Attrib::Gen::ClassRefSpec_<class>` names.
* ClassRefSpec class names present: `rendering, stadiumdb, stad_common, stad_day_1, stad_day_2, stad_dusk_1, stad_night_1, stad_review, presentation, actor, collision, cpu_ai, defense, evaluation, goalkeeper, kick_common, kick_error, kick_pass, kick_shot, locomotion, physical_play, physics, player, player_attribute, player_behavior, positioning, rules, setplay, team` plus audio/crowd classes.
* `attribdbgameplay/attribdb.bin` (35,296 bytes): `StrE` (16), `EndC` (16), then from 0x20 `0009 0009 0004 0000` followed by big-endian float32 data (first values 1.2, 0.7). Structure beyond that is **unknown**.
* `.opt` files are 16 bytes: `EndC`, size 0x10, 8 zero bytes.

## 4. Neural-network files `data/neuralnet/nnet{pass,shot,tackle,dribble}.dat` — layout verified by size closure

Stream of **little-endian** float32 (the rest of the engine data is big-endian):
`float[0] = L` (layer count), `float[1..L]` = layer sizes input→output, then `2*(n_first + n_last)` values and `Σ (n_i+1)·n_{i+1}` weight+bias values.
That formula gives exactly the float count in all four files:

| File | Layers | Floats |
|---|---|---|
| nnetpass | 15, 15, 15, 15, 1 | 774 |
| nnetshot | 8, 15, 15, 15, 1 | 655 |
| nnettackle | 7, 10, 10, 1 | 222 |
| nnetdribble | 10, 10, 7, 1 | 222 |

**Inferred:** the `2*(n_first+n_last)` values are input and output normalization pairs. **Unknown:** block order, activation function, and what each input means. `python tools/nnet_dump.py <file>` prints the summary.

## 5. Skill-move AI sequences `data/skillmoveai` (`skillmoveai.big`, BIG4 after decoding)

273 `.seq` files in six folders (`generic` 227, `messi` 42, `cronaldo`, `davidvilla`, `ribery`, `robinho` 1 each), plus an `aisequence.libfinal` per folder.

* `.seq`: magic `ESIA`, `u32 BE id` at 0x04, `u32 BE w` at 0x08 (values: 4 in 184 files, 5 in 44, 0xFFFFFFFF in 41, 0 in 4), `u32 BE n` at 0x0C. The id equals the decimal number in the file name (`_837299881_.seq` = 0x31E82EA9) on all 273. **File size = `24*n + 128` when `w == 0`, else `28*n + 152`**, verified on all 273 files (`tools/verify_all.py`); the record contents behind those counts are **unknown**.
* `aisequence.libfinal` — verified: `u32 BE version` (4 or 5), `u32 BE count`, `count` sorted `u32 BE` ids. File size = `8 + 4*count` and the id set equals the set of `.seq` files in every folder (generic: 227).

## 6. `fifa_street_db.db` (t3db) — partly identified
723,536 bytes, header `DB 00 08`, then `u16 BE 0x0100`, `u32 BE 0` and `u32 BE 723536` (the file size). `fifa_street_db-meta.xml` is a t3db meta file (database version 6) whose table and field names are 4-letter hashes (e.g. `shortname="bd_t"`); the table directory was not decoded.

## 7. Other files
`setplays.bin` (1,744 bytes): starts with big-endian u32 0x91 then sequential ids; not decoded. `camera/*.dat`, `fesettings/*.bin`, `nis/*.bin`, `rendering.cdb`: not analyzed.

## 8. Executables (`binaries/`)
`fifadllzf.xex.dll` and `FootballCompEngzf.xex.dll` are XEX2 (the first has file-format flags `encryption=1`, `compression=1`); ReXGlue decodes them as part of recompilation. `fifastreet_fifadllzf_xex.dll` is an 82,740,224-byte x86-64 PE of that recompiled code. The recompiled C++ and the guest image dump are described in `physics_spec.md` section 7.

## 9. ANT bundles `ant.cbac` and `common.cbac` (`GD.STRM`) — decoded, layout inferred and cross-checked
Loose files in `Game/data/`: `ant.cbac` (28.9 MB; 70,625,288 bytes decoded; 190 classes, 92,152 instances) and `common.cbac` (166,609 bytes; 822,724 decoded; 115 classes, 1,315 instances). Both are `chunkref` containers (section 2). The same format is used by 1,841 members of `data7.big` (`data/ant/pc/niscbac`, `faceposerbig`: cutscene and face-pose assets). Parser: `tools/gdstrm.py`; exporter: `tools/gd_export.py`.

**Sections (verified):** `GD.STRMb` at 0, u32 BE total length at +8 (equal to the decoded length on all 1,843 files), `GD.REFLb` at +16 (the class schema), then many `GD.DATAb` blocks (instances).

**`GD.REFL` class record (inferred):** `[marker FF FF FF FD | 5 x u32 | u32 1 | u32 classHash | n x 32-byte field entries] [NUL-separated name pool: class name, __name, __guid, __base, field names...]`. The marker, the metadata and the name pool of the *next* class follow in sequence. A field entry is 8 x u32 BE: `kind, size, payload_offset, name_pool_offset, flagsA, flagsB, 0, typeRef`. `name_pool_offset` is 1-based into the class's name pool, advancing by `len+1`. Kinds seen: `0x1` byte/bool, `0x3` byte, `0x5`/`0x6`/`0x7` 32-bit integers (`0x7` also read as `Duration` in `TackleTag`), `0xA` float32 (a 16-byte `0xA` is a vec4), `0xC` vec4, `0xF` 4x4 matrix (64 bytes), `0x10` GUID or GUID list handle, `0x11` string handle, `0x12` reference handle.

**`GD.DATAb` instance block (inferred):** `GD.DATAb | u32 total | u32 payload | ... | u32 classHash at +36 | 48-byte header`; field `payload_offset` is relative to `block + 48`. Cross-checks that hold on every instance: float fields read as sane values and `InertiaTensorScale` is exactly 1.0 on all 14 `PartProperty` blocks; all 4,157 state-flow transition `From`/`To` GUIDs resolve to node blocks.
* **Strings:** a string field is a handle `(len, cap, 0, off)`; the text is at `block + 16 + off`, NUL-terminated, `len` counting the NUL. 85,979 of 92,152 blocks yield a name this way; the other 6,173 do not (class has no `__name`, or the rule fails there), **not investigated**.
* **GUID lists:** a list field is a handle `(count, count, 0, off)`; the items are `count` 16-byte GUIDs at `block + 16 + off`. A single reference field holds the 16-byte GUID directly. A GUID is the `__guid` field of the target block.

Not decoded: the unnamed block classes (`?` in `gdstrm.py` output), 17 other field kinds, curve data (`PiecewiseLinearAsset.PointValues`), `VbrAnimationAsset` / `DctAnimationAsset` (compressed animation) and the `0x0C` word at +12 of the file. What the decoded values mean is in `state_machine.md` sections 8-11 and `physics_spec.md` section 10.

## 10. Other archives of the user's `Game` folder
`data1`..`data7.big` use the same `BIG4` layout (size fields match the files: 546,215,104 / 343,111,054 / 1,162,629,608 / 373,141,536 / 1,169,013,768 / 351,991,936 bytes for data1/2/3/5/6/7). Listings: `docs/listings/Game_data{1,2,3,5,6,7}.big.txt` (entry counts 19,206 / 65 / 15,705 / 1 / 25 / 3,783). `data1`: UI images and DLC INIs; `data2`/`data3`: `.rx3` scene assets (stadiums, ball, pitch, kits, faces); `data5`/`data6`: audio banks; `data7`: ANT cutscene assets and the 406 XML `.tg` test scenarios (`state_machine.md` section 10). `Game/data/gameconfig/*.gcf` (47 files) and `.xur` UI files were not analyzed.
