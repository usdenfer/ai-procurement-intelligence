import main


def test_build_parser_has_subcommands():
    parser = main.build_parser()
    args = parser.parse_args(["ingest"])
    assert args.command == "ingest"
    args = parser.parse_args(["ask", "预算多少"])
    assert args.command == "ask"
    assert args.question == "预算多少"
    args = parser.parse_args(["schedule"])
    assert args.command == "schedule"
    assert args.interval_hours is None


def test_interval_hours_parses_flag_and_env(monkeypatch):
    assert main._interval_hours(12.0) == 12.0
    monkeypatch.setenv("AI_PROC_INTERVAL_HOURS", "6")
    assert main._interval_hours(None) == 6.0
    monkeypatch.setenv("AI_PROC_INTERVAL_HOURS", "bad")
    assert main._interval_hours(None) == 24.0
    monkeypatch.delenv("AI_PROC_INTERVAL_HOURS", raising=False)
    assert main._interval_hours(None) == 24.0
