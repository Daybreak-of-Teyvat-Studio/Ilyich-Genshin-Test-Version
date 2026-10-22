---
name: hoi4-icon-region-assign
description: Assigns HOI4 MOD focus icon / idea picture sprites so that (a) each file only uses sprites from its own region pack, (b) no sprite repeats more than twice within a single file, and (c) the sprite name semantically matches the focus/idea meaning. Use when rebalancing GFX_goal_/GFX_idea_ sprite assignments, fixing wrong-region icons, deduplicating heavily reused icons, or replacing unknown/path-broken sprite references. Also documents the Paradox-script file write-back procedure for write-protected workspaces.
agent_created: true
---

# HOI4 focus/idea icon region-assignment

Rebalance `icon =` (national_focus) and `picture =` (ideas) sprite references in a HOI4 mod so
each file draws only from its own geographic region's icon pack, no sprite repeats more than
twice inside one file, and each sprite's name semantically matches the entry's meaning.

## When to use

- A mod has several regional icon packs (e.g. `interface/DOT_Icons_<TAG>.gfx`, 200 `GFX_goal_` + 200 `GFX_idea_` each)
  and focus/idea files pick sprites from the wrong pack.
- The same sprite is reused dozens of times across one focus tree.
- `unknown` or path-broken sprite names need replacing.
- Any of the above where the user has supplied a **country-TAG → region** mapping table.

## Engine rules that drive the design

1. **`idea.picture` resolution**: the engine prepends `GFX_idea_` when the value omits it.
   Both `picture = generic_manpower_bonus` (resolves to `GFX_idea_generic_manpower_bonus`) and
   `picture = GFX_idea_FOO` are legal and equivalent.
2. **`idea` must NOT be given a `GFX_goal_` sprite** — the engine looks up
   `GFX_idea_GFX_goal_XXX`, which never exists. Vanilla has 0 such cases.
3. **`focus.icon` does no prefix completion** — it queries the sprite name verbatim.
   `icon = GFX_idea_...` is legal (vanilla has 1 case, many mods have hundreds), so a
   focus using an idea-class sprite is *not* a bug. Do not "fix" it.
4. **Sprite names are real only if a `.gfx` defines them.** Extract with
   `re.finditer(r'name\s*=\s*"([^"]+)"', src)` — **no `^` anchor**, because single-line inline
   definitions (`SpriteType = { name = "GFX_goal_..." texturefile = "..." }`) are common.
   Anchoring with `^\s*name` + `re.M` misses them and yields hundreds of false
   "path-broken" verdicts.

## Workflow

### Step 1 — Build the authoritative TAG → region table

Ask the user for their table if not supplied; do **not** guess from filenames or localisation.
Persist it to `tag2pack.json`. Derive the file-level map with `scripts/build_file_region.py`,
which extracts the TAG from the filename (strip a `New` prefix, `v1` suffix) and honors
`OVERRIDE` (shared trees, and nations the user clarifies late) plus `SHARED` (files left alone).

Do not stop at the table. Users often add or correct entries mid-task, and each addition means
re-running the assigner **for the affected files only** — a full re-plan would churn the 50+
files already written back. `scripts/reassign_new.py` does this: it `exec`s the main assigner
with its write-back disabled, then re-plans just the filenames listed in `ONLY`.

**Verify against the focus file headers** — the tag is authoritative and cheap to read:

```bash
cd "<MOD>/common/national_focus"
for f in *.txt; do
  id=$(grep -m1 -oP '^\s*id\s*=\s*\K\S+' "$f")
  tags=$(grep -oP '^\s*tag\s*=\s*\K\S+' "$f" | sort -u | tr '\n' ',')
  printf "%-28s id=%-16s tags=%s\n" "$f" "$id" "$tags"
done
```

Cross-check a sample before running anything. If a tree's `country` block lists several tags
(e.g. `FAV,LAW,SPI,DVA`), it belongs to whichever single region those tags share.

Mark shared/global files as region `None` and **leave them untouched**:
`DOT_*`, `DOT_generic.txt`, faction-agnostic ideas, non-regional nations.

### Step 2 — Parse localisation (both languages)

`scripts/build_loc.py` → `loc.json`.

Scan the **subdirectories** `localisation/simp_chinese/*.yml` and `localisation/english/*.yml`.
Scanning only the top level yields zero keys — a wasted round.

Format: ` KEY:0 "text"`. Handle a UTF-8 BOM via `utf-8-sig`, fall back to `gb18030`.

### Step 3 — Extract entry context

`scripts/extract_ctx.py` → `ctxmap.json`.

- focus: the nearest preceding `id = X`
- **idea: the block name itself** (`GUN_Family = { ... picture = ... }`) — idea blocks have
  **no `id =` line**. Track block headers with `^\s*([A-Za-z0-9_.]+)\s*=\s*\{\s*$`.

Searching upward for `id =` silently gives ~350 ideas no context, and a 45-line window is
shorter than many idea blocks.

### Step 4 — Assign

`scripts/reassign_v10.py` (edit the `MOD` / `STG` / `PACKS` constants first) → `plan_v10.json`.

Hard constraints:
- H1 region-correct: only the file's own pack
- H2 ≤ 2 uses per sprite **per file**. Confirm the intended scope with the user; per-file is far
  weaker than global and usually the intended one — it also makes capacity a non-issue, since
  `max(entries per file) ≤ pack_size × 2`
- H3 only sprites with a real `.gfx` definition
- H4 `idea` → `GFX_idea_`, `focus` → `GFX_goal_`

Scoring: convert the entry name to Chinese (localisation first, then per-word translation of the
id) and the sprite name to Chinese the same way, then compare **character 2-gram sets**:
`score = 0.70·|i|/|a| + 0.30·|i|/|a∪b|`.

Two pitfalls that dominate the result:

- **Never fall back to alphabetical order.** `for n in pool: if used[n] < 2: pick = n` hands
  every unmatched entry the alphabetically-first sprites (`Alchemy_Lab`, `Alchemy_Theory`, …)
  and reports them as 0-score matches. When an entry's candidates are all at quota, walk **that
  entry's own candidate list** and take the highest-scoring one still under quota.
- **Use an intersection test, not a score threshold.** 2-gram overlap is intrinsically low
  (1 hit in a 4-gram query ≈ 0.175), so `> 0.02` is near-random noise while `> 0.3` is
  unreachable. Use `has_hit(a, b) = bool(a & b)` and degrade in tiers:
  literal title → concept bridge (expand both sides through a domain dictionary) → id `_desc`
  bridge (only when the title yields nothing).

### Step 5 — Emit and verify

`scripts/emit_v10.py` → out dir + backup dir. It asserts **line number AND current value**
before rewriting each line, so drift or a shifted line count surfaces as `DRIFT`/`BADLINE`
instead of silent corruption. Then re-verify the emitted copies:

- `unknown`/empty = 0
- truly-undefined = 0
- region mismatch = 0
- per-file reuse > 2 = 0
- `idea` using `GFX_goal_` = 0
- non-`icon`/`picture` lines changed = 0
- brace depth unchanged = 0

**Verify against the mod itself, not the staging copy**, with `scripts/final_audit.py` — the
staging copy cannot reveal a failed write-back.

When extracting the pack name for the audit, use
`re.match(r'GFX_(?:goal|idea)_([A-Za-z]+)_', v)`. A loose `re.search(r'_([A-Za-z]+)_')`
grabs `idea` and makes every file look wrong.

### Step 6 — Write back

See `references/write-back-protected-workspace.md`. Short version: top-level Bash,
`dangerouslyDisableSandbox: true`, `rm -f` then `cat src > dst`, **two files per call**, and
`cmp` after each batch. Progress check: `scripts/wb_check.py` (it must compare focus and idea
against their own directories or it reports false "pending").

## Bundled scripts

| Script | Purpose |
|---|---|
| `build_file_region.py` | filename TAG → region, with override + shared-file tables |
| `build_loc.py` | localisation subdirs (zh + en) → `loc.json` |
| `extract_ctx.py` | focus id / idea block name per line → `ctxmap.json` |
| `reassign_v10.py` | the assigner (region + per-file dedup + semantics) |
| `reassign_new.py` | re-plan only the files in `ONLY` (use after the user adds a region) |
| `emit_v10.py` | apply plan to copies, double-asserted, with full validation |
| `verify_out6.py` | staging-dir validation under the per-file scope |
| `final_audit.py` | validate the mod itself |
| `wb_check.py` | write-back progress check (separate dirs for focus/idea) |

All scripts hardcode absolute paths near the top; edit those constants for a different mod.
