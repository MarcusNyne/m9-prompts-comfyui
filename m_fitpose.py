# Pure geometry for FitPose [m9].
# Deliberately free of torch/PIL/ComfyUI imports so the arithmetic can be exercised
# standalone, the same way m_prompt.py can be.

# ComfyUI latents are [batch, channels, h, w] where h/w are 1/8 the pixel dimensions.
# Holds for SD1.5, SDXL, SD3 and Flux; revisit if a future VAE uses a different factor.
sLatentScaleFactor = 8

# Where the fitted image sits on the canvas when it doesn't fill it (subscale < 1).
# Each entry maps to (horizontal, vertical) anchors; anything unrecognized falls back
# to centering on that axis, so calc_fit stays total for a garbage placement string.
sPlacements = {
    "centered":     ("center", "center"),
    "bottom":       ("center", "bottom"),
    "left":         ("left",   "center"),
    "right":        ("right",  "center"),
    "bottom-left":  ("left",   "bottom"),
    "bottom-right": ("right",  "bottom"),
}


def _anchor_offset(inSlack, inAnchor):
    # inSlack is target - new, so it goes negative when the image overflows the canvas.
    if inAnchor in ("left", "top"):
        return 0
    if inAnchor in ("right", "bottom"):
        return inSlack
    return inSlack // 2


def calc_fit(inImageW, inImageH, inTargetW, inTargetH, inSubscale, inPlacement="centered"):
    """Fit an image into a target canvas without stretching.

    Returns (new_w, new_h, x_offset, y_offset). Offsets are top-left paste coordinates
    and go negative when inSubscale > 1, which is intended: the image overflows and is
    cropped by the canvas edges. With an edge placement the overflow is pushed entirely
    to the opposite edge -- e.g. "left" keeps x_offset at 0 and crops off the right.
    """
    # Guards: these shouldn't happen, but a zero dimension would divide by zero.
    inImageW = max(int(inImageW), 1)
    inImageH = max(int(inImageH), 1)
    inTargetW = max(int(inTargetW), 1)
    inTargetH = max(int(inTargetH), 1)

    fit_scale = min(inTargetW / inImageW, inTargetH / inImageH)
    final_scale = fit_scale * max(float(inSubscale), 0.0)

    # Clamp to 1px so a very small subscale degrades to a dot rather than an empty resize.
    new_w = max(int(round(inImageW * final_scale)), 1)
    new_h = max(int(round(inImageH * final_scale)), 1)

    h_anchor, v_anchor = sPlacements.get(inPlacement, sPlacements["centered"])
    x_offset = _anchor_offset(inTargetW - new_w, h_anchor)
    y_offset = _anchor_offset(inTargetH - new_h, v_anchor)

    return (new_w, new_h, x_offset, y_offset)


def target_from_latent(inLatent, inScaleFactor=sLatentScaleFactor):
    """Derive (target_w, target_h) in pixels from a ComfyUI LATENT, or None if unusable.

    Only the spatial shape is read; a latent batch size that differs from the image
    batch size is ignored.
    """
    if not isinstance(inLatent, dict):
        return None

    samples = inLatent.get("samples")
    if samples is None:
        return None

    shape = getattr(samples, "shape", None)
    if shape is None or len(shape) < 4:
        return None

    return (int(shape[3]) * inScaleFactor, int(shape[2]) * inScaleFactor)
