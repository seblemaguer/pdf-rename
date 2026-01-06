# PDF rename files

Rename files to be more homogeneous using the meta-data or the google scholar information

## Installation

Clone the current repository and run pip:

```sh
pip install -e .
```

## Run

The command is the following:

```sh
usage: pdf_rename [-h] [-l LOG_FILE] [-v] [-a ARXIV_ID] [-d DOI] [-n] [-N] [-t TITLE] input_pdf

positional arguments:
  input_pdf             The input PDF file to rename

options:
  -h, --help            show this help message and exit
  -l LOG_FILE, --log_file LOG_FILE
                        Logger file
  -v, --verbosity       increase output verbosity
  -a ARXIV_ID, --arxiv-id ARXIV_ID
                        Assume the paper is an arxiv preprint, extract and then override the DOI using the
                        ID
  -d DOI, --doi DOI     Override the DOI (this override has priority over any other ones)
  -n, --dry-run         Activate the dry run mode
  -N, --no-text-search  Prevent to search using the full text
  -t TITLE, --title TITLE
                        Override the title
```
