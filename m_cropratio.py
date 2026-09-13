# Pure geometry for CropToRatio [m9].
# Deliberately free of torch/PIL/ComfyUI imports so the arithmetic can be exercised
# standalone, the same way m_fitpose.py can be.

# Which source images get cropped at all. The gate is on the *orientation of the
# incoming image and of the result*, not on which axis ends up being trimmed.
sModes = (
    "Vertical only",
    "Horizontal only",
    "Always",
)

sDefaultMode = "Always"


def _orientation(inW, inH):
    """1 for landscape, -1 for portrait, 0 for square."""
    return (inW > inH) - (inH > inW)


def _mode_allows(inSrcW, inSrcH, inNewW, inNewH, inMode):
    """Whether a crop from inSrc* to inNew* is permitted under inMode.

    A restricted mode never changes an image's orientation: "Vertical only" crops a
    portrait source and leaves it portrait. A landscape target ratio would flip it, so
    the image passes through untouched instead; a landscape source is not its business
    either way. "Horizontal only" is the mirror.

    Both ends are judged, not just the source, so the guarantee survives the rounding
    at extreme sizes -- a 1x8 source against a 832:1216 ratio computes to 1x1, which is
    square rather than portrait, and is refused here. Square is neither portrait nor
    landscape, so a square source or a square result declines under both restricted
    modes. An unrecognized mode falls back to "Always", which keeps calc_crop total.
    """
    if inMode == "Vertical only":
        return _orientation(inSrcW, inSrcH) < 0 and _orientation(inNewW, inNewH) < 0
    if inMode == "Horizontal only":
        return _orientation(inSrcW, inSrcH) > 0 and _orientation(inNewW, inNewH) > 0
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

    Under a restricted mode the result always has the same orientation as the source;
    see _mode_allows.
    """
    # Guards: these shouldn't happen, but a zero dimension would divide by zero.
    src_w = max(int(inSrcW), 1)
    src_h = max(int(inSrcH), 1)
    ratio_w = int(inRatioW)
    ratio_h = int(inRatioH)

    no_crop = (src_w, src_h, 0, 0)

    if ratio_w <= 0 or ratio_h <= 0:
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

    # Gated on the computed result, not just on the source, so a restricted mode can
    # never hand back an image whose orientation changed.
    if not _mode_allows(src_w, src_h, new_w, new_h, inMode):
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
