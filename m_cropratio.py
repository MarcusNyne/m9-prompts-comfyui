# Pure geometry for CropToRatio [m9].
# Deliberately free of torch/PIL/ComfyUI imports so the arithmetic can be exercised
# standalone, the same way m_fitpose.py can be.

# Which source images get cropped at all. The gate is on the *orientation of the
# incoming image*, not on which axis ends up being trimmed.
sModes = (
    "Vertical only",
    "Horizontal only",
    "Always",
)

sDefaultMode = "Always"


def _mode_allows(inSrcW, inSrcH, inMode):
    """Whether an image of this shape is cropped at all under inMode.

    "Vertical only" crops portrait sources and passes landscape ones through
    untouched; "Horizontal only" is the mirror. A square source is neither portrait
    nor landscape, so both restricted modes leave it alone. An unrecognized mode
    falls back to "Always", which keeps calc_crop total.
    """
    if inMode == "Vertical only":
        return inSrcH > inSrcW
    if inMode == "Horizontal only":
        return inSrcW > inSrcH
    return True


def calc_crop(inSrcW, inSrcH, inRatioW, inRatioH, inMode=sDefaultMode):
    """Center-crop an image to a target aspect ratio by trimming a single axis.

    Only the ratio of inRatioW:inRatioH matters -- 1216x832 and 152x104 give the same
    crop. The image is never scaled and never grown: one axis is trimmed equally from
    both ends until the remainder matches the ratio.

    Returns (new_w, new_h, x_offset, y_offset), where the offsets are the top-left
    corner of the kept region. They are always >= 0 and the region always lies inside
    the source. An odd number of trimmed pixels leaves the extra one on the bottom or
    the right, so y_offset/x_offset floor.

    A pass-through -- ratio already matched, mode gates it out, or a ratio dimension is
    non-positive -- comes back as (inSrcW, inSrcH, 0, 0), which callers can test for.
    """
    # Guards: these shouldn't happen, but a zero dimension would divide by zero.
    src_w = max(int(inSrcW), 1)
    src_h = max(int(inSrcH), 1)
    ratio_w = int(inRatioW)
    ratio_h = int(inRatioH)

    no_crop = (src_w, src_h, 0, 0)

    if ratio_w <= 0 or ratio_h <= 0:
        return no_crop

    if not _mode_allows(src_w, src_h, inMode):
        return no_crop

    # Cross-multiplied comparison of src_w/src_h against ratio_w/ratio_h, so the
    # already-matching case is an exact integer test rather than a float one.
    src_cross = src_w * ratio_h
    ratio_cross = src_h * ratio_w

    if src_cross > ratio_cross:
        # Too wide for the ratio: trim the left and right edges.
        new_w = max(min(int(round(src_h * ratio_w / ratio_h)), src_w), 1)
        new_h = src_h
    elif src_cross < ratio_cross:
        # Too tall for the ratio: trim the top and bottom edges.
        new_h = max(min(int(round(src_w * ratio_h / ratio_w)), src_h), 1)
        new_w = src_w
    else:
        return no_crop

    return (new_w, new_h, (src_w - new_w) // 2, (src_h - new_h) // 2)


def ratio_from_image(inImage):
    """Derive (width, height) from a ComfyUI IMAGE tensor, or None if unusable.

    IMAGE is [batch, h, w, channels]. Only the spatial shape is read; the batch size
    of the ratio image is irrelevant, and so is everything but its proportions.
    """
    shape = getattr(inImage, "shape", None)
    if shape is None or len(shape) < 4:
        return None

    return (int(shape[2]), int(shape[1]))
