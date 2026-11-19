from enum import Enum


class CameraIntents(str, Enum):
    ACTION_STILL_IMAGE_CAMERA = 'android.media.action.STILL_IMAGE_CAMERA'
    ACTION_VIDEO_CAMERA = 'android.media.action.VIDEO_CAMERA'
    ACTION_IMAGE_CAPTURE = 'android.media.action.IMAGE_CAPTURE'

    def __str__(self) -> str:
        return self.value
