"""
Digital Signal Processing & Acoustic Filters for Speech Audio.
Simulates telephony bandwidths (narrowband) and human speech spectral ranges (wideband).
"""

from typing import Dict, Any, Optional


class AudioFilters:
    """Provides digital filtering presets via FFmpeg audio filter graphs."""

    @staticmethod
    def get_filter_string(filter_config: Optional[Dict[str, Any]]) -> Optional[str]:
        """
        Converts filter configuration dictionary into an FFmpeg audio filter string (-af).
        Supports bandpass, highpass, and lowpass.
        """
        if not filter_config:
            return None

        ftype = filter_config.get("type", "bandpass")
        low = filter_config.get("low", 80)
        high = filter_config.get("high", 7500)

        if ftype == "bandpass":
            # highpass at low cut, lowpass at high cut (Butterworth 2-pole equivalent)
            return f"highpass=f={low},lowpass=f={high}"
        elif ftype == "highpass":
            return f"highpass=f={low}"
        elif ftype == "lowpass":
            return f"lowpass=f={high}"
        
        return None

    @staticmethod
    def telephony_narrowband() -> Dict[str, Any]:
        """Classic PSTN Telephony filter (300 Hz - 3400 Hz)."""
        return {"type": "bandpass", "low": 300, "high": 3400}

    @staticmethod
    def voice_wideband() -> Dict[str, Any]:
        """Optimized Speech Wideband filter (80 Hz - 7500 Hz). Discards sub-bass and ultra-high noise."""
        return {"type": "bandpass", "low": 80, "high": 7500}
