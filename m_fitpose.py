# Pure geometry for FitPose [m9].
# Deliberately free of torch/PIL/ComfyUI imports so the arithmetic can be exercised
# standalone, the same way m_prompt.py can be.

# ComfyUI latents are [batch, channels, h, w] where h/w are 1/8 the pixel dimensions.
# Holds for SD1.5, SDXL, SD3 and Flux; revisit if a future VAE uses a different factor.
sLatentScaleFactor = 8


def calc_fit(inImageW, inImageH, inTargetW, inTargetH, inSubscale):
    """Fit an image into a target canvas without stretching.

    Returns (new_w, new_h, x_offset, y_offset). Offsets are top-left paste coordinates
    and go negative when inSubscale > 1, which is intended: the image overflows and is
    cropped by the canvas edges.
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

    x_offset = (inTargetW - new_w) // 2
    y_offset = (inTargetH - new_h) // 2

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
