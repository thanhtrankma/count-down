from app.services.ffmpeg_progress import parse_progress_file


def test_parse_progress_file_from_out_time_us():
    content = """
frame=100
out_time_us=5400000000
progress=continue
"""
    assert parse_progress_file(content, 10800) == 50.0


def test_parse_progress_file_uses_last_update():
    content = """
out_time_us=1000000
out_time_us=5000000
progress=continue
"""
    assert parse_progress_file(content, 10) == 50.0


def test_parse_progress_file_returns_none_without_out_time_us():
    assert parse_progress_file("progress=continue\n", 60) is None
