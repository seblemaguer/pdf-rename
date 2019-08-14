#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUTHOR

    Sébastien Le Maguer <lemagues@tcd.ie>

DESCRIPTION

LICENSE
    This script is in the public domain, free from copyrights or restrictions.
    Created: 21 March 2019
"""

import os
import sys
import shutil
import traceback
import argparse
import time
import logging

LEVEL = [logging.WARNING, logging.INFO, logging.DEBUG]

import glob
import papers.bib
from papers.extract import extract_pdf_doi, isvaliddoi, parse_doi
from papers.extract import extract_pdf_metadata
from papers.encoding import parse_file, format_file, standard_name, family_names, format_entries
from papers.extract import fetch_bibtex_by_fulltext_crossref, fetch_bibtex_by_doi

import bibtexparser


###############################################################################
# Functions
###############################################################################

def first_names(author_field):
    authors = standard_name(author_field).split(' and ')
    return [nm.split(',')[1].strip() for nm in authors]



###############################################################################
# Main function
###############################################################################
def main():
    """Main entry function
    """
    global args

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
        logging.info("Renaming %s..." % cur_pdf)
        print("Renaming %s..." % cur_pdf)
        try:
            bibtex = extract_pdf_metadata(cur_pdf,
                                          search_doi=True,
                                          search_fulltext=True,
                                          scholar=True,
                                          minwords=200,
                                          max_query_words=200)

            bib = bibtexparser.loads(bibtex)
            entry = bib.entries[0]

            # Generate accurate format for author
            fam_names = family_names(entry.get('author', 'unknown').lower())
            fir_names = first_names(entry.get('author', 'unknown').lower())
            formatted_name = "%s. %s" % (fir_names[0][0].capitalize(), fam_names[0].capitalize())
            final_name = "%s - %s - %s.pdf" % (entry["year"], formatted_name, entry["title"])

            os.makedirs(args.output_dir, exist_ok=True)
            shutil.move(cur_pdf, "%s/%s" % (args.output_dir, final_name))
        except Exception as ex:
            if args.failed_dir is not None:
                os.makedirs(args.failed_dir, exist_ok=True)
                shutil.copyfile(cur_pdf, "%s/%s" % (args.failed_dir, os.path.basename(cur_pdf)))
            logging.error("Ignored as cannot rename \"%s\": %s" % (cur_pdf, ex))
            logging.error(str(ex))
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
        parser.add_argument("-r", "--recursive", action="store_true",
                            help="recursive list all pdf!")
        parser.add_argument("-v", "--verbosity", action="count", default=0,
                            help="increase output verbosity")

        # Add arguments
        parser.add_argument("input", help="input pdf file to be renamed")
        parser.add_argument("output_dir", help="Output directory")

        # Parsing arguments
        args = parser.parse_args()

        # Verbose level => logging level
        log_level = args.verbosity
        if (args.verbosity >= len(LEVEL)):
            log_level = len(LEVEL) - 1
            logging.basicConfig(level=LEVEL[log_level])
            logging.warning("verbosity level is too high, I'm gonna assume you're taking the highest (%d)" % log_level)
        else:
            logging.basicConfig(level=LEVEL[log_level])

        # Debug time
        start_time = time.time()
        logging.info("start time = " + time.asctime())

        # Running main function <=> run application
        main()

        # Debug time
        logging.info("end time = " + time.asctime())
        logging.info('TOTAL TIME IN MINUTES: %02.2f' %
                     ((time.time() - start_time) / 60.0))

        # Exit program
        sys.exit(0)
    except KeyboardInterrupt as e:  # Ctrl-C
        raise e
    except SystemExit as e:  # sys.exit()
        pass
    except Exception as e:
        logging.error('ERROR, UNEXPECTED EXCEPTION')
        logging.error(str(e))
        traceback.print_exc(file=sys.stderr)
        sys.exit(-1)
