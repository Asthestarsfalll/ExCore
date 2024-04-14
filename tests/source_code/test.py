import argparse

from mmengine.config import DictAction


def parse_args():
    parser = argparse.ArgumentParser(description="Train a model")
    parser.add_argument("config", help="train config file path")
    parser.add_argument(
        "--cfg-options",
        nargs="+",
        action=DictAction,
        help="override some settings in the used config, the key-value pair "
        "in xxx=yyy format will be merged into config file. If the value to "
        'be overwritten is a list, it should be like key="[a,b]" or key=a,b '
        'It also allows nested list/tuple values, e.g. key="[(a,b),(c,d)]" '
        "Note that the quotation marks are necessary and that no white space "
        "is allowed.",
    )

    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    print(args.cfg_options)


if __name__ == "__main__":
    main()
