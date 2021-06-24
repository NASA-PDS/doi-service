import re
import nltk

nltk.download('stopwords', quiet=True)
from nltk.corpus import stopwords

nltk.download('wordnet', quiet=True)
from nltk.stem.wordnet import WordNetLemmatizer
from pds_doi_service.core.util.general_util import get_logger

logger = get_logger(__name__)


class KeywordTokenizer():
    def __init__(self):
        logger.debug('initialize keyword tokenizer')
        self.pos_dict = {'pds', 'mars'}
        self._stop_words = set(stopwords.words("english"))
        self._keywords = set()

    def process_text(self, text):
        # Remove punctuations
        logger.debug(f'extract keywords from {text}')
        text = re.sub('^[^a-zA-Z0-9]+', ' ', text)
        text = re.sub('[^a-zA-Z0-9]+$', ' ', text)
        text = re.sub('[^a-zA-Z0-9]+ ', ' ', text)
        text = re.sub(' [^a-zA-Z0-9]+', ' ', text)

        # Convert to lowercase
        text = text.lower()

        # remove tags
        text = re.sub("&lt;/?.*?&gt;", " &lt;&gt; ", text)

        # remove special characters
        text = re.sub("(\|\\W)+", " ", text)

        # Convert to list from string
        text = text.split()

        # Lemmatisation
        lem = WordNetLemmatizer()
        keyword_set = set([word if word in self.pos_dict else lem.lemmatize(word)
                           for word in text if word not in self._stop_words])

        self._keywords |= keyword_set

        logger.debug(f'new keyword list is {self._keywords}')

    def get_keywords(self):
        return self._keywords
