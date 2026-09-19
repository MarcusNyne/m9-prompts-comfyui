from .m_evalstring import evaluate_string


class EvaluateStringMultiline_m9:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        # Modeled on the stock PrimitiveStringMultiline: one multiline `value` widget.
        # seed_optional works exactly as it does on StepReplace [m9].
        return {"required": {"value": ("STRING", {"default": "", "multiline": True}),
                            },
                "optional": {"seed_optional": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                            }}

    RETURN_TYPES = ("STRING", "STRING", )
    RETURN_NAMES = ("text", "random_line", )

    FUNCTION = "evaluate"

    # utilities/primitive is where the stock PrimitiveStringMultiline lives (it was
    # utils/primitive on older builds), so this sits directly beside the node it extends.
    CATEGORY = "utilities/primitive"

    @classmethod
    def IS_CHANGED(s, seed_optional=0, **kwargs):
        # Same convention as StepReplace [m9]: a seed of 0 means "re-roll every run".
        # NaN never compares equal to itself, so ComfyUI re-executes the node each queue
        # instead of serving one cached roll forever.  Any other seed is returned as-is.
        if not seed_optional:
            return float("nan")
        return seed_optional

    def evaluate(self, value, seed_optional=0):
        # 0 is what an unconnected widget sends, and it means "no seed given" --
        # random.Random(None) then seeds from entropy.
        seed = None if not seed_optional else seed_optional
        return evaluate_string(value, inSeed=seed)


NODE_CLASS_MAPPINGS = {
    "EvaluateStringMultiline_m9": EvaluateStringMultiline_m9
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "EvaluateStringMultiline_m9": "EvaluateStringMultiline [m9]"
}
