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

A third node is an image op, filed under the stock `image/transform` category so it's discoverable where
people look for image nodes (`image/transform` is where the stock resize/crop/pad ops live;
`image/postprocessing` would be wrong — that naming is for after-generation filters and no longer exists
upstream, where those are now `image/filters`):

- `FitPose [m9]` — fit a pose/control image into a latent's (or an explicit) canvas size without
  stretching, placed on black

A fourth node is a string utility, filed under the stock `utils` category alongside the primitive/string
helpers rather than with the CLIP-encoding nodes:

- `Prefix [m9]` — join name/theme/scene/frame into one underscore-separated filename prefix

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
ComfyUI's own environment. So `m9_fit_pose_node.py` cannot be imported here, but the two logic modules
have no third-party imports and are meant to be exercised directly:

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
from m_prefix import build_prefix
print(build_prefix('cara', '', 'alley', ''))   # -> cara_alley
print(build_prefix())                          # -> ComfyUI"
```

`mPrompt.TestParse(prompt)` dumps the parsed token dicts, and `LoadPrompt`/`SavePrompt` read and write
prompt files — both exist for ad-hoc checking and are unused by the nodes.

To smoke-test the node wrapper's wiring without ComfyUI, stub `torch`/`numpy`/`PIL` in `sys.modules`
before importing the package, then monkeypatch `tensor_to_pil`, `pil_to_tensor`, `Image.new`, and
`torch.cat` with recorders — that covers the batch loop, latent override, and paste offsets without any
real imaging.

The bundled `venv/` (gitignored) contains `comfy_cli`, used for publishing to the Comfy Registry; registry
metadata (`PublisherId`, `version`) lives in `pyproject.toml` and must be bumped there for each release.

## Architecture

Every node follows the same two-layer split: a dependency-free logic module (`m_*.py`) paired with a thin
ComfyUI wrapper (`m9_*.py`). Keep new work on that seam — it's what makes anything testable here.

- `m_prompt.py` — `mPrompt`, all the prompt logic. Stateless w.r.t. ComfyUI.
- `m9_prompt_nodes.py` — the ComfyUI node classes plus `Color9`, an ANSI-color console printer used for
  the `print_output` field. Both nodes' `encode()` follow the same shape: build an `mPrompt`, apply
  transforms, `Generate()`, `clip.tokenize` + `encode_from_tokens(..., return_pooled=True)`, then prepend
  `conditioning_optional` to the resulting conditioning list so the node composes with other prompt nodes.
- `m_fitpose.py` — `calc_fit()` (the fit arithmetic) and `target_from_latent()`. No torch/PIL.
- `m9_fit_pose_node.py` — `FitPose_m9` plus the tensor↔PIL helpers.
- `m_prefix.py` — `build_prefix()` and `sanitize_part()`. Pure stdlib, so it runs here directly.
- `m9_prefix_node.py` — `Prefix_m9`, a thin pass-through to `build_prefix()`.

`__init__.py` merges the `NODE_CLASS_MAPPINGS` / `NODE_DISPLAY_NAME_MAPPINGS` dicts that each `m9_*.py`
module declares. A new node module must export both and be merged there, or ComfyUI won't see it.

The node percentages are converted to absolute counts in `encode()` (`percent * CountTokens('prompt') / 100`)
before being passed to `mPrompt` as `inLimit`/`inTarget` — `mPrompt` itself only deals in counts.

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
  process-wide generator that ComfyUI and every other custom node share. `random.Random(None)` seeds from
  entropy, so an unconnected `seed_optional` stays fully random.

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

## Known gaps

`ScrambleReduction` clamps its target with `min(max(inTarget, 1), len(pmap)-1)`, so a computed target of 0
still removes one prompt. With a small `remove_prompts_percent` and few prompts the percentage rounds down
to 0 and one prompt is dropped anyway. Left as-is because changing it alters existing workflow output.

Both node `encode()` methods have a commented-out `IS_CHANGED` classmethod and a commented-out second
`STRING` return value — leftovers from when the nodes also emitted the final prompt text.
