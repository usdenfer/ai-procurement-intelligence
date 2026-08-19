import main


def test_build_parser_has_subcommands():
    parser = main.build_parser()
    args = parser.parse_args(["ingest"])
    assert args.command == "ingest"
    args = parser.parse_args(["ask", "预算多少"])
    assert args.command == "ask"
    assert args.question == "预算多少"
