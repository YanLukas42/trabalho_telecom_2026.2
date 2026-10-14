"""Formatação de tempos usada nos timestamps dos relatórios."""


def format_clock(seconds: float) -> str:
    """Formata segundos como MM:SS, ou HH:MM:SS a partir de uma hora."""
    seconds = max(0.0, seconds)
    hours, rest = divmod(int(seconds), 3600)
    minutes, secs = divmod(rest, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def format_range(start: float, end: float) -> str:
    """Intervalo no formato 'MM:SS - MM:SS', usado nos timestamps das falas."""
    return f"{format_clock(start)} - {format_clock(end)}"


def format_clock_ms(seconds: float) -> str:
    """Formata segundos como MM:SS.mmm (alinhamento palavra a palavra)."""
    seconds = max(0.0, seconds)
    minutes, secs = divmod(int(seconds), 60)
    millis = min(999, int(round((seconds - int(seconds)) * 1000)))
    return f"{minutes:02d}:{secs:02d}.{millis:03d}"
