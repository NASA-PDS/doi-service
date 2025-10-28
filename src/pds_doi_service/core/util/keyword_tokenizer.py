import os
import re

import nltk  # type: ignore
from pds_doi_service.core.util.general_util import get_logger

logger = get_logger(__name__)

# Configure NLTK to use bundled data (FIPS-compatible, no MD5 downloads needed)
# Get the path to the bundled nltk_data directory
_bundled_nltk_data = os.path.join(os.path.dirname(__file__), "..", "..", "nltk_data")
_bundled_nltk_data = os.path.abspath(_bundled_nltk_data)

# Prepend bundled data path to NLTK's search path (takes precedence)
if _bundled_nltk_data not in nltk.data.path:
    nltk.data.path.insert(0, _bundled_nltk_data)
    logger.debug(f"Added bundled NLTK data path: {_bundled_nltk_data}")

# Import NLTK resources from bundled data (no download needed)
from nltk.corpus import stopwords  # type: ignore # noqa: E402
from nltk.stem.wordnet import WordNetLemmatizer  # type: ignore # noqa: E402


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
