# Ordered search-and-replace with inline random choices, for StepReplace [m9].
# Deliberately free of ComfyUI imports so the logic can be exercised standalone,
# the same way m_prompt.py, m_fitpose.py and m_prefix.py can be.

import random
import re


# A choice is written { one | two | three } and collapses to exactly one option.
# Braces only count as a choice when they contain a separator -- {like_this} is left
# alone, so text that merely happens to use braces comes through unchanged.
sChoicePattern = re.compile(r'\{([^{}]*)\}')
sChoiceSeparator = '|'

# Choices nest: { a | { b | c } } resolves innermost-first, one pass per level of
# depth.  The cap only exists so a pathological input can't spin forever.
sMaxChoicePasses = 20

# \{ \| \} escape a literal brace or pipe.  They are swapped out before parsing and
# back in afterwards, the same trick m_prompt.py uses for escaped parenthesis.
sEscapes = ((r'\{', '@@1@@'), (r'\|', '@@2@@'), (r'\}', '@@3@@'))


def _protect(inText):
    for escaped, placeholder in sEscapes:
        inText = inText.replace(escaped, placeholder)
    return inText


def _restore(inText):
    # The backslash is dropped here -- an escaped brace was always meant to come out bare.
    for escaped, placeholder in sEscapes:
        inText = inText.replace(placeholder, escaped[1:])
    return inText


def _is_word_char(inChar):
    return inChar.isalnum() or inChar == '_'


def expand_choices(inText, inRng=None):
    """Collapse every { a | b } in the text down to one randomly chosen option.

    Options are trimmed, so { a | b } and {a|b} behave identically, and an empty
    option ({ a || b }) is a legitimate way to choose nothing at all.
    """
    if inText is None:
        return ""
    if inRng is None:
        inRng = random.Random()

    text = _protect(str(inText))

    for _ in range(sMaxChoicePasses):
        expanded = False

        def pick(inMatch):
            nonlocal expanded
            body = inMatch.group(1)
            if sChoiceSeparator not in body:
                # Not a choice; hand the braces back untouched.
                return inMatch.group(0)
            expanded = True
            return inRng.choice([o.strip() for o in body.split(sChoiceSeparator)])

        text = sChoicePattern.sub(pick, text)
        if not expanded:
            break

    return _restore(text)


def build_pattern(inSearch):
    """Compile one search term into a case-insensitive pattern.

    The term is escaped, so it always matches literally -- [FIND_THIS] and
    <lora:foo:0.8> mean exactly what they say.  A word boundary is added only at an
    end whose own character is a word character, so `cat` will not match inside
    `category`, while a term wrapped in brackets still matches wherever it appears.
    """
    pattern = re.escape(inSearch)
    if _is_word_char(inSearch[0]):
        pattern = r'\b' + pattern
    if _is_word_char(inSearch[-1]):
        pattern = pattern + r'\b'
    return re.compile(pattern, re.IGNORECASE)


def apply_step(inText, inSearch, inReplace, inRng=None):
    """Replace every occurrence of one search term.  Returns (text, count).

    The replacement is expanded at the moment it is inserted, so each occurrence
    draws its own choice: three hits of a { rose | tulip } replacement can produce
    three different flowers.  An empty or whitespace-only search term is a no-op,
    and an empty replacement deletes the term.
    """
    text = "" if inText is None else str(inText)
    search = "" if inSearch is None else str(inSearch).strip()
    replace = "" if inReplace is None else str(inReplace).strip()

    if search == "":
        return (text, 0)

    if inRng is None:
        inRng = random.Random()

    def swap(inMatch):
        return expand_choices(replace, inRng)

    return build_pattern(search).subn(swap, text)


def step_replace(inText, inPairs, inSeed=None):
    """Run each (search, replace) pair in turn over the running text.

    Pairs are applied top to bottom against the result of the pair before it, so a
    later search term can match text an earlier replacement produced.  Choices in
    the incoming text are resolved before the first pair runs, for the same reason:
    nothing downstream should ever have to look inside an unresolved { a | b }.

    Returns (text, log).  inSeed of None seeds from entropy; any other value makes
    the whole run reproducible.  One generator is built here and shared by every
    draw in the run -- seeding per draw would return the same option every time.
    """
    rng = random.Random(inSeed)
    log = []

    text = expand_choices(inText, rng)

    for step, pair in enumerate(inPairs, start=1):
        search = "" if pair[0] is None else str(pair[0]).strip()
        replace = pair[1]

        if search == "":
            log.append("step {n}: skipped (no search term)".format(n=step))
            continue

        text, count = apply_step(text, search, replace, rng)

        if count == 0:
            log.append("step {n}: '{s}' not found".format(n=step, s=search))
        else:
            log.append("step {n}: '{s}' replaced {c} time{p}".format(
                n=step, s=search, c=count, p="" if count == 1 else "s"))

    return (text, "\n".join(log))
