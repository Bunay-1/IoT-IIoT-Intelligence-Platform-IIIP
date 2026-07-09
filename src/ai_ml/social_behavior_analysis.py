"""
Social Behavior Analysis Module
Provides tools for analyzing social media data, including sentiment analysis,
topic modeling, and trend detection.
"""
import re
import string
import logging
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

# NLTK for text processing
try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer
    from nltk.tokenize import word_tokenize
    # Ensure NLTK data is downloaded
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('wordnet', quiet=True)
    nltk.download('vader_lexicon', quiet=True)
    from nltk.sentiment.vader import SentimentIntensityAnalyzer
except ImportError:
    logging.warning("NLTK not found. Please install it using: pip install nltk")
    # Provide dummy classes/functions if NLTK is not available
    SentimentIntensityAnalyzer = lambda: None

# Scikit-learn for topic modeling
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.decomposition import LatentDirichletAllocation
    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import KMeans
except ImportError:
    logging.warning("Scikit-learn not found. Please install it using: pip install scikit-learn")

from src.utils.logging_config import get_logger

logger = get_logger(__name__)

class SocialBehaviorAnalytics:
    """
    A comprehensive toolkit for analyzing social behavior from textual data.
    """
    def __init__(self, data: pd.DataFrame, text_column: str, user_column: str, timestamp_column: str):
        if not all(col in data.columns for col in [text_column, user_column, timestamp_column]):
            raise ValueError("One or more specified columns are not in the DataFrame.")

        self.data = data.copy()
        self.text_column = text_column
        self.user_column = user_column
        self.timestamp_column = timestamp_column
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))

        # Preprocess text data upon initialization
        self.data['processed_text'] = self.data[self.text_column].apply(self.preprocess_text)

    def preprocess_text(self, text: str) -> str:
        """
        Cleans and prepares text for analysis.
        - Lowercasing
        - Removing punctuation and numbers
        - Tokenization
        - Stopword removal
        - Lemmatization
        """
        text = text.lower()
        text = re.sub(r'\d+', '', text)
        text = text.translate(str.maketrans('', '', string.punctuation))
        tokens = word_tokenize(text)
        tokens = [self.lemmatizer.lemmatize(word) for word in tokens if word not in self.stop_words and len(word) > 2]
        return " ".join(tokens)

    def analyze_sentiment(self):
        """
        Performs sentiment analysis on the text data using NLTK's VADER.
        Adds 'sentiment_score' and 'sentiment_label' columns to the DataFrame.
        """
        sia = SentimentIntensityAnalyzer()
        self.data['sentiment_score'] = self.data[self.text_column].apply(
            lambda text: sia.polarity_scores(text)['compound']
        )

        def to_sentiment_label(score):
            if score > 0.05:
                return 'Positive'
            elif score < -0.05:
                return 'Negative'
            else:
                return 'Neutral'

        self.data['sentiment_label'] = self.data['sentiment_score'].apply(to_sentiment_label)
        logger.info("Sentiment analysis completed.")
        return self.data[['sentiment_score', 'sentiment_label']]

    def model_topics(self, n_topics: int = 5, n_top_words: int = 10):
        """
        Performs topic modeling using Latent Dirichlet Allocation (LDA).
        """
        vectorizer = TfidfVectorizer(max_df=0.95, min_df=2, stop_words='english')
        tfidf = vectorizer.fit_transform(self.data['processed_text'])

        lda = LatentDirichletAllocation(n_components=n_topics, random_state=42)
        lda.fit(tfidf)

        self.data['topic'] = lda.transform(tfidf).argmax(axis=1)

        # Get topic keywords
        feature_names = vectorizer.get_feature_names_out()
        topics = {}
        for topic_idx, topic in enumerate(lda.components_):
            top_words = [feature_names[i] for i in topic.argsort()[:-n_top_words - 1:-1]]
            topics[topic_idx] = top_words

        logger.info(f"Topic modeling completed with {n_topics} topics.")
        return topics, self.data['topic']

    def plot_sentiment_distribution(self, filename: str = None):
        """
        Generates a bar plot of the sentiment distribution.
        """
        if 'sentiment_label' not in self.data.columns:
            self.analyze_sentiment()

        plt.figure(figsize=(8, 6))
        sns.countplot(x='sentiment_label', data=self.data, palette='viridis', order=['Positive', 'Neutral', 'Negative'])
        plt.title('Sentiment Distribution')
        plt.xlabel('Sentiment')
        plt.ylabel('Number of Posts')

        if filename:
            plt.savefig(filename)
            logger.info(f"Sentiment distribution plot saved to {filename}")
        else:
            plt.show()

    def plot_sentiment_over_time(self, filename: str = None):
        """
        Generates a time-series plot of sentiment scores.
        """
        if 'sentiment_score' not in self.data.columns:
            self.analyze_sentiment()

        df = self.data.set_index(self.timestamp_column)
        plt.figure(figsize=(15, 7))
        df['sentiment_score'].resample('D').mean().plot()
        plt.title('Average Sentiment Over Time')
        plt.xlabel('Date')
        plt.ylabel('Average Sentiment Score')

        if filename:
            plt.savefig(filename)
            logger.info(f"Sentiment over time plot saved to {filename}")
        else:
            plt.show()

    def segment_users(self, n_clusters: int = 4):
        """
        Segments users into clusters based on their posting behavior.
        - Number of posts
        - Average sentiment score
        """
        if 'sentiment_score' not in self.data.columns:
            self.analyze_sentiment()

        user_behavior = self.data.groupby(self.user_column).agg(
            post_count=('sentiment_score', 'count'),
            avg_sentiment=('sentiment_score', 'mean')
        ).reset_index()

        if len(user_behavior) < n_clusters:
            logger.warning(f"Number of users ({len(user_behavior)}) is less than n_clusters ({n_clusters}). Cannot perform clustering.")
            return None

        features = user_behavior[['post_count', 'avg_sentiment']]
        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(features)

        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        user_behavior['cluster'] = kmeans.fit_predict(scaled_features)

        logger.info(f"User segmentation completed with {n_clusters} clusters.")
        return user_behavior

if __name__ == '__main__':
    # --- Демонстрация на Social Behavior Analytics ---
    print("\n" + "="*50)
    print("ДЕМОНСТРАЦИЯ НА АНАЛИЗ НА СОЦИАЛНО ПОВЕДЕНИЕ")
    print("="*50 + "\n")

    # 1. Генериране на симулационни данни
    # Създаваме симулиран набор от данни, сякаш от социална мрежа
    users = ['user_A', 'user_B', 'user_C', 'user_D', 'user_E']
    topics_corpus = {
        'tech': ["The new AI model is incredible!", "I love the latest smartphone features.", "Quantum computing will change everything.", "Software development is a great career."],
        'sports': ["What a game last night!", "The team played with so much heart.", "I can't believe that final score.", "He is the best player in the league."],
        'food': ["This restaurant is amazing, the food is delicious.", "I'm trying a new recipe tonight.", "I dislike bland food.", "Best pizza I have ever had!"]
    }

    data = []
    start_date = pd.to_datetime('2023-01-01')
    for i in range(200):
        user = np.random.choice(users)
        topic_key = np.random.choice(list(topics_corpus.keys()))
        text = np.random.choice(topics_corpus[topic_key])
        if np.random.rand() < 0.1: # Add some random negative sentiment
            text += " But the customer service was terrible."
        timestamp = start_date + pd.to_timedelta(i, unit='h')
        data.append({'timestamp': timestamp, 'user_id': user, 'post_text': text})

    sample_df = pd.DataFrame(data)
    logger.info(f"Генерирани са {len(sample_df)} примерни поста.")
    print("Примерни данни:")
    print(sample_df.head())
    print("\n" + "-"*50 + "\n")

    # 2. Инициализация на аналитичния модул
    try:
        analyzer = SocialBehaviorAnalytics(
            data=sample_df,
            text_column='post_text',
            user_column='user_id',
            timestamp_column='timestamp'
        )
        logger.info("Аналитичният модул е инициализиран успешно.")

        # 3. Анализ на настроенията
        print("Извършване на анализ на настроенията...")
        analyzer.analyze_sentiment()
        print("Топ 5 най-позитивни поста:")
        print(analyzer.data.nlargest(5, 'sentiment_score')[['post_text', 'sentiment_score']])
        print("\nТоп 5 най-негативни поста:")
        print(analyzer.data.nsmallest(5, 'sentiment_score')[['post_text', 'sentiment_score']])
        print("\n" + "-"*50 + "\n")

        # 4. Моделиране на теми
        print("Извършване на моделиране на теми...")
        topics, topic_assignments = analyzer.model_topics(n_topics=3)
        print("Открити теми и техните ключови думи:")
        for topic_id, words in topics.items():
            print(f"  Тема {topic_id}: {', '.join(words)}")
        print("\nРазпределение на постовете по теми:")
        print(analyzer.data['topic'].value_counts())
        print("\n" + "-"*50 + "\n")

        # 5. Сегментиране на потребители
        print("Извършване на сегментиране на потребители...")
        user_segments = analyzer.segment_users(n_clusters=3)
        if user_segments is not None:
            print("Резултати от сегментирането:")
            print(user_segments)
            # Визуализация на клъстерите
            plt.figure(figsize=(10, 7))
            sns.scatterplot(data=user_segments, x='post_count', y='avg_sentiment', hue='cluster', palette='bright', s=100)
            plt.title('Потребителски сегменти')
            plt.xlabel('Брой публикации')
            plt.ylabel('Среден сентимент')
            plt.legend(title='Клъстер')
            plt.savefig("user_segments.png")
            logger.info("Графиката на потребителските сегменти е запазена в user_segments.png")
            plt.close()
        print("\n" + "-"*50 + "\n")

        # 6. Генериране на визуализации
        logger.info("Генериране на обобщени визуализации...")
        analyzer.plot_sentiment_distribution(filename="sentiment_distribution.png")
        analyzer.plot_sentiment_over_time(filename="sentiment_over_time.png")
        logger.info("Визуализациите са запазени като PNG файлове.")

    except (ImportError, ValueError) as e:
        logger.error(f"Грешка по време на демонстрацията: {e}")

    print("\n" + "="*50)
    print("ДЕМОНСТРАЦИЯТА ПРИКЛЮЧИ")
    print("="*50 + "\n")