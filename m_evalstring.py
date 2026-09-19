# Choice evaluation and random line picking for EvaluateStringMultiline [m9].
# Deliberately free of ComfyUI imports so the logic can be exercised standalone,
# the same way m_stepreplace.py can be.

import random

# Relative inside the package (how ComfyUI loads it), plain when run from the checkout.
try:
    from .m_stepreplace import expand_choices
except ImportError:
    from m_stepreplace import expand_choices


def pick_line(inText, inRng=None):
    """One randomly chosen line of the text, or "" when it has none.

    Lines are trimmed, and blank or whitespace-only lines are never picked, so a
    trailing newline or a spacer line can't come back as an empty result.  With a
    single non-blank line, that line is always the one returned.
    """
    if inRng is None:
        inRng = random.Random()

    lines = [line.strip() for line in str(inText).splitlines()]
    lines = [line for line in lines if line != ""]

    if len(lines) == 0:
        return ""
    if len(lines) == 1:
        # No draw, so a one-line value doesn't consume a number from the generator.
        return lines[0]
    return inRng.choice(lines)


def evaluate_string(inText, inSeed=None):
    """Resolve every { a | b } in the text, then pick one line of the result.

    Returns (text, random_line).  The line is drawn from the evaluated text, so it
    always matches a line of the text output.  inSeed of None seeds from entropy; any
    other value makes both outputs reproducible.  One generator serves both steps.
    """
    rng = random.Random(inSeed)
    text = expand_choices(inText, rng)
    return (text, pick_line(text, rng))
