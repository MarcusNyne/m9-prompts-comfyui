from .m_prefix import build_prefix


class Prefix_m9:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        # All four are required widgets rather than optional inputs so they show as text
        # fields on the node; an empty field is simply skipped. Any of them can still be
        # converted to an input and driven by another node.
        return {"required": {"name": ("STRING", {"default": "", "multiline": False}),
                                "theme": ("STRING", {"default": "", "multiline": False}),
                                "scene": ("STRING", {"default": "", "multiline": False}),
                                "frame": ("STRING", {"default": "", "multiline": False}),
                            }}

    RETURN_TYPES = ("STRING", )
    RETURN_NAMES = ("prefix", )

    FUNCTION = "build"

    # utils is where the stock string/primitive helpers live, so this sits next to the
    # other plumbing nodes rather than in conditioning with the CLIP-encoding ones.
    CATEGORY = "utils"

    def build(self, name="", theme="", scene="", frame=""):
        return (build_prefix(name, theme, scene, frame), )


NODE_CLASS_MAPPINGS = {
    "Prefix_m9": Prefix_m9
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Prefix_m9": "Prefix [m9]"
}
