#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUTHOR

    Sébastien Le Maguer <sebastien.lemaguer@adaptcentre.ie>

DESCRIPTION

LICENSE
    This script is in the public domain, free from copyrights or restrictions.
    Created:  5 June 2020
"""

# System/default
import sys
import os

# Arguments
import argparse

# Messaging/logging
import traceback
import time
import logging

# Shell
import shutil
import glob

# Papers
from papers.extract import extract_pdf_doi, isvaliddoi, parse_doi
from papers.extract import extract_pdf_metadata
from papers.encoding import parse_file, format_file, standard_name, family_names, format_entries
from papers.extract import fetch_bibtex_by_fulltext_crossref, fetch_bibtex_by_doi

# Bibtex
import bibtexparser

###############################################################################
# global constants
###############################################################################
LEVEL = [logging.WARNING, logging.INFO, logging.DEBUG]


###############################################################################
# Functions
###############################################################################

def first_names(author):
    """Extract firstnames from the AUTHOR parameters.
    """
    authors = standard_name(author).split(' and ')
    return [nm.split(',')[1].strip() for nm in authors]

###############################################################################
# Main function
###############################################################################
def main():
    """Main entry function
    """
    global args, logger

    pdfs = []
    if args.input.endswith(".pdf"):
        pdfs = [args.input]
    elif not args.recursive:
        pdfs = [f for f in glob.glob("%s/*.pdf" % args.input)]
    else:
        pdfs = []
        for (dirpath, dirnames, filenames) in os.walk(args.input):
            for name in filenames:
                if name.endswith(".pdf"):
                    pdfs.append("%s/%s" % (dirpath, name))


    for cur_pdf in pdfs:
        print("")
        print("# ======================================================================")
        print("# Renaming %s..." % cur_pdf)
        print("# ======================================================================")
        try:
            bibtex = extract_pdf_metadata(cur_pdf,
                                          search_doi=False,
                                          search_fulltext=True,
                                          scholar=False,
                                          minwords=200,
                                          max_query_words=200)

            bib = bibtexparser.loads(bibtex)
            entry = bib.entries[0]

            # Generate accurate format for author
            fam_names = family_names(entry.get('author', 'unknown').lower())
            try:
                fir_names = first_names(entry.get('author', 'unknown').lower())
            except Exception:
                raise Exception("The following author entry doesn't contain proper author names: \"%s\"" % (entry.get('author', 'unknown')))

            if (not fam_names) or (fam_names[0] == "unknown"):
                logger.warning("%s doesn't have proper author: \"%s\"" % (cur_pdf, str(fam_names)))
                continue

            formatted_name = "%s. %s" % (fir_names[0][0].capitalize(), fam_names[0].capitalize())
            final_name = "%s - %s - %s.pdf" % (entry["year"], formatted_name, entry["title"])

            os.makedirs(args.output_dir, exist_ok=True)
            shutil.move(cur_pdf, "%s/%s" % (args.output_dir, final_name))
        except Exception as ex:
            if args.failed_dir is not None:
                os.makedirs(args.failed_dir, exist_ok=True)
                shutil.copyfile(cur_pdf, "%s/%s" % (args.failed_dir, os.path.basename(cur_pdf)))
            logger.error("Ignored as cannot rename \"%s\": %s" % (cur_pdf, ex))
            logger.error(str(ex))
            traceback.print_exc(file=sys.stderr)

###############################################################################
#  Envelopping
###############################################################################
if __name__ == '__main__':
    try:
        parser = argparse.ArgumentParser(description="")

        # Add options
        parser.add_argument("-f", "--failed-dir", type=str, default=None,
                            help="Directory to store all the files which have been failed to be renamed")
        parser.add_argument("-l", "--log_file", default=None,
                            help="Logger file")
        parser.add_argument("-r", "--recursive", action="store_true",
                            help="recursive list all pdf!")
        parser.add_argument("-v", "--verbosity", action="count", default=0,
                            help="increase output verbosity")

        # Add arguments
        parser.add_argument("input", help="pdf file or directory containing the pdf files to be renamed")
        parser.add_argument("output_dir", help="Output directory which will contain the renamed files")

        # Parsing arguments
        args = parser.parse_args()

        # create logger
        logger = logging.getLogger(os. path. basename(__file__).replace(".py", ""))

        # Define formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s: %(message)s')

        # Verbose level => logging level
        log_level = args.verbosity
        if (args.verbosity >= len(LEVEL)):
            log_level = len(LEVEL) - 1
            logger.warning("verbosity level is too high, I'm gonna assume you're taking the highest (%d)" % log_level)
        loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
        for l in loggers:
            l.setLevel(LEVEL[log_level])

        # create console handle
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        # create file handler
        if args.log_file is not None:
            fh = logging.FileHandler(args.log_file)
            logger.addHandler(fh)

        # Debug time
        start_time = time.time()
        logger.info("start time = " + time.asctime())

        # Running main function <=> run application
        main()

        # Debug time
        logger.info("end time = " + time.asctime())
        logger.info('TOTAL TIME IN MINUTES: %02.2f' %
                     ((time.time() - start_time) / 60.0))

        # Exit program
        sys.exit(0)
    except KeyboardInterrupt as e:  # Ctrl-C
        raise e
    except SystemExit:  # sys.exit()
        pass
    except Exception as e:
        logging.error('ERROR, UNEXPECTED EXCEPTION')
        logging.error(str(e))
        traceback.print_exc(file=sys.stderr)
        sys.exit(-1)
