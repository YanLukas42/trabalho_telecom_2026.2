"""Cadeias de filtros FFmpeg (-af) usadas pelos tratamentos de áudio."""

# Passa-banda de voz humana: preserva F0 e formantes, descarta sub-graves e ruído agudo.
WIDEBAND_VOICE = "highpass=f=80,lowpass=f=7500"

# Canal telefônico clássico (PSTN).
TELEPHONY_NARROWBAND = "highpass=f=300,lowpass=f=3400"

# Normalização de loudness EBU R128.
LOUDNORM = "loudnorm=I=-16:TP=-1.5:LRA=11"


def silence_remove(threshold_db: float = -40.0, stop_duration_sec: float = 0.3) -> str:
    """Remove silêncios com o filtro silenceremove (VAD simples, sem mapa de tempo)."""
    return (
        "silenceremove=start_periods=1:start_duration=0.1"
        f":start_threshold={threshold_db}dB"
        f":stop_periods=-1:stop_duration={stop_duration_sec}"
        f":stop_threshold={threshold_db}dB"
    )
