import re

from Stemmer import Stemmer


class Tokenizer:
   
    DEFAULT_STOPWORDS = {
        'o', 'a', 'os', 'as', 'um', 'uma', 'uns', 'umas',
        'de', 'do', 'da', 'dos', 'das', 'dum', 'duma', 'duns', 'dumas',
        'em', 'no', 'na', 'nos', 'nas', 'num', 'numa', 'nuns', 'numas',
        'por', 'pelo', 'pela', 'pelos', 'pelas',
        'ao', 'aos', 'à', 'às',
        'para', 'com', 'sem', 'sob', 'sobre',
        'e', 'ou', 'mas', 'porém', 'contudo', 'todavia',
        'que', 'se', 'não', 'nem',
        'mais', 'menos', 'muito', 'muita', 'muitos', 'muitas',
        'pouco', 'pouca', 'poucos', 'poucas',
        'todo', 'toda', 'todos', 'todas',
        'já', 'ainda', 'também', 'só', 'apenas', 'somente',
        'até', 'desde', 'quando', 'onde', 'como', 'porque', 'porquê',
        'isso', 'isto', 'esse', 'esta', 'este', 'essa',
        'desse', 'desta', 'deste', 'dessa',
        'nesse', 'nesta', 'neste', 'nessa',
        'aquele', 'aquela', 'aquilo', 'aqueles', 'aquelas',
        'ele', 'ela', 'eles', 'elas',
        'eu', 'tu', 'você', 'vocês', 'nós', 'vós',
        'me', 'te', 'se', 'lhe', 'lhes', 'nos', 'vos',
        'meu', 'minha', 'meus', 'minhas',
        'teu', 'tua', 'teus', 'tuas',
        'seu', 'sua', 'seus', 'suas',
        'nosso', 'nossa', 'nossos', 'nossas',
        'vosso', 'vossa', 'vossos', 'vossas',
        'dele', 'dela', 'deles', 'delas',
        'qual', 'quais', 'quem', 'cujo', 'cuja', 'cujos', 'cujas',
        'quanto', 'quanta', 'quantos', 'quantas',
        'ser', 'estar', 'ter', 'haver', 'fazer', 'ir', 'poder',
        'dizer', 'dar', 'ver', 'saber', 'querer', 'ficar', 'vir',
        'foi', 'é', 'são', 'era', 'eram', 'será', 'serão',
        'está', 'estão', 'estava', 'estavam', 'estará', 'estarão',
        'tem', 'têm', 'tinha', 'tinham', 'terá', 'terão',
        'há', 'havia', 'haverá', 'houve',
        'faz', 'fazem', 'fazia', 'faziam', 'fará', 'farão', 'fez', 'fizeram',
        'vai', 'vão', 'ia', 'iam', 'irá', 'irão',
        'pode', 'podem', 'podia', 'podiam', 'poderá', 'poderão', 'pôde', 'puderam',
        'diz', 'dizem', 'dizia', 'diziam', 'dirá', 'dirão', 'disse', 'disseram'
    }
    
    def __init__(self, min_len=2, use_stem=True, use_stopwords=True,
                 remove_numbers=False, custom_stopwords=None, language='portuguese'):
       
        self.tokenizer_re = re.compile(r'\w+')
        self.min_len = min_len
        self.use_stem = use_stem
        self.remove_numbers = remove_numbers
        self.language = language
        
        # Setup stopwords
        base_stopwords = self.DEFAULT_STOPWORDS.copy() if use_stopwords else set()
        if custom_stopwords:
            base_stopwords |= set(custom_stopwords)
        self.stop_words = base_stopwords
        
        # Setup stemmer (PyStemmer is 10-100x faster than NLTK)
        self.stemmer = Stemmer(language) if use_stem else None
        
        # Regex to detect pure numbers
        self.num_re = re.compile(r"^\d+$")
    
    def tokenize(self, text):
       
        if not text:
            return
        
        # Step 1 & 2: Tokenization + Normalization (lowercase)
        text = text.lower()
        
        # Extract all word tokens
        for token in self.tokenizer_re.findall(text):
            # Filter by minimum length
            if len(token) < self.min_len:
                continue
            
            # Optionally remove pure numbers
            if self.remove_numbers and self.num_re.match(token):
                continue
            
            # Step 3: Stop word removal
            if token in self.stop_words:
                continue
            
            # Step 4: Stemming
            if self.stemmer:
                token = self.stemmer.stemWord(token)
            
            yield token
    
    def tokenize_list(self, text):
       
        return list(self.tokenize(text))
    
    def tokenize_batch(self, texts):
       
        return [self.tokenize_list(text) for text in texts]
    
    def get_vocabulary(self, texts):
       
        vocab = set()
        for text in texts:
            vocab.update(self.tokenize(text))
        return vocab
    
    def get_config(self):
        """Get tokenizer configuration (only __init__ parameters)."""
        return {
            "language": self.language,
            "min_len": self.min_len,
            "use_stem": self.use_stem,
            "use_stopwords": bool(self.stop_words),
            "remove_numbers": self.remove_numbers,
            "custom_stopwords": None  # Can't serialize the actual set
        }
    
    def get_stats(self):
        """Get tokenizer statistics (non-constructor info)."""
        return {
            "num_stopwords": len(self.stop_words),
            "has_stemmer": self.stemmer is not None
        }
    
    def __repr__(self):
        config = self.get_config()
        stats = self.get_stats()
        all_info = {**config, **stats}
        return f"Tokenizer({', '.join(f'{k}={v}' for k, v in all_info.items())})"