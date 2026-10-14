from telecom.timefmt import format_clock, format_clock_ms, format_range


def test_format_clock_minutes_and_hours():
    assert format_clock(0.0) == "00:00"
    assert format_clock(45.2) == "00:45"
    assert format_clock(125.0) == "02:05"
    assert format_clock(3665.0) == "01:01:05"


def test_format_clock_ms_clamps_millis():
    assert format_clock_ms(61.5) == "01:01.500"
    assert format_clock_ms(0.9999) == "00:00.999"


def test_format_range():
    assert format_range(12.0, 18.0) == "00:12 - 00:18"
