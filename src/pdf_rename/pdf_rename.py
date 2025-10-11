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
import sys
import os
import re
import pathlib

# Arguments
import argparse

# Messaging/logging
import traceback
import logging
from logging.config import dictConfig

# Shell
import shutil

# Papers
import requests
import pymupdf
from papers.extract import extract_pdf_metadata
from papers.encoding import standard_name, family_names

# Bibtex
import bibtexparser

###############################################################################
# global constants
###############################################################################
LEVEL = [logging.INFO, logging.DEBUG]
DOI_REGEXP = r"/^10\.\d{4,9}\/[-._;()/:A-Z0-9]+$/i"


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
    parser.add_argument("-d", "--doi", default=None, type=str, help="Override the DOI")

    # Add arguments
    parser.add_argument("input_pdf", help="The input PDF file to rename")

    # Return parser
    return parser


###############################################################################
# Helper functions
###############################################################################


def first_names(author):
    """Extract firstnames from the AUTHOR parameters."""
    authors = standard_name(author).split(" and ")
    return [nm.split(",")[1].strip() for nm in authors]


def extract_doi_from_pdf(pdf_path: pathlib.Path):
    """Extracts DOI from the PDF's metadata or text."""
    doc = pymupdf.open(pdf_path)

    # First try to find DOI in metadata (if available)
    metadata = doc.metadata
    if (metadata is None) or (not isinstance(metadata, dict)):
        return None

    if "doi" in metadata:
        return metadata["doi"]

    # Otherwise, extract text and search for DOI
    first_page_text = doc[0].get_text("text")
    doi_match = re.search(DOI_REGEXP, first_page_text, re.IGNORECASE)
    if doi_match:
        return doi_match.group(0)

    return None


def get_metadata_from_crossref(doi) -> tuple[str, str, str, str] | None:
    """Fetches metadata from CrossRef API using DOI."""
    url = f"https://api.crossref.org/works/{doi}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        item = data["message"]
        # Extracting relevant metadata
        year = item["published"]["date-parts"][0][0]  # Year of publication
        title = item["title"][0]  # The title of the work
        authors = item["author"]
        first_author = authors[0] if authors else None
        first_name_initial = first_author["given"][:1] if first_author else "Unknown"
        last_name = first_author["family"] if first_author else "Unknown"

        return year, first_name_initial, last_name, title
    else:
        return None


def get_metadata_from_google_scholar(pdf_path: pathlib.Path) -> tuple[str, str, str, str]:
    # If no information, try to extract some additional part
    bibtex = extract_pdf_metadata(
        str(pdf_path.resolve()), search_doi=False, search_fulltext=True, scholar=False, minwords=200, max_query_words=200
    )

    bib = bibtexparser.loads(bibtex)
    entry = bib.entries[0]

    # Generate accurate format for author
    fam_names = family_names(entry.get("author", "unknown").lower())
    try:
        fir_names = first_names(entry.get("author", "unknown").lower())
    except Exception:
        raise Exception(
            'The following author entry doesn\'t contain proper author names: "%s"' % (entry.get("author", "unknown"))
        )

    if (not fam_names) or (fam_names[0] == "unknown"):
        raise Exception('%s doesn\'t have proper author: "%s"' % (pdf_path, str(fam_names)))

    return entry["year"], fir_names[0][0].capitalize(), fam_names[0].capitalize(), entry["title"]

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

    year, first_initial, last_name, title = (None, None, None, None)
    doi = args.doi
    if doi is None:
        doi = extract_doi_from_pdf(input_pdf)
    if doi is not None:
        logger.debug(f"We found a doi: {doi}, let's try crossref")
        metadata = get_metadata_from_crossref(doi)
        if metadata is not None:
            year, first_initial, last_name, title = metadata
            logger.debug(f"crossref do provide some metadata: {metadata}")

    # We
    if year is None:
        logger.debug(f"Nothing worked up to now, let's try google scholar")
        metadata = get_metadata_from_google_scholar(input_pdf)
        if metadata is not None:
            year, first_initial, last_name, title = metadata
            logger.debug(f"google scholar do provide some metadata: {metadata}")

    if year is None:
        logger.error(f"Didn't find anything, {input_pdf} is not renamed")
        sys.exit(-1)

    final_name = "%s - %s. %s - %s.pdf" % (year, first_initial, last_name, title)

    shutil.move(input_pdf, output_dir / final_name)
    logger.info(f"{input_pdf} renamed to {output_dir}/{final_name}")

###############################################################################
#  Envelopping
###############################################################################
if __name__ == "__main__":
    main()
