# Pure arithmetic for CalcScaleFactor [m9].
# Deliberately free of torch/PIL/ComfyUI imports so it can be exercised standalone,
# the same way m_cropratio.py can be.

# Every computed side lands on a multiple of this.
sStep = 32


def _snap(inValue, inStep=sStep):
    """Round to the nearest multiple of inStep, never below one step."""
    return max(int(round(inValue / inStep)) * inStep, inStep)


def calc_scale(inSrcW, inSrcH, inMegapixels, inStep=sStep):
    """Scale factor that takes a inSrcW x inSrcH image to roughly inMegapixels.

    Returns (scale_factor, new_w, new_h), both sides multiples of inStep. The step
    boundary takes priority over the megapixel target, so the result's area is
    approximate.

    The width is snapped from the ideal uniform factor, and scale_factor is then
    new_w / src_w, so scaling by it lands the width exactly on new_w. A single factor
    can't in general land both sides on the boundary -- most aspect ratios have no such
    factor anywhere near the target -- so new_h is the multiple nearest to what the
    factor actually gives the height, src_h * scale_factor. Scaling by the factor alone
    therefore comes within inStep / 2 of new_h -- unless the height is so small it
    clamps up to one step, as a 2340x3 source does.

    Total like calc_crop: a missing size or a non-positive target comes back as a
    pass-through, (1.0, src_w, src_h).
    """
    src_w = int(inSrcW)
    src_h = int(inSrcH)

    if src_w <= 0 or src_h <= 0 or inMegapixels <= 0:
        return (1.0, max(src_w, 0), max(src_h, 0))

    ideal = (inMegapixels * 1_000_000 / (src_w * src_h)) ** 0.5
    new_w = _snap(src_w * ideal, inStep)
    scale = new_w / src_w
    # From the final factor, not the ideal one, so new_h stays nearest to where scaling
    # by scale_factor actually puts the height.
    new_h = _snap(src_h * scale, inStep)

    return (scale, new_w, new_h)
