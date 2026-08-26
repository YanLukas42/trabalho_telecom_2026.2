"""
Audio Dynamic Range and Loudness Normalization.
Applies EBU R128 loudness normalization and peak gain leveling for optimal ASR recognition.
"""

class AudioNormalizer:
    """Generates FFmpeg audio filters for volume normalization."""

    @staticmethod
    def get_loudnorm_filter_string(integrated_lufs: float = -16.0) -> str:
        """
        Applies EBU R128 loudness normalization filter (loudnorm).
        Integrated target default: -16 LUFS (optimal for speech intelligibility).
        """
        return f"loudnorm=I={integrated_lufs}:TP=-1.5:LRA=11"
