from argparse import ArgumentParser


def get_option():
    argparser = ArgumentParser()
    argparser.add_argument(
        "-M",
        "--member",
        type=str,
        default=None,
        help="Only members that contain strings",
    )
    argparser.add_argument(
        "-N", "--nogi", action="store_true", help="if scraping only nogizaka"
    )
    argparser.add_argument(
        "-S", "--sakura", action="store_true", help="if scraping only sakurazaka"
    )
    argparser.add_argument(
        "-H", "--hinata", action="store_true", help="if scraping only hinatazaka"
    )
    argparser.add_argument("-D", "--debug", action="store_true", help="debug mode")
    argparser.add_argument(
        "-B", "--back_ground", action="store_true", help="make back ground image"
    )

    return argparser.parse_args()
