import logging
import re
import pathlib

# Papers
from papers.extract import pdfhead
from papers.extract import fetch_bibtex_by_doi, fetch_bibtex_by_arxiv, fetch_bibtex_by_fulltext_scholar
from papers.encoding import standard_name, family_names
from papers.encoding import standard_name, family_names

import pymupdf
import bibtexparser

DOI_REGEXP = r"10\.\d{4,9}\/[-._;()/:A-Za-z0-9]+[A-Za-z0-9]"


def first_names(author: str) -> list[str]:
    """Extract firstnames from the AUTHOR parameters."""
    authors = standard_name(author).split(" and ")
    return [nm.split(",")[1].strip() for nm in authors]


def fix_title(title: str) -> str:
    title = title.replace(": ", " - ")
    title = title.replace("/", "_")
    return re.sub(r'[\'"‘’]', "", title)


class Metadata:
    def __init__(self, bibtex_str: str):
        bib = bibtexparser.loads(bibtex_str)
        entry = bib.entries[0]

        self._content = entry

    def generate_pdf_filename(self) -> str:
        # Generate accurate format for author
        fam_names = family_names(self._content.get("author", "unknown").lower())
        try:
            fir_names = first_names(self._content.get("author", "unknown").lower())
        except Exception:
            raise Exception(
                'The following author self._content doesn\'t contain proper author names: "%s"'
                % (self._content.get("author", "unknown"))
            )

        if (not fam_names) or (fam_names[0] == "unknown"):
            raise Exception('%s doesn\'t have proper author: "%s"' % (self._content, str(fam_names)))

        year = self._content["year"]
        first_initial = fir_names[0][0].capitalize()
        last_name = fam_names[0].capitalize()
        title = fix_title(self._content["title"])

        return f"{year} - {first_initial}. {last_name} - {title}.pdf"


class MetadataExtractor:
    def __init__(
        self,
        pdf_path: pathlib.Path,
        arxiv_id: str | None = None,
        doi: str | None = None,
        title: str | None = None,
        disable_text_search: bool = False,
    ):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._pdf_path: pathlib.Path = pdf_path
        self._arxiv_id: str | None = arxiv_id
        self._doi: str | None = doi
        self._title: str | None = title
        self._no_text_search: bool = disable_text_search

    def extract_metadata(self) -> Metadata:
        bibtex_str = None
        if self._arxiv_id is not None:
            bibtex_str = fetch_bibtex_by_arxiv(self._arxiv_id)
        else:
            if self._doi is None:
                self._doi = self._extract_doi_from_pdf()

            if self._doi is not None:
                self._logger.debug(f"We found a doi: {self._doi}, let's try crossref")
                bibtex_str = fetch_bibtex_by_doi(self._doi)
                if bibtex_str is None:
                    self._logger.warning(f"Metadata couldn't be loaded from DOI: {self._doi}")

        if (bibtex_str is None) and (not self._no_text_search):
            self._logger.debug(f"Nothing worked up to now, let's try google scholar")

            # Override the title and actually set it as the query
            if self._title is not None:
                query_text = self._title.lower().strip()
            else:
                query_text = pdfhead(str(self._pdf_path.resolve()), 1, 100, image=False)

            bibtex_str = fetch_bibtex_by_fulltext_scholar(query_text)
            if bibtex_str is not None:
                bib = bibtexparser.loads(bibtex_str)
                entry = bib.entries[0]
                title = entry["title"]
                if (self._title is not None) and (title.lower().strip() != self._title.lower().strip()):
                    raise Exception(f"The retrieved entry is not the correct one, retrieved title: {title}")

                self._logger.debug(f"google scholar do provide some bibtex_str: {bibtex_str}")

        if bibtex_str is None:
            raise Exception(f'Could not find any metadata for "{self._pdf_path}"')

        return Metadata(bibtex_str)

    def _extract_doi_from_pdf(self):
        """Extracts DOI from the PDF's metadata or text."""
        doc = pymupdf.open(str(self._pdf_path.resolve()))

        # First try to find DOI in metadata (if available)
        metadata = doc.metadata
        if (metadata is None) or (not isinstance(metadata, dict)):
            return None

        if "doi" in metadata:
            return metadata["doi"]

        # Otherwise, extract text and search for DOI
        first_page_text = doc[0].get_text("text")
        self._logger.debug(f"First page text:\n{first_page_text}")
        doi_match = re.findall(DOI_REGEXP, first_page_text)
        if len(doi_match) > 0:
            return doi_match[0]

        return None
