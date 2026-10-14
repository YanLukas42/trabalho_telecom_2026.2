"""Matrizes de experimentos: os tratamentos de cada estudo, como dados."""

from telecom.audio.filters import LOUDNORM, TELEPHONY_NARROWBAND, WIDEBAND_VOICE, silence_remove
from telecom.audio.preparer import Treatment

# Diarização (fase 2): comparação de bitrate, banda e VAD por mapa de tempo, com WER contra o baseline 320k.
DIARIZATION_MATRIX: tuple[Treatment, ...] = (
    Treatment("01_baseline_320k_stereo", "Baseline 320k Estéreo (Máxima Fidelidade)", "320k", 44100, 2,
              is_baseline=True),
    Treatment("02_bitrate_128k_stereo", "MP3 128k Estéreo (Padrão)", "128k", 44100, 2),
    Treatment("03_bitrate_64k_mono_wideband", "MP3 64k Mono + Filtro Voz Wideband", "64k", 16000, 1,
              filters=(WIDEBAND_VOICE,)),
    Treatment("04_bitrate_32k_mono_wideband", "MP3 32k Mono + Filtro Voz Wideband", "32k", 16000, 1,
              filters=(WIDEBAND_VOICE,)),
    Treatment("05_bitrate_16k_mono_wideband", "MP3 16k Mono + Filtro Voz Wideband", "16k", 16000, 1,
              filters=(WIDEBAND_VOICE,)),
    Treatment("06_bitrate_8k_mono_wideband", "MP3 8k Mono + Filtro Voz Wideband (Ultra-leve)", "8k", 16000, 1,
              filters=(WIDEBAND_VOICE,)),
    Treatment("07_bitrate_32k_stereo_spatial", "MP3 32k Estéreo (Espacialidade para Diarização)", "32k", 24000, 2),
    Treatment("08_vad_compact_32k_mono", "MP3 32k Mono + VAD (Compactação e Correção Temporal)", "32k", 16000, 1,
              filters=(WIDEBAND_VOICE,), compact_silence=True),
    Treatment("09_vad_compact_16k_opus", "OPUS 16k VBR Mono + VAD (Máxima Eficiência e Precisão)", "16k", 16000, 1,
              codec="opus", filters=(WIDEBAND_VOICE,), compact_silence=True),
)

# Benchmark de compressão MP3 (fase 1): varredura de bitrate, taxa de amostragem, canal, filtros, VAD e ganho.
MP3_MATRIX: tuple[Treatment, ...] = (
    Treatment("01_baseline_320k_stereo", "Baseline 320k (Stereo 44.1kHz)", "320k", 44100, 2,
              category="Bitrate Sweep", is_baseline=True),
    Treatment("02_bitrate_192k", "MP3 192k (Stereo 44.1kHz)", "192k", 44100, 2, category="Bitrate Sweep"),
    Treatment("03_bitrate_128k", "MP3 128k (Stereo 44.1kHz)", "128k", 44100, 2, category="Bitrate Sweep"),
    Treatment("04_bitrate_64k", "MP3 64k (Stereo 44.1kHz)", "64k", 44100, 2, category="Bitrate Sweep"),
    Treatment("05_bitrate_32k", "MP3 32k (Stereo 44.1kHz)", "32k", 44100, 2, category="Bitrate Sweep"),
    Treatment("06_bitrate_16k", "MP3 16k (Mono 22.05kHz)", "16k", 22050, 1, category="Bitrate Sweep"),
    Treatment("07_bitrate_8k", "MP3 8k (Mono 16kHz - Ultra-compressed)", "8k", 16000, 1, category="Bitrate Sweep"),
    Treatment("08_sample_rate_24k", "Sample Rate 24kHz (128k Stereo)", "128k", 24000, 2,
              category="Sample Rate Sweep"),
    Treatment("09_sample_rate_16k", "Sample Rate 16kHz (128k Stereo)", "128k", 16000, 2,
              category="Sample Rate Sweep"),
    Treatment("10_sample_rate_8k", "Sample Rate 8kHz Telephony (64k Stereo)", "64k", 8000, 2,
              category="Sample Rate Sweep"),
    Treatment("11_mono_downmix", "Downmix to Mono (128k 44.1kHz)", "128k", 44100, 1,
              category="Channel Optimization"),
    Treatment("12_filter_telecom_narrowband", "Filtro Telefonia Narrowband (300Hz-3.4kHz)", "64k", 16000, 1,
              category="Acoustic Filtering", filters=(TELEPHONY_NARROWBAND,)),
    Treatment("13_filter_voice_wideband", "Filtro Voz Humana Wideband (80Hz-7.5kHz)", "64k", 16000, 1,
              category="Acoustic Filtering", filters=(WIDEBAND_VOICE,)),
    Treatment("14_vad_silence_stripping", "VAD (Corte de Silêncio e Pausas)", "64k", 16000, 1,
              category="Temporal / VAD", filters=(silence_remove(),)),
    Treatment("15_loudness_normalized", "Normalização de Ganho / Volume", "64k", 16000, 1,
              category="Dynamic Range", filters=(LOUDNORM,)),
    Treatment("16_ai_optimized_mp3_candidate", "⭐ MP3 Otimizado para IA (Novo MP3)", "32k", 16000, 1,
              category="AI Optimized Recipe", filters=(WIDEBAND_VOICE, silence_remove(), LOUDNORM)),
)

MATRICES: dict[str, tuple[Treatment, ...]] = {
    "diarizacao": DIARIZATION_MATRIX,
    "mp3": MP3_MATRIX,
}
