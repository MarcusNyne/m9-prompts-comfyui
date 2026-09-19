from .m_cropratio import ratio_from_image
from .m_scalefactor import calc_scale


class CalcScaleFactor_m9:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        # The size comes in the same way CropToRatio [m9] takes its ratio: image overrides
        # the width/height sockets, and all three sit in optional so wiring only one side
        # is a complete graph. Only the image's shape is read, never its pixels.
        return {"required": {"megapixels": ("FLOAT", {"default": 1.0, "min": 0.01, "max": 64.0, "step": 0.01}),
                            },
                "optional":{"image": ("IMAGE", ),
                            "width": ("INT", {"forceInput": True}),
                            "height": ("INT", {"forceInput": True}),
                            }}

    RETURN_TYPES = ("FLOAT", "INT", "INT", )
    RETURN_NAMES = ("scale_factor", "width", "height", )

    FUNCTION = "calc"

    # image/upscaling is where the stock ImageScaleBy and ImageScaleToTotalPixels live --
    # the nodes this one's outputs are meant to drive.
    CATEGORY = "image/upscaling"

    # width/height default to 0 -- no size given -- which calc_scale reads as a pass-through.
    def calc(self, megapixels, width=0, height=0, image=None):
        src_w = width
        src_h = height
        if image is not None:
            # A connected image takes priority over the width/height inputs.
            size = ratio_from_image(image)
            if size is not None:
                src_w, src_h = size

        return calc_scale(src_w, src_h, megapixels)


NODE_CLASS_MAPPINGS = {
    "CalcScaleFactor_m9": CalcScaleFactor_m9
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CalcScaleFactor_m9": "CalcScaleFactor [m9]"
}
