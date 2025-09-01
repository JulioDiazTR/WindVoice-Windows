class WindVoiceError(Exception):
    pass


class ConfigurationError(WindVoiceError):
    pass


class AudioError(WindVoiceError):
    pass


class TranscriptionError(WindVoiceError):
    pass


class TextInjectionError(WindVoiceError):
    pass


class HotkeyError(WindVoiceError):
    pass