# ComfyUI Custom Node: "FitPose [m9]"

## Resolved decisions

Settled during spec review (2026-08-14) — these override anything below that conflicts:

| Decision | Choice |
|---|---|
| Location | Ships inside **this repo** (`m9-prompts-comfyui`), not a standalone package. |
| Class name | `FitPose_m9` |
| Mapping key | `FitPose_m9` |
| Display name | `FitPose [m9]` |
| Category | `image/transform` (stock ComfyUI category, for discoverability — deliberately *not* `M9 Prompts`, since this is an image node). Corrected from `image/postprocessing`, which is for after-generation filters and no longer exists upstream; `image/transform` is where ImageCrop / ImageStitch / ResizeAndPadImage live. |
| Alpha | Dropped entirely. Always emit 3-channel RGB on black. No `transparent_background` widget, no `MASK` output. |
| Upscaling | Always fit. A small pose image *is* upscaled to touch the canvas edge at `subscale = 1.0`. No `allow_upscale` toggle. |
| `subscale` min | Stays `0.0`. The 1-pixel clamp means `subscale = 0` yields a 1x1 dot centered on black — accepted as harmless. |

## Goal

Build a ComfyUI custom node that takes a pose/control image (e.g. an OpenPose skeleton
rendered on a black background) and fits it into a target canvas size — matching the
dimensions of a latent or an explicit width/height — **without stretching**, centered,
padded with black, and with an adjustable "subscale" margin control.

## Behavior spec

Given:
- An input image of size `(img_w, img_h)`
- A target canvas size of `(target_w, target_h)` (sourced either from a `LATENT` input's
  tensor shape, or from explicit `width`/`height` int widgets — support both, see Inputs
  below)
- A `subscale` float (default `1.0`, range `0.0`–`2.0`, step `0.01`)

Compute:

```
fit_scale   = min(target_w / img_w, target_h / img_h)
final_scale = fit_scale * subscale

new_w = round(img_w * final_scale)
new_h = round(img_h * final_scale)
```

Then:
1. Resize the input image to `(new_w, new_h)`, preserving aspect ratio (this is guaranteed
   by construction above — do not independently compute width/height scale factors).
2. Create a new black canvas `(target_h, target_w, 3)` — pure black `(0, 0, 0)`, matching
   the background OpenPose renders normally use. Always 3-channel RGB; if an input somehow
   arrives with 4 channels, drop alpha rather than erroring.
3. Paste/composite the resized image centered on the canvas:
   ```
   x_offset = (target_w - new_w) // 2
   y_offset = (target_h - new_h) // 2
   ```
   When `subscale > 1.0` these offsets go **negative**, and Python's `//` floors toward
   negative infinity. `PIL.Image.paste` handles negative offsets by cropping cleanly, which
   is the desired behavior. Do **not** implement the paste with numpy slice assignment —
   negative indices there wrap to the opposite edge instead of cropping.
4. Return the composited image as a ComfyUI `IMAGE` tensor.

### Semantics of `subscale`
- `subscale = 1.0` → image is scaled up/down so its **longest relevant dimension**
  touches the edge of the target canvas exactly (full "contain" fit, zero margin).
- `subscale = 0.8` → the fitted image is scaled to 80% of the full-fit size in both
  dimensions, leaving a proportional margin around it (biggest margin appears along
  the axis that was touching the edge at `subscale = 1.0`).
- `subscale > 1.0` → image will overflow / be cropped off canvas edges. This should be
  **allowed** (some users may want slight overflow/cropping), just don't special-case it.

### Resampling
- Use **`PIL.Image.LANCZOS`** (aka `Image.Resampling.LANCZOS` in modern Pillow) for both
  upscale and downscale by default — good general quality for line art.
- Add an optional `interpolation` combo widget: `["lanczos", "bicubic", "bilinear",
  "nearest"]`, default `"lanczos"`, so users can switch to `"nearest"` if they want to
  preserve hard skeleton lines without any anti-aliasing softness.

## Inputs

| Name | Type | Notes |
|---|---|---|
| `image` | `IMAGE` | Required. The pose/control image to fit. |
| `subscale` | `FLOAT` | Widget. Default `1.0`, min `0.0`, max `2.0`, step `0.01`. |
| `interpolation` | Combo | `["lanczos", "bicubic", "bilinear", "nearest"]`, default `"lanczos"`. |
| `latent` | `LATENT` | **Optional.** If connected, derive `target_w`/`target_h` from it (see note below). |
| `width` | `INT` | Widget, default `1024`, min `64`, max `8192`, step `8`. Used only if `latent` not connected. |
| `height` | `INT` | Widget, default `1024`, min `64`, max `8192`, step `8`. Used only if `latent` not connected. |

### Deriving target size from LATENT
ComfyUI latents are `[batch, channels, h, w]` where `h`/`w` are **1/8 the pixel
dimensions** (standard SD VAE downscale factor). So:
```
target_h = latent["samples"].shape[2] * 8
target_w = latent["samples"].shape[3] * 8
```
The factor of 8 is a hardcoded VAE assumption. It holds for SD1.5, SDXL, SD3, and Flux;
leave it hardcoded but comment it so it's findable if a future model breaks it. If the
latent's batch size differs from the image's, ignore it — only the spatial shape is read.
If a `latent` input is connected, it should **override** the `width`/`height` widgets
(or better: grey them out / ignore them — ComfyUI doesn't support dynamic widget
disabling easily, so just document that `latent` takes priority when connected).

## Output

| Name | Type |
|---|---|
| `image` | `IMAGE` |

Also worth returning `width`/`height` as `INT` outputs (the resolved target dimensions) —
handy for wiring into an EmptyLatentImage node downstream so the whole pipeline stays in
sync.

## Implementation notes

- ComfyUI `IMAGE` tensors are `torch.Tensor` of shape `[batch, H, W, C]`, float32, values
  in `[0, 1]`. Convert to PIL for the resize/paste logic, then back to tensor. Standard
  pattern:
  ```python
  import numpy as np
  from PIL import Image
  import torch

  def tensor_to_pil(frame):        # frame is a SINGLE [H, W, C] slice, not the batch
      i = 255. * frame.cpu().numpy()
      return Image.fromarray(np.clip(i, 0, 255).astype(np.uint8)).convert("RGB")

  def pil_to_tensor(pil_img):      # returns [1, H, W, C]
      arr = np.array(pil_img).astype(np.float32) / 255.0
      return torch.from_numpy(arr)[None,]
  ```
- Handle the batch dimension — loop over `image.shape[0]` and process each frame in the
  batch independently (pose images will usually be batch size 1, but don't assume it).
  Note the helpers above are per-frame: `tensor_to_pil` takes `image[i]` (a `[H,W,C]`
  slice — passing the 4-D batch tensor straight to `Image.fromarray` raises), and
  `pil_to_tensor` re-adds a batch dim per frame, so collect the results and finish with
  `torch.cat(frames, dim=0)` rather than returning a list.
- Keep the geometry separable from torch. Put the arithmetic
  (`img_w, img_h, target_w, target_h, subscale -> new_w, new_h, x_off, y_off`) in a plain
  function with no torch/PIL dependency, mirroring how `m_prompt.py` stays importable
  without ComfyUI. It makes every arithmetic case in the checklist below verifiable from a
  one-line `python -c`, which matters because torch/numpy/Pillow are not installed for the
  Python on PATH in this dev environment — only inside ComfyUI's own env.
- Guard against `img_w == 0` or `img_h == 0` (shouldn't happen, but don't crash).
- Guard against `fit_scale` producing `new_w == 0` or `new_h == 0` when `subscale` is very
  small — clamp to minimum `1` pixel.

## File structure

This ships inside the existing `m9-prompts-comfyui` package — **not** a standalone custom
node folder. Add one module alongside the existing ones:

```
m9-prompts-comfyui/
├── __init__.py            # merges both modules' mappings
├── m9_prompt_nodes.py     # existing: ScramblePrompts_m9, TweakWeights_m9
├── m9_fit_pose_node.py    # new: FitPose_m9 node wrapper (torch/PIL/numpy)
├── m_fitpose.py           # new: pure geometry, no torch/PIL imports
└── m_prompt.py            # existing, untouched
```

The geometry lives in its own `m_fitpose.py` rather than inside the node module, so it
stays importable without torch — same `m_prompt.py` / `m9_prompt_nodes.py` split the
package already uses. It exposes `calc_fit(img_w, img_h, target_w, target_h, subscale)`
-> `(new_w, new_h, x_offset, y_offset)` and `target_from_latent(latent)` -> `(w, h)` or
`None`.

`__init__.py` merges the two mapping dicts:
```python
from .m9_prompt_nodes import NODE_CLASS_MAPPINGS as PROMPT_CLASS_MAPPINGS, \
    NODE_DISPLAY_NAME_MAPPINGS as PROMPT_NAME_MAPPINGS
from .m9_fit_pose_node import NODE_CLASS_MAPPINGS as FITPOSE_CLASS_MAPPINGS, \
    NODE_DISPLAY_NAME_MAPPINGS as FITPOSE_NAME_MAPPINGS

NODE_CLASS_MAPPINGS = {**PROMPT_CLASS_MAPPINGS, **FITPOSE_CLASS_MAPPINGS}
NODE_DISPLAY_NAME_MAPPINGS = {**PROMPT_NAME_MAPPINGS, **FITPOSE_NAME_MAPPINGS}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
```

`m9_fit_pose_node.py`: implement the `FitPose_m9` class with:
- `INPUT_TYPES(cls)` classmethod per the Inputs table above (note `latent` should be
  under `"optional"` in the input dict, everything else under `"required"`).
- `RETURN_TYPES = ("IMAGE", "INT", "INT")`
- `RETURN_NAMES = ("image", "width", "height")`
- `FUNCTION = "fit"`
- `CATEGORY = "image/transform"`
- `fit(self, image, subscale, interpolation, latent=None, width=1024, height=1024)`
  method implementing the behavior spec above.
- Its own `NODE_CLASS_MAPPINGS` / `NODE_DISPLAY_NAME_MAPPINGS` dicts (`FitPose_m9` ->
  `"FitPose [m9]"`) for `__init__.py` to merge.

The existing nodes print a colored load/status banner via the `Color9` helper in
`m9_prompt_nodes.py`. Reuse it rather than reimplementing if this node needs console output.

### Packaging

`pyproject.toml` needs its `description` and `version` updated before the next Comfy
Registry publish — done as part of this change. No new dependencies: `torch`, `numpy`, and
`Pillow` all come from ComfyUI's own environment, so `pyproject.toml` stays dependency-free.
README still documents only the two prompt nodes and needs a `FitPose [m9]` section.

## Testing checklist

Everything except the last item is pure arithmetic and can be checked against the
torch-free geometry function without a running ComfyUI; the interpolation item needs a
visual check in the app.

- [ ] Square pose image → square target: `subscale=1.0` fills edge-to-edge, no black
      border.
- [ ] Portrait pose image → landscape target: image height-fits, black bars on left/right.
- [ ] Landscape pose image → portrait target: image width-fits, black bars on top/bottom.
- [ ] `subscale=0.8`: confirm ~20% margin appears along the previously-edge-touching axis.
- [ ] `subscale=0.5`: image roughly half size, centered, large black margin all around.
- [ ] `subscale=1.5`: image overflows canvas — confirm it crops cleanly rather than
      erroring or wrapping.
- [ ] `LATENT` input connected: confirm target dims correctly read as `latent_h*8` /
      `latent_w*8` and override the width/height widgets.
- [ ] Batch of >1 pose images processed in one call → all frames fit independently and
      correctly, and the result is a single concatenated `[B,H,W,3]` tensor.
- [ ] Small pose image (e.g. 512px) → larger target (1024px) at `subscale=1.0`: confirm it
      upscales to touch the edges rather than sitting native-size in the middle.
- [ ] `interpolation="nearest"` produces visibly sharper/blockier lines than `"lanczos"`
      on a heavily downscaled pose image.
