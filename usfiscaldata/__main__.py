import argparse
import logging

from usfiscaldata import FiscalData

logger = logging.getLogger("usfiscaldata.__main__")


def setup_logging():
    root_logger = logging.getLogger("usfiscaldata")
    root_logger.setLevel(logging.DEBUG)

    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        fmt="[%(asctime)s] %(levelname)s - %(message)s - %(filename)s[%(lineno)d]"
    )
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)


def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "endpoint",
        help="dot-separated endpoint, e.g. 'v1.accounting.od.auctions_query'",
    )
    parsed_args = parser.parse_args()
    setup_logging()

    endpoint: str = parsed_args.endpoint

    response = FiscalData()(endpoint)()
    response.log_metadata()


if __name__ == "__main__":
    cli()
