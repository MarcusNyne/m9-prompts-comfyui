from .m_stepreplace import step_replace
from .m9_prompt_nodes import Color9

# How many search/replace pairs the node exposes.  The widgets and the pair list the
# node hands to step_replace() are both built from this, so they can't drift apart;
# step_replace() itself takes any number of pairs.
sStepCount = 5


class StepReplace_m9:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        # Dict order is widget order: text, then each search/replace pair, then the
        # print toggle.  `text` is forceInput -- the text lives in whatever node feeds
        # this one, which is the point of a node that only rewrites it.
        fields = {"text": ("STRING", {"forceInput": True})}
        for n in range(1, sStepCount + 1):
            fields["search_{n}".format(n=n)] = ("STRING", {"default": "", "multiline": False})
            fields["replace_{n}".format(n=n)] = ("STRING", {"default": "", "multiline": True})
        fields["print_output"] = ("BOOLEAN", {"default": False})

        return {"required": fields,
                "optional": {"seed_optional": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                            }}

    RETURN_TYPES = ("STRING", )
    RETURN_NAMES = ("text", )

    FUNCTION = "replace"

    # text is where upstream keeps its own string ops as of ComfyUI v0.34.0 (on older
    # builds that menu was utils/string), so this sits directly beside the stock
    # Replace Text node it extends.
    CATEGORY = "text"

    @classmethod
    def IS_CHANGED(s, seed_optional=0, **kwargs):
        # A seed of 0 means "re-roll every run".  ComfyUI folds this value into the
        # node's cache key, and NaN never compares equal to itself, so the node is
        # re-executed every queue instead of serving one cached variation forever.
        # Any other seed is returned as-is, leaving normal input-based caching alone.
        if not seed_optional:
            return float("nan")
        return seed_optional

    # The search/replace widgets arrive as keyword arguments named by the loop above,
    # so they are collected rather than spelled out one by one.
    def replace(self, text, print_output, seed_optional=0, **kwargs):
        pairs = [(kwargs.get("search_{n}".format(n=n), ""),
                  kwargs.get("replace_{n}".format(n=n), ""))
                 for n in range(1, sStepCount + 1)]

        # 0 is what an unconnected widget sends, and it is the one value that means
        # "no seed given" -- random.Random(None) then seeds from entropy.
        seed = None if not seed_optional else seed_optional

        final_text, log = step_replace(text, pairs, inSeed=seed)

        if print_output:
            clr = Color9("StepReplace [m9]")
            clr.Header()
            clr.Print(log, "LIGHTVIOLET")
            clr.Print(final_text, "LIGHTVIOLET")

        return (final_text, )


NODE_CLASS_MAPPINGS = {
    "StepReplace_m9": StepReplace_m9
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "StepReplace_m9": "StepReplace [m9]"
}
