import functools
import hashlib
import re

import nltk  # type: ignore

# Monkeypatch nltk.downloader.md5 to include usedforsecurity=False
nltk.downloader.md5 = functools.partial(hashlib.md5, usedforsecurity=False)

nltk.download("stopwords", quiet=True)
from nltk.corpus import stopwords  # type: ignore # noqa: E402

nltk.download("wordnet", quiet=True)
from nltk.stem.wordnet import WordNetLemmatizer  # type: ignore # noqa: E402 # @nutjob4life: 😩
from pds_doi_service.core.util.general_util import get_logger  # noqa: E402

logger = get_logger(__name__)


class KeywordTokenizer:
    def __init__(self):
        logger.debug("initialize keyword tokenizer")
        self.pos_dict = {"pds", "mars"}
        self._stop_words = set(stopwords.words("english"))
        self._keywords = set()

    def process_text(self, text):
        # Remove punctuations
        logger.debug(f"extract keywords from {text}")
        # Fix regex patterns to avoid potential catastrophic backtracking
        # Limit consecutive non-alphanumeric chars to a reasonable maximum (100)
        text = re.sub("^[^a-zA-Z0-9]{1,100}", " ", text)
        text = re.sub("[^a-zA-Z0-9]{1,100}$", " ", text)
        text = re.sub("[^a-zA-Z0-9]{1,100} ", " ", text)
        text = re.sub(" [^a-zA-Z0-9]{1,100}", " ", text)

        # Convert to lowercase
        text = text.lower()

        # Remove tags with bounded repetition
        # Replace non-greedy .* pattern with character class and bounded repetition
        text = re.sub("&lt;/?[^&>]{0,1000}&gt;", " &lt;&gt; ", text)

        # Remove special characters with bounded repetition
        text = re.sub(r"(\|\\W){1,100}", " ", text)

        # Convert to list from string
        text = text.split()

        # Lemmatisation
        lem = WordNetLemmatizer()
        keyword_set = set(
            [word if word in self.pos_dict else lem.lemmatize(word) for word in text if word not in self._stop_words]
        )

        self._keywords |= keyword_set

        logger.debug(f"new keyword list is {self._keywords}")

    def get_keywords(self):
        return self._keywords
