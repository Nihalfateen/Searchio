import re

from nltk.corpus import stopwords

'''
Portuguese stop words list sourced from NLTK:

'a'	'à'	'ao'	'aos'	'aquela'
'aquelas'	'aquele'	'aqueles'	'aquilo'	'as'
'às'	'até'	'com'	'como'	'da'
'das'	'de'	'dela'	'delas'	'dele'
'deles'	'depois'	'do'	'dos'	'e'
'é'	'ela'	'elas'	'ele'	'eles'
'em'	'entre'	'era'	'eram'	'éramos'
'essa'	'essas'	'esse'	'esses'	'esta'
'está'	'estamos'	'estão'	'estar'	'estas'
'estava'	'estavam'	'estávamos'	'este'	'esteja'
'estejam'	'estejamos'	'estes'	'esteve'	'estive'
'estivemos'	'estiver'	'estivera'	'estiveram'	'estivéramos'
'estiverem'	'estivermos'	'estivesse'	'estivessem'	'estivéssemos'
'estou'	'eu'	'foi'	'fomos'	'for'
'fora'	'foram'	'fôramos'	'forem'	'formos'
'fosse'	'fossem'	'fôssemos'	'fui'	'há'
'haja'	'hajam'	'hajamos'	'hão'	'havemos'
'haver'	'hei'	'houve'	'houvemos'	'houver'
'houvera'	'houverá'	'houveram'	'houvéramos'	'houverão'
'houverei'	'houverem'	'houveremos'	'houveria'	'houveriam'
'houveríamos'	'houvermos'	'houvesse'	'houvessem'	'houvéssemos'
'isso'	'isto'	'já'	'lhe'	'lhes'
'mais'	'mas'	'me'	'mesmo'	'meu'
'meus'	'minha'	'minhas'	'muito'	'na'
'não'	'nas'	'nem'	'no'	'nos'
'nós'	'nossa'	'nossas'	'nosso'	'nossos'
'num'	'numa'	'o'	'os'	'ou'
'para'	'pela'	'pelas'	'pelo'	'pelos'
'por'	'qual'	'quando'	'que'	'quem'
'são'	'se'	'seja'	'sejam'	'sejamos'
'sem'	'ser'	'será'	'serão'	'serei'
'seremos'	'seria'	'seriam'	'seríamos'	'seu'
'seus'	'só'	'somos'	'sou'	'sua'
'suas'	'também'	'te'	'tem'	'tém'
'temos'	'tenha'	'tenham'	'tenhamos'	'tenho'
'terá'	'terão'	'terei'	'teremos'	'teria'
'teriam'	'teríamos'	'teu'	'teus'	'teve'
'tinha'	'tinham'	'tínhamos'	'tive'	'tivemos'
'tiver'	'tivera'	'tiveram'	'tivéramos'	'tiverem'
'tivermos'	'tivesse'	'tivessem'	'tivéssemos'	'tu'
'tua'	'tuas'	'um'	'uma'	'você'
'vocês'	'vos'

'''
from nltk.stem.snowball import SnowballStemmer
from nltk.tokenize import RegexpTokenizer


class Tokenizer:
    def __init__(self,
                 min_len=2,
                 use_stem=True,
                 use_stopwords=True,
                 remove_numbers=True,
                 remove_alphanumerics=True,
                 use_dates=True,
                 filter_repetitive=True,
                 custom_stopwords=None):
        """
        Tokenizer for Portuguese text with flexible configuration options.
        """
        
        self.tokenizer = RegexpTokenizer(r'[A-Za-zÀ-ÿ0-9]+(?:[/\-][A-Za-zÀ-ÿ0-9]+)*') # Matches words, numbers, and hyphenated/slash-separated tokens

        # Configuration flags
        self.min_len = min_len
        self.use_stem = use_stem
        self.use_stopwords = use_stopwords
        self.remove_numbers = remove_numbers
        self.remove_alphanumerics = remove_alphanumerics
        self.use_dates = use_dates
        self.filter_repetitive = filter_repetitive

        # Stopwords
        base_stopwords = set(stopwords.words('portuguese')) if use_stopwords else set()
        if custom_stopwords:
            base_stopwords |= set(custom_stopwords)
        self.stop_words = base_stopwords

        # Stemmer
        self.stemmer = SnowballStemmer("portuguese") if use_stem else None

        # Regex definitions
        self.num_re = re.compile(r"^\d+$") # Matches numeric-only tokens
        # Matches years from 1000 to 2099
        self.year_re = re.compile(r"^(1[0-9]{3}|20[0-9]{2})$")
        self.date_re = re.compile(r"^(?:0?[1-9]|[12]\d|3[01])([/\-])(0?[1-9]|1[0-2])\1(1|2)\d{3}$") # Matches dates like "dd/mm/yyyy" or "dd-mm-yy"
        self.word_re = re.compile(r"^[a-zA-ZÀ-ÿ]+$") # Matches pure alphabetic words
        self.alnum_re = re.compile(r"^(?=.*[a-zA-ZÀ-ÿ])(?=.*\d)[A-Za-zÀ-ÿ0-9]+$") # Matches alphanumeric mixes
        self.repetitive_re = re.compile(r"^([a-z])\1{2,}$") # Matches overly repetitive tokens like "aaaaaa"

    def is_valid_token(self, token):
        """Check if token should be kept."""
        # Accept valid years and dates (if enabled)
        if self.use_dates and (self.year_re.match(token) or self.date_re.match(token)):
            return True

        # Keep pure alphabetic words
        if self.word_re.match(token):
            # Reject overly repetitive or low-diversity tokens if enabled
            if self.filter_repetitive:
                unique_chars = set(token)
                if len(unique_chars) <= 3 and len(token) > 8:
                    return False
                if self.repetitive_re.match(token):
                    return False
            return True

        # Remove alphanumeric mixes like "a400m" if requested
        if self.remove_alphanumerics and self.alnum_re.match(token):
            return False

        return False

    def tokenize(self, text):
        """Generate cleaned tokens from text according to configuration."""
        text = text.lower()

        for t in self.tokenizer.tokenize(text):
            # Minimum length
            if len(t) < self.min_len + 1:
                continue

            # Stopword filtering
            if t in self.stop_words:
                continue

            # Remove numeric-only tokens unless valid year/date
            if self.remove_numbers and self.num_re.match(t):
                if not (self.use_dates and (self.year_re.match(t) or self.date_re.match(t))):
                    continue

            # Remove tokens starting with digits unless date/year
            if self.remove_numbers and re.match(r"^\d", t):
                if not (self.use_dates and (self.year_re.match(t) or self.date_re.match(t))):
                    continue

            # Validate token
            if not self.is_valid_token(t):
                continue

            # Skip tokens with too many separators
            if t.count('-') + t.count('/') >  2:
                continue
            
            # Apply stemming
            if self.stemmer:
                t = self.stemmer.stem(t)

            yield t

    def get_config(self):
        """Return a configuration dictionary for saving tokenizer settings."""
        return {
            "min_len": self.min_len,
            "use_stem": self.use_stem,
            "use_stopwords": self.use_stopwords,
            "remove_numbers": self.remove_numbers,
            "remove_alphanumerics": self.remove_alphanumerics,
            "use_dates": self.use_dates,
            "filter_repetitive": self.filter_repetitive,
            "custom_stopwords": list(self.stop_words) if self.stop_words else None,
        }

    @classmethod
    def from_config(cls, config):
        """Recreate a Tokenizer from a saved configuration dictionary."""
        return cls(
            min_len=config.get("min_len", 2),
            use_stem=config.get("use_stem", True),
            use_stopwords=config.get("use_stopwords", True),
            remove_numbers=config.get("remove_numbers", True),
            remove_alphanumerics=config.get("remove_alphanumerics", True),
            use_dates=config.get("use_dates", True),
            filter_repetitive=config.get("filter_repetitive", True),
            custom_stopwords=config.get("custom_stopwords", None),
        )


# Example usage:
# tokenizer = Tokenizer()
# tokens = list(tokenizer.tokenize("41-44/1891 emprego711313-36363122371969201 11-12 01/07/1960 78-79-80 1200 seríamos B.C a0110  89-0 Exemplo 1949 aabbbbaabba gh-uo 19494 a400m y  yy  ypy de texto a/67/317 para ab-rog teste tokenização afastam-s afro-stalinism aaaaa em 05-10-2023 a2/3 a9culo-xix-967e6bbd00c2  ."))
# print(tokens) # Output the tokens generated by the tokenizer
