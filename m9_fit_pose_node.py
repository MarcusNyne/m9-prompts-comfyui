import numpy as np
import torch
from PIL import Image

from .m_fitpose import calc_fit, target_from_latent

# Image.Resampling exists on Pillow >= 9.1; older releases expose the constants on Image.
_Resampling = getattr(Image, "Resampling", Image)

INTERPOLATION_FILTERS = {
    "lanczos": _Resampling.LANCZOS,
    "bicubic": _Resampling.BICUBIC,
    "bilinear": _Resampling.BILINEAR,
    "nearest": _Resampling.NEAREST,
}


def tensor_to_pil(inFrame):
    # inFrame is a single [H, W, C] slice, not the [B, H, W, C] batch.
    i = 255. * inFrame.cpu().numpy()
    return Image.fromarray(np.clip(i, 0, 255).astype(np.uint8)).convert("RGB")


def pil_to_tensor(inImage):
    # Returns [1, H, W, C]; callers concatenate these back into a batch.
    arr = np.array(inImage).astype(np.float32) / 255.0
    return torch.from_numpy(arr)[None,]


class FitPose_m9:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"image": ("IMAGE", ),
                                "subscale": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 2.0, "step": 0.01}),
                                "interpolation": (["lanczos", "bicubic", "bilinear", "nearest"], {"default": "lanczos"}),
                                "width": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8}),
                                "height": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 8}),
                            },
                "optional":{"latent": ("LATENT", ),
                            }}

    RETURN_TYPES = ("IMAGE", "INT", "INT", )
    RETURN_NAMES = ("image", "width", "height", )

    FUNCTION = "fit"

    # image/transform is where the stock resize/crop/pad ops live (ImageCrop, ImageStitch,
    # ResizeAndPadImage). Not image/postprocessing -- that's for after-generation filters.
    CATEGORY = "image/transform"

    def fit(self, image, subscale, interpolation, width=1024, height=1024, latent=None):
        target_w = width
        target_h = height
        if latent is not None:
            # A connected latent takes priority over the width/height widgets.
            latent_size = target_from_latent(latent)
            if latent_size is not None:
                target_w, target_h = latent_size

        resample = INTERPOLATION_FILTERS.get(interpolation, _Resampling.LANCZOS)

        frames = []
        for x in range(image.shape[0]):
            frame = tensor_to_pil(image[x])
            new_w, new_h, x_offset, y_offset = calc_fit(frame.width, frame.height, target_w, target_h, subscale)
            resized = frame.resize((new_w, new_h), resample)

            canvas = Image.new("RGB", (target_w, target_h), (0, 0, 0))
            # paste() crops against the canvas edges when the offsets are negative,
            # which is how subscale > 1 overflow is handled. Slicing would wrap instead.
            canvas.paste(resized, (x_offset, y_offset))

            frames.append(pil_to_tensor(canvas))

        if len(frames) == 0:
            return (image, target_w, target_h, )

        return (torch.cat(frames, dim=0), target_w, target_h, )


NODE_CLASS_MAPPINGS = {
    "FitPose_m9": FitPose_m9
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "FitPose_m9": "FitPose [m9]"
}
