#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUTHOR

    Sébastien Le Maguer <sebastien.lemaguer@helsinki.fi>

DESCRIPTION

LICENSE
    This script is in the public domain, free from copyrights or restrictions.
    Created: 13 March 2025
"""

# System/default
import pathlib

# Arguments
import argparse

# Messaging/logging
import logging
from logging.config import dictConfig

# Shell
import shutil

from .metadata import Metadata, MetadataExtractor


###############################################################################
# global constants
###############################################################################
LEVEL = [logging.INFO, logging.DEBUG]


###############################################################################
# Functions
###############################################################################
def configure_logger(args) -> logging.Logger:
    """Setup the global logging configurations and instanciate a specific logger for the current script

    Parameters
    ----------
    args : dict
        The arguments given to the script

    Returns
    --------
    the logger: logger.Logger
    """
    # create logger and formatter
    logger = logging.getLogger()

    # Verbose level => logging level
    log_level = args.verbosity
    if args.verbosity >= len(LEVEL):
        log_level = len(LEVEL) - 1
        # logging.warning("verbosity level is too high, I'm gonna assume you're taking the highest (%d)" % log_level)

    # Define the default logger configuration
    logging_config = dict(
        version=1,
        disable_existing_logger=True,
        formatters={
            "f": {
                "format": "[%(asctime)s] [%(levelname)s] — [%(name)s — %(funcName)s:%(lineno)d] %(message)s",
                "datefmt": "%d/%b/%Y: %H:%M:%S ",
            }
        },
        handlers={
            "h": {
                "class": "logging.StreamHandler",
                "formatter": "f",
                "level": LEVEL[log_level],
            }
        },
        root={"handlers": ["h"], "level": LEVEL[log_level]},
    )

    # Add file handler if file logging required
    if args.log_file is not None:
        logging_config["handlers"]["f"] = {
            "class": "logging.FileHandler",
            "formatter": "f",
            "level": LEVEL[log_level],
            "filename": args.log_file,
        }
        logging_config["root"]["handlers"] = ["h", "f"]

    # Setup logging configuration
    dictConfig(logging_config)

    # Retrieve and return the logger dedicated to the script
    logger = logging.getLogger(__name__)
    return logger


def define_argument_parser() -> argparse.ArgumentParser:
    """Defines the argument parser

    Returns
    --------
    The argument parser: argparse.ArgumentParser
    """
    parser = argparse.ArgumentParser(description="")

    # Add logging options
    parser.add_argument("-l", "--log_file", default=None, help="Logger file")
    parser.add_argument(
        "-v",
        "--verbosity",
        action="count",
        default=0,
        help="increase output verbosity",
    )

    # Add overriding options
    parser.add_argument(
        "-a",
        "--arxiv-id",
        default=None,
        type=str,
        help="Assume the paper is an arxiv preprint, extract and then override the DOI using the ID",
    )
    parser.add_argument(
        "-d", "--doi", default=None, type=str, help="Override the DOI (this override has priority over any other ones)"
    )
    parser.add_argument("-n", "--dry-run", action="store_true", help="Activate the dry run mode")
    parser.add_argument("-N", "--no-text-search", action="store_true", help="Prevent to search using the full text")
    parser.add_argument("-t", "--title", default=None, type=str, help="Override the title")

    # Add arguments
    parser.add_argument("input_pdf", help="The input PDF file to rename")

    # Return parser
    return parser


###############################################################################
# Helper functions
###############################################################################


###############################################################################
#  Entry point
###############################################################################
def main():
    # Initialization
    arg_parser = define_argument_parser()
    args = arg_parser.parse_args()
    logger = configure_logger(args)

    input_pdf = pathlib.Path(args.input_pdf)
    output_dir = input_pdf.parent

    extractor = MetadataExtractor(input_pdf, args.arxiv_id, args.doi, args.title, args.no_text_search)
    metadata = extractor.extract_metadata()

    final_name = metadata.generate_pdf_filename()
    if not args.dry_run:
        shutil.move(input_pdf, output_dir / final_name)
        logger.info(f"{input_pdf} renamed to {output_dir}/{final_name}")
    else:
        logger.info(f"[dry-run] {input_pdf} renamed to {output_dir}/{final_name}")


###############################################################################
#  Envelopping
###############################################################################
if __name__ == "__main__":
    main()
