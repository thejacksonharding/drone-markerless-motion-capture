from .simple_transform import SimpleTransform
from .simple_transform_3d_smpl import SimpleTransform3DSMPL
from .simple_transform_3d_smpl_cam import SimpleTransform3DSMPLCam
from .simple_transform_cam import SimpleTransformCam

__all__ = [
    'SimpleTransform', 'SimpleTransform3DSMPL', 'SimpleTransform3DSMPLCam', 'SimpleTransformCam',
    'SimpleTransform3DSMPLX']


def __getattr__(name):
    # The SMPL-X transform constructs its body model at import time. Load it
    # only when requested so the SMPL demo needs only the SMPL model files.
    if name == 'SimpleTransform3DSMPLX':
        from .simple_transform_3d_smplx import SimpleTransform3DSMPLX
        globals()[name] = SimpleTransform3DSMPLX
        return SimpleTransform3DSMPLX
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
