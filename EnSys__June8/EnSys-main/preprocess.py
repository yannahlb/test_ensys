from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.sentiment.vader import SentimentIntensityAnalyzer

class TextPreprocessor:
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()
        self.analyzer = SentimentIntensityAnalyzer()
        self.menu_keywords = {'menu', 'dessert', 'drinks', 'main course', 'pasta', 'salad', 'sides', 'baked lasagna', 'seafood sotanghon'}

    def preprocess(self, text):
        print("Original text:", text)  # Debugging
        tokens = word_tokenize(text)
        lowercased = [w.lower() for w in tokens]
        filtered = [w for w in lowercased if w not in self.stop_words or w in self.menu_keywords]
        lemmatized = [w if w in self.menu_keywords else self.lemmatizer.lemmatize(w) for w in filtered]
        preprocessed_text = ' '.join(lemmatized)
        print("Preprocessed text:", preprocessed_text)  # Debugging
        return preprocessed_text

    def get_sentiment(self, text):
        sentiment_scores = self.analyzer.polarity_scores(text)
        print("Sentiment scores:", sentiment_scores)  # Debugging
        return sentiment_scores