# Pure string assembly for Prefix [m9].
# Deliberately free of ComfyUI imports so the logic can be exercised standalone,
# the same way m_prompt.py and m_fitpose.py can be.

# Emitted when every field is empty. Matches ComfyUI's own default filename_prefix,
# so an unconfigured node behaves exactly like an unconnected SaveImage.
sDefaultPrefix = "ComfyUI"

sSeparator = "_"

# Characters Windows forbids outright, plus the two path separators -- those are legal
# on disk but would redirect the file into a subfolder, which isn't what a prefix field
# is for. Note this also flattens ComfyUI's %date:yyyy-MM-dd% tokens, since they contain
# a colon; sanitizing is a deliberate choice here, not an oversight.
sUnsafeChars = '<>:"/\\|?*'
sReplacementChar = "_"


def sanitize_part(inValue):
    """Trim one field and replace anything illegal in a filename.

    Unsafe characters are replaced rather than dropped, so two halves of a value can't
    silently run together. Returns "" for a value that is empty or whitespace only.
    """
    if inValue is None:
        return ""

    out = []
    for ch in str(inValue).strip():
        # Control characters are illegal too, and invisible, so they'd be baffling to debug.
        if ch in sUnsafeChars or ord(ch) < 32:
            out.append(sReplacementChar)
        else:
            out.append(ch)

    # Windows silently drops trailing dots and spaces, so strip them here instead --
    # otherwise the name on disk wouldn't match the one in the widget.
    return "".join(out).rstrip(". ")


def build_prefix(inName=None, inTheme=None, inScene=None, inFrame=None):
    """Join the supplied fields with underscores, skipping the ones left empty.

    Separators only appear between parts that are actually present, so a lone name
    comes back with no underscores at all. Returns sDefaultPrefix when nothing is
    supplied, so the result is always a usable prefix.
    """
    parts = [sanitize_part(p) for p in (inName, inTheme, inScene, inFrame)]
    parts = [p for p in parts if p != ""]

    if len(parts) == 0:
        return sDefaultPrefix

    return sSeparator.join(parts)
