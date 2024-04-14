import argparse

from excore import DictAction, load


def parse_args():
    parser = argparse.ArgumentParser(description="Test")
    parser.add_argument("--config", type=str)
    parser.add_argument(
        "--cfg-options",
        nargs="+",
        action=DictAction,
    )
    parser.add_argument("--dump", type=str)
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    print(args.cfg_options)
    print(args.dump)
    cfg = load(
        args.config,
        dump_path=args.dump,
        update_dict=args.cfg_options,
        parse_config=False,
    )
    assert "Test" in args.cfg_options
    assert args.cfg_options["Test"]["1"]["data"] == [0, 3]
    assert args.cfg_options["Test"]["2"] == 1
    assert args.cfg_options["Test"]["3"] == (0,)
    assert cfg.Test["1"]["data"] == [0, 3]
    assert cfg.Test["2"] == 1
    assert cfg.Test["3"] == (0,)
    assert "TMP" in args.cfg_options
    assert args.cfg_options["TMP"]["1"]["2"]["3"]["4"]["5"]["6"] == 7
    assert cfg.TMP["1"]["2"]["3"]["4"]["5"]["6"] == 7


if __name__ == "__main__":
    main()
