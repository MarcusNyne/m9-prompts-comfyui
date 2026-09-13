# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A ComfyUI custom-node package (pure Python, no build step, no test suite). Every node is filed under a
**stock ComfyUI category**, never a package-named menu — the package is discovered by the `[m9]` suffix on
the node name, not by a branded submenu. That's a deliberate product decision: people look for a node by
what it does, so it has to sit next to the stock nodes it works with.

Two nodes rewrite a text prompt before CLIP-encoding it. They take `STRING` + `CLIP` and return
`CONDITIONING` — the `CLIPTextEncode` signature — so they live in `conditioning` beside the encoder they
replace, alongside the stock `Conditioning*` ops. Not `advanced/conditioning`: upstream reserves that for
model-specific and low-level encoders (`CLIPTextEncodeSDXL`, `ConditioningZeroOut`), and these are ordinary
text encoders with extra knobs.

- `ScramblePrompts [m9]` — reorder, remove, and randomly nudge weights
- `TweakWeights [m9]` — nudge weights of prompts matching keywords

Each of those has a text-in/text-out variant that runs the same transforms with no `clip` and no
`CONDITIONING`, so the rewritten prompt can feed a stock encoder or be chained into another prompt node.
They are filed under `utils`, not `conditioning` — without a CLIP input they are not encoders. Not `text`
either, where the stock string ops live: these are prompt transforms that happen to speak strings, so they
belong with the plumbing rather than with the general-purpose text nodes. Their `prompt` is `forceInput`
rather than a widget: the text belongs to whatever node feeds them, which is the point of the variant.

- `ScramblePromptsText [m9]` / `TweakWeightsText [m9]`

Two nodes are image ops, filed under the stock `image/transform` category so they're discoverable where
people look for image nodes (`image/transform` is where the stock resize/crop/pad ops live;
`image/postprocessing` would be wrong — that naming is for after-generation filters and no longer exists
upstream, where those are now `image/filters`):

- `FitPose [m9]` — fit a pose/control image into a latent's (or an explicit) canvas size without
  stretching, placed on black
- `CropToRatio [m9]` — trim an image to a target aspect ratio, cutting equally from two opposite edges

Two more nodes are plain text ops, filed under the stock `text` category — that is where upstream keeps
its own string nodes (`StringReplace`/"Replace Text", `StringConcatenate`, the `Regex*` nodes) as of
ComfyUI v0.34.0. On builds older than the rename that menu was `utils/string`, and the stock primitives
have moved along too (`utils/primitive` → `utilities/primitive`), so plain `utils` is no longer where a
general-purpose string node belongs:

- `Prefix [m9]` — join name/theme/scene/frame into one underscore-separated filename prefix
- `StepReplace [m9]` — rewrite text through five ordered search/replace steps, resolving `{ a | b }`
  choices as it goes

Changing a `CATEGORY` does not break saved workflows — ComfyUI serializes nodes by their
`NODE_CLASS_MAPPINGS` key (`ScramblePrompts_m9`), not by category or display name.

`m_prompt.py` must stay free of ComfyUI imports — stdlib only. That is what keeps the prompt logic
directly runnable in this checkout, where torch/numpy/PIL are unavailable (see Running / testing).
Anything ComfyUI-specific belongs in `m9_prompt_nodes.py`.

## Conventions

### No references to the sibling projects

**As of 2026-08-17, project artifacts must not mention the deprecated sibling Automatic1111 projects
(`sd-scramble-prompts-m9`, `sd-tweak-weights-m9`) or the UI they target.** This covers everything in the
repo: README, source and comments, `pyproject.toml` metadata, specs under `.claude/`, commit messages, and
release notes. Do not reintroduce such a reference when editing existing text either.

Those repos are being deprecated. This one no longer tracks them: shared logic is not ported out, and
their behavior is not a constraint on anything changed here. This file is the sole exception to the rule —
it has to name what it excludes in order to be enforceable.

## Running / testing

ComfyUI loads the package by directory: clone or symlink the repo into `ComfyUI/custom_nodes/` and restart
ComfyUI. There is no lint, build, or test command.

Neither the Python on PATH nor the bundled `venv/` has `torch`, `numpy`, or `Pillow` — those come from
ComfyUI's own environment. So `m9_fit_pose_node.py` cannot be imported here, but every `m_*.py` logic
module has no third-party imports and is meant to be exercised directly:

```bash
python -c "
from m_prompt import mPrompt
mp = mPrompt(inSeed=None, inPrompt='alpha, (beta:1.2), <lora:foo:0.8>')
mp.ScrambleOrder(inLimit=2)
print(mp.Generate()); print(mp.GetLog())"
```

```bash
python -c "
from m_fitpose import calc_fit
print(calc_fit(512, 768, 1216, 832, 1.0))   # -> (555, 832, 330, 0)"
```

```bash
python -c "
from m_cropratio import calc_crop
print(calc_crop(801, 400, 1, 1))                     # -> (400, 400, 200, 0)
print(calc_crop(400, 801, 16, 9, 'Vertical only'))   # -> (400, 801, 0, 0), would flip"
```

```bash
python -c "
from m_prefix import build_prefix
print(build_prefix('cara', '', 'alley', ''))   # -> cara_alley
print(build_prefix())                          # -> ComfyUI"
```

```bash
python -c "
from m_stepreplace import step_replace
pairs = [('flower', '{rose|tulip}'), ('rose', 'red rose'), ('', '')]
print(step_replace('a flower in a vase', pairs, inSeed=7))"
```

`mPrompt.TestParse(prompt)` dumps the parsed token dicts, and `LoadPrompt`/`SavePrompt` read and write
prompt files — both exist for ad-hoc checking and are unused by the nodes.

To smoke-test the node wrapper's wiring without ComfyUI, stub `torch`/`numpy`/`PIL` in `sys.modules`
before importing the package, then monkeypatch `tensor_to_pil`, `pil_to_tensor`, `Image.new`, and
`torch.cat` with recorders — that covers the batch loop, latent override, and paste offsets without any
real imaging.

`m9_crop_ratio_node.py` needs none of that: it imports nothing but its own logic module, so it can be
loaded here directly by registering the repo as a package (`sys.modules["m9pkg"] = <module with
__path__ = ["."]>`, then `importlib.import_module("m9pkg.m9_crop_ratio_node")`) and handed an object that
carries a `shape` and records the `__getitem__` slice. Skip `__init__.py` — that one does pull in torch.

The bundled `venv/` (gitignored) contains `comfy_cli`, used for publishing to the Comfy Registry; registry
metadata (`PublisherId`, `version`) lives in `pyproject.toml` and must be bumped there for each release.

## Architecture

Every node follows the same two-layer split: a dependency-free logic module (`m_*.py`) paired with a thin
ComfyUI wrapper (`m9_*.py`). Keep new work on that seam — it's what makes anything testable here.

- `m_prompt.py` — `mPrompt`, all the prompt logic. Stateless w.r.t. ComfyUI.
- `m9_prompt_nodes.py` — the four prompt node classes plus `Color9`, an ANSI-color console printer used
  for the `print_output` field. The transforms live in the module-level `apply_scramble()` /
  `apply_tweak()` helpers, which both the `CONDITIONING` node and its `Text` variant call, so the pair can
  never drift apart — add a transform there, not in a node method. Each `encode()` then follows the same
  shape: build an `mPrompt`, apply, `Generate()`, `clip.tokenize` + `encode_from_tokens(...,
  return_pooled=True)`, then prepend `conditioning_optional` to the resulting conditioning list so the node
  composes with other prompt nodes. The `Text` variants stop after `Generate()` and return the string.
- `m_fitpose.py` — `calc_fit()` (the fit arithmetic) and `target_from_latent()`. No torch/PIL.
- `m9_fit_pose_node.py` — `FitPose_m9` plus the tensor↔PIL helpers.
- `m_cropratio.py` — `calc_crop()` (the crop arithmetic), `_mode_allows()` and `ratio_from_image()`. Pure
  stdlib, so it runs here directly.
- `m9_crop_ratio_node.py` — `CropToRatio_m9`. The only node wrapper with no third-party imports: the crop
  is one tensor slice, so there is no torch/PIL round trip to make.
- `m_prefix.py` — `build_prefix()` and `sanitize_part()`. Pure stdlib, so it runs here directly.
- `m9_prefix_node.py` — `Prefix_m9`, a thin pass-through to `build_prefix()`.
- `m_stepreplace.py` — `step_replace()` plus `apply_step()`, `expand_choices()` and `build_pattern()`.
  Pure stdlib, so it runs here directly.
- `m9_step_replace_node.py` — `StepReplace_m9`. Its search/replace widgets and the pair list it hands to
  `step_replace()` are both generated from `sStepCount`, so the two can't drift; the widgets arrive back as
  `**kwargs` for the same reason. `step_replace()` itself takes any number of pairs.

`__init__.py` merges the `NODE_CLASS_MAPPINGS` / `NODE_DISPLAY_NAME_MAPPINGS` dicts that each `m9_*.py`
module declares. A new node module must export both and be merged there, or ComfyUI won't see it.

The node percentages are converted to absolute counts in `apply_scramble()` (`percent *
CountTokens('prompt') / 100`) before being passed to `mPrompt` as `inLimit`/`inTarget` — `mPrompt` itself
only deals in counts.

### Token model

`__init_prompt` normalizes newlines and lora brackets to commas, then splits on `,(?![^\(]*\))` so commas
inside parentheses stay in one prompt. Each piece becomes a dict: `{'token': str}` plus optional `'weight'`
and `'lora': True`.

Weight handling is lossy-by-design and round-trips through parentheses: on parse, each `(` multiplies the
weight by 1.05 and the parens are stripped; on `Generate()`, `__calc_paren` searches back for the shortest
representation, re-emitting up to 4 parens plus a `:weight` suffix formatted to 3 significant digits. So
output text is normalized, not preserved verbatim. Escaped parens (`\(`, `\)`) are protected via `@@@`/`###`
placeholders during parsing.

Loras (`'lora' in token`) are excluded from `ScrambleReduction` and from the non-lora branch of
`ScrambleWeights`, and are re-wrapped in `<...>` on output. `CountTokens('prompt')` counts non-loras only.

Every transform appends to `p_log` (`__log_header` for section lines starting with `=`, `__log_entry` for
indented per-prompt lines); `GetLog()` renders it. `ScramblePrompts` prints the generated text while
`TweakWeights` prints the log — that asymmetry is intentional.

### Seeding

`mPrompt.__init__` builds one private generator, `self.rng = random.Random(inSeed)`, and every transform
draws from it. Two invariants hold and both are easy to break:

- **Seed once per object, never per draw.** Seeding immediately before each individual draw rewinds the
  sequence every time, so every draw returns the same number. That was the behavior until 2026-08-17, and
  it silently disabled things: `ScrambleOrder` drew `r1 == r2` on every attempt and bailed out without
  reordering anything, and `ScrambleWeights`/`TweakWeights` applied one identical delta to every selected
  prompt. A fixed seed must reproduce a run exactly while still varying *within* the run.
- **Draw from `self.rng`, not the `random` module.** Module-level `random.seed()` would reset the
  process-wide generator that ComfyUI and every other custom node share. `random.Random(None)` would seed
  from entropy, but that path is not reached from the nodes — see below.

`seed_optional` sits in `optional` *with a widget spec*, so ComfyUI renders it as an INT widget and always
passes a value; unconnected it is `0`, never `None`. An unconnected node is therefore fully deterministic,
and ComfyUI caches its output, so it produces one variation and reuses it forever. Getting a fresh
variation per run means driving `seed_optional` from a seed primitive — which is what the README tells
users to do. Adding `"control_after_generate": True` to the widget spec would give the node its own
randomize control and remove that requirement.

`StepReplace_m9` **deliberately inverts that convention**: there `0` means *no seed given*, so it passes
`None` to `random.Random` and seeds from entropy. That only works because the class also defines
`IS_CHANGED`, which returns `float("nan")` for seed 0 — ComfyUI folds that value into the node's cache key
and NaN never compares equal to itself, so the node re-executes every queue. Delete `IS_CHANGED` and the
node silently pins itself to its first roll forever. Any non-zero seed is returned from `IS_CHANGED`
unchanged, leaving normal input-based caching intact and the run reproducible.

### Fit geometry

`calc_fit` returns `(new_w, new_h, x_offset, y_offset)` and is total — it clamps rather than raising, so a
zero dimension, a negative `subscale`, or an unknown `placement` degrades (to a 1px result, or to centering)
instead of raising.

`placement` names an anchor from `sPlacements` (`centered`, `bottom`, `left`, `right`, `bottom-left`,
`bottom-right`), each a `(horizontal, vertical)` pair resolved by `_anchor_offset` against the slack
`target - new`. `m9_fit_pose_node.py` builds its dropdown from `sPlacements.keys()`, so adding a `top*`
variant is a one-line dict entry — the widget follows. The default is `centered`, and `fit()` defaults the
argument too so workflows saved before the widget existed still load.

Two things there are load-bearing and easy to break:

- **Negative offsets are intentional.** `subscale > 1.0` makes the fitted image larger than the canvas, so
  the paste offsets go negative and the image is meant to crop against the edges. `PIL.Image.paste` does
  exactly that. Numpy slice-assignment would wrap the overflow to the opposite edge instead — that's why
  the composite goes through PIL and not tensor slicing. Placement still applies when overflowing: the
  negative slack lands wholly on the anchored axis's far side, so `left` holds `x_offset` at 0 and crops
  only the right.
- **`subscale = 1.0` always fills the canvas**, upscaling a small input to touch the edges. That's a
  deliberate product decision, not an oversight; there is no never-upscale toggle.

A connected `latent` overrides the `width`/`height` widgets (ComfyUI can't grey widgets out dynamically).
`target_from_latent` multiplies the latent's spatial shape by a hardcoded 8 — correct for SD1.5, SDXL,
SD3, and Flux — and returns `None` on anything it doesn't recognize, which falls back to the widgets. Only
spatial shape is read, so a latent batch size that differs from the image batch is ignored.

The tensor helpers in `m9_fit_pose_node.py` are **per-frame**: `tensor_to_pil` takes an `image[i]` slice
(`[H,W,C]`), not the `[B,H,W,C]` batch, and `pil_to_tensor` re-adds a batch dim, so `fit()` collects
frames and ends with `torch.cat(..., dim=0)`.

### Crop geometry

`calc_crop` returns `(new_w, new_h, x_offset, y_offset)` — the same shape as `calc_fit`, but here the
offsets are the top-left corner of a region that always lies *inside* the source, so they are never
negative. It is total in the same way: a zero dimension, a non-positive ratio, or an unknown mode
degrades to a pass-through rather than raising. A pass-through is `(src_w, src_h, 0, 0)`, which is what
`CropToRatio_m9.crop()` tests for in order to hand back the original tensor instead of a copy.

Four decisions there are load-bearing:

- **`mode` gates on orientation, not on which axis gets trimmed.** `Vertical only` means "crop vertical
  images and leave them vertical". It does *not* mean "only trim top and bottom" — a portrait source is
  trimmed on whichever axis the ratio calls for. That reading was considered and rejected; don't quietly
  swap them.
- **A restricted mode never changes orientation.** `_mode_allows` is called with the *computed result*,
  after the crop arithmetic, and requires both ends to be portrait (or both landscape). Gating on the
  target ratio instead is nearly the same test but not quite: a 1x8 source against 832:1216 rounds to
  1x1, square, and only the result-side check catches it. Square counts as neither, so a square source
  or a square result declines under both restricted modes.
- **Only the ratio matters.** `1216x832` and `152x104` give identical results, and the image is never
  scaled — the node cannot grow an image or resize it to the reference. The already-matching test is a
  cross-multiplied integer comparison rather than a float one, so exact matches are exact.
- **The odd pixel goes to the bottom or the right.** Both offsets floor (`(src - new) // 2`), so trimming
  401 rows takes 200 off the top and 201 off the bottom.

Unlike `FitPose`, the composite is plain tensor slicing (`image[:, y:y+h, x:x+w, :]`) rather than a PIL
round trip — the offsets are guaranteed in-bounds and non-negative, so there is no overflow to crop and
nothing PIL would do better. Every frame of a batch shares one size, so a single slice crops all of them
and there is no per-frame loop. The slice is a view; `.contiguous()` packs it before it leaves the node.

The ratio comes in over sockets, not widgets: `width`/`height` are `forceInput` INTs and `ratio_image` is
an IMAGE, all three in `optional`. `required` would be wrong for the pair — `ratio_image` overrides them,
so wiring only the reference image has to be a complete graph. Unconnected optional inputs never reach
`crop()`, so its `width=0, height=0` defaults stand and `calc_crop` reads that as a pass-through: a node
with nothing but an image wired in is a no-op rather than an error. `ratio_from_image` reads only
`shape[2]`/`shape[1]` of the `[B,H,W,C]` tensor and returns `None` on anything it doesn't recognize, which
falls back to the `width`/`height` inputs; the ratio image's batch size and pixels are never touched.

The node returns `IMAGE` alone. `FitPose` also emits its resolved `width`/`height` because that canvas size
is what an `EmptyLatentImage` downstream needs; a crop result is nothing another node has to be told, so
there is no size output here.

### Prefix assembly

`build_prefix` skips empty parts *before* joining, so separators only appear between parts that survive —
a lone `name` comes back with no underscore at all. `sDefaultPrefix` (`"ComfyUI"`) is the all-empty
fallback, chosen to match ComfyUI's own default `filename_prefix` so an unconfigured node behaves like an
untouched SaveImage.

Sanitizing is a **deliberate product decision, made with the tradeoff known**: `sanitize_part` replaces the
Windows-illegal set plus both path separators, which also flattens `%date:yyyy-MM-dd%` tokens (they contain
a colon) and defeats `/` subfolder syntax. Replacement is per-character and runs are not collapsed, so
`"a//b"` yields `"a__b"` — predictable beats tidy here, and it guarantees two halves of a value can never
silently run together. Don't "fix" the date tokens without asking; the alternative was offered and declined.

### Step replacement

`step_replace()` runs the pairs top to bottom over one running string, and **expands choices as it goes**:
the incoming text is expanded before step 1, and each replacement is expanded at the moment it is inserted.
That ordering is the feature — it is what lets `search_2` match text that `replace_1` produced, including
the option a `{ a | b }` picked. Expanding once at the end instead would break that chaining.

Four details there are load-bearing:

- **Each occurrence draws its own choice.** `apply_step` passes a function to `Pattern.subn`, so a
  replacement of `{ rose | tulip }` against three hits can yield three different flowers. Expanding the
  replacement once and reusing the string would quietly make them identical.
- **One generator per call.** `step_replace` builds a single `random.Random(inSeed)` and threads it through
  every expansion — same invariant as `mPrompt`, and just as easy to break by seeding inside a loop.
- **Braces without a `|` are left alone.** `{like_this}` survives verbatim, so text that merely happens to
  use braces isn't mangled. The cost is that a pipe-less inner brace also blocks an enclosing choice
  (`{ a | {b} }` stays literal); the real nesting case, `{ a | { b | c } }`, resolves innermost-first.
  `\{`, `\|` and `\}` are protected through `@@1@@`/`@@2@@`/`@@3@@` placeholders, the same trick
  `m_prompt.py` uses for escaped parenthesis, and come back out as bare characters.
- **Word boundaries are conditional.** `build_pattern` escapes the term, then adds `\b` only at an end
  whose own character is a word character. So `cat` won't match inside `category`, while `[FIND_THIS]` and
  `<lora:foo:0.8>` still match anywhere — an unconditional `\b` would never match those at all. Matching
  is case-insensitive, and both fields are `strip()`ed (a whitespace-only search is what "skip this step"
  means).

## Known gaps

`ScrambleReduction` clamps its target with `min(max(inTarget, 1), len(pmap)-1)`, so a computed target of 0
still removes one prompt. With a small `remove_prompts_percent` and few prompts the percentage rounds down
to 0 and one prompt is dropped anyway. Left as-is because changing it alters existing workflow output.

Both node `encode()` methods have a commented-out `IS_CHANGED` classmethod and a commented-out second
`STRING` return value — leftovers from when the nodes also emitted the final prompt text.
