class WindVoiceError(Exception):
    pass


class ConfigurationError(WindVoiceError):
    pass


class AudioError(WindVoiceError):
    pass


class AudioDeviceBusyError(AudioError):
    """Audio device is busy/in use by another application"""
    pass


class TranscriptionError(WindVoiceError):
    pass


class TextInjectionError(WindVoiceError):
    pass


class HotkeyError(WindVoiceError):
    pass