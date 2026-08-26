"""
Voice Activity Detection (VAD) and Silence Stripping.
Removes dead air, prolonged pauses and non-speech silence to conserve transmission tokens.
"""

from typing import Dict, Any, Optional


class VoiceActivityDetector:
    """Applies silence removal and voice gating using FFmpeg silenceremove filter."""

    @staticmethod
    def get_vad_filter_string(
        stop_periods: int = -1,
        stop_duration_sec: float = 0.3,
        stop_threshold_db: float = -40.0
    ) -> str:
        """
        Generates FFmpeg silenceremove filter string:
        - stop_periods=-1: continuous removal across entire audio
        - stop_duration_sec: silences longer than this duration are trimmed
        - stop_threshold_db: noise floor below which audio is considered silence
        """
        # silenceremove filter trims both start silence and intermediate silences
        return f"silenceremove=start_periods=1:start_duration=0.1:start_threshold={stop_threshold_db}dB:stop_periods={stop_periods}:stop_duration={stop_duration_sec}:stop_threshold={stop_threshold_db}dB"
