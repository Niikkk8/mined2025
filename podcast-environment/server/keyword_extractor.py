from sklearn.feature_extraction.text import TfidfVectorizer
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import string

nltk.download('punkt')
nltk.download('stopwords')

def extract_keywords(text, num_keywords=5):
    # Tokenize and clean the text
    tokens = word_tokenize(text.lower())
    stop_words = set(stopwords.words('english'))
    tokens = [token for token in tokens if token not in stop_words 
              and token not in string.punctuation
              and len(token) > 2]
    
    # Create document for TF-IDF
    document = ' '.join(tokens)
    
    # Calculate TF-IDF
    vectorizer = TfidfVectorizer(ngram_range=(1, 2))
    tfidf_matrix = vectorizer.fit_transform([document])
    
    # Get feature names and their scores
    feature_names = vectorizer.get_feature_names_out()
    scores = tfidf_matrix.toarray()[0]
    
    # Sort keywords by score
    keyword_scores = list(zip(feature_names, scores))
    keyword_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Return top keywords
    return [keyword for keyword, _ in keyword_scores[:num_keywords]]