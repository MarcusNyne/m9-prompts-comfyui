from .m_cropratio import calc_crop, ratio_from_image, sModes, sDefaultMode

# Dropdown order for the mode widget; the values themselves come from m_cropratio so
# the widget can't drift from the gate that reads them.
MODES = list(sModes)


class CropToRatio_m9:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"image": ("IMAGE", ),
                                "mode": (MODES, {"default": sDefaultMode}),
                                "width": ("INT", {"default": 1024, "min": 1, "max": 8192, "step": 1}),
                                "height": ("INT", {"default": 1024, "min": 1, "max": 8192, "step": 1}),
                            },
                "optional":{"ratio_image": ("IMAGE", ),
                            }}

    RETURN_TYPES = ("IMAGE", "INT", "INT", )
    RETURN_NAMES = ("image", "width", "height", )

    FUNCTION = "crop"

    # image/transform is where the stock resize/crop/pad ops live (ImageCrop, ImageStitch,
    # ResizeAndPadImage), and where FitPose [m9] sits.
    CATEGORY = "image/transform"

    def crop(self, image, mode=sDefaultMode, width=1024, height=1024, ratio_image=None):
        ratio_w = width
        ratio_h = height
        if ratio_image is not None:
            # A connected ratio image takes priority over the width/height widgets.
            ratio_size = ratio_from_image(ratio_image)
            if ratio_size is not None:
                ratio_w, ratio_h = ratio_size

        src_h = int(image.shape[1])
        src_w = int(image.shape[2])

        new_w, new_h, x_offset, y_offset = calc_crop(src_w, src_h, ratio_w, ratio_h, mode)

        if new_w == src_w and new_h == src_h:
            # Nothing to trim: hand back the original tensor rather than a copy of it.
            return (image, src_w, src_h, )

        # Every frame of a batch shares one size, so a single slice crops the whole batch.
        # The offsets are non-negative and inside the source, so this can't wrap the way
        # a negative index would. contiguous() because the slice is a view and downstream
        # nodes that reshape or hand the tensor to numpy expect a packed buffer.
        cropped = image[:, y_offset:y_offset + new_h, x_offset:x_offset + new_w, :].contiguous()

        return (cropped, new_w, new_h, )


NODE_CLASS_MAPPINGS = {
    "CropToRatio_m9": CropToRatio_m9
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CropToRatio_m9": "CropToRatio [m9]"
}
