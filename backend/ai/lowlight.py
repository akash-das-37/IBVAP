import cv2
import numpy as np

class LowLightEnhancer:
    """
    CLAHE (Contrast Limited Adaptive Histogram Equalization) preprocessor.
    Enhances contrast in low-light surveillance frames without washing out colors
    by operating strictly on the Luminance (L) channel in LAB color space.
    """

    def __init__(self, clip_limit: float = 2.5, tile_grid_size: tuple = (8, 8)):
        self.clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)

    def enhance(self, frame: np.ndarray) -> np.ndarray:
        if frame is None or frame.size == 0:
            return frame

        # Convert BGR to LAB color space
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)

        # Apply CLAHE to L-channel
        cl = self.clahe.apply(l)

        # Merge enhanced L-channel with original color channels
        limg = cv2.merge((cl, a, b))

        # Convert back to BGR
        enhanced_bgr = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
        return enhanced_bgr
