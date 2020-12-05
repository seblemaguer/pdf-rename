# PDF rename files

Rename files to be more homogeneous using the meta-data or the google scholar information

## Installation

Just install and activate the conda environment:

```sh
conda env create -f environment.yaml
conda activate pdf-rename
```

## Run

The command is the following:

```sh
usage: pdf-rename.py [-h] [-f FAILED_DIR] [-l LOG_FILE] [-r] [-v]
                     input output_dir

positional arguments:
  input                 pdf file or directory containing the pdf files to be
                        renamed
  output_dir            Output directory which will contain the renamed files

optional arguments:
  -h, --help            show this help message and exit
  -f FAILED_DIR, --failed-dir FAILED_DIR
                        Directory to store all the files which have been
                        failed to be renamed
  -l LOG_FILE, --log_file LOG_FILE
                        Logger file
  -r, --recursive       recursive list all pdf!
  -v, --verbosity       increase output verbosity
```
