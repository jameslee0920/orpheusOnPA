"""Get recommendations for a Spotify user"""
import os
import pickle
import numpy as np
import pandas as pd
from sklearn import preprocessing
import spotipy

spotify = spotipy.Spotify()
def spotify_ids_to_str(spotify_ids):
    def to_str(item):
        if not item:
            return "NA"
        return item['artists'][0]['name'] + " - " + item['name']
    return [to_str(item) for item in spotify.tracks(spotify_ids)['tracks']]

PATH_TO_DATA = '/home/3rdworldjuander/mysite/processed_data/'

class Recommender(object):
    """Music recommender using collaborative filtering"""

    # Model parameters
    RANK = 50
    LAMBDA = 1.0
    ALPHA = 40.0

    def __init__(self):
        """Load model data"""

        self.product_features = self.load_product_features()
        self.product_features_mapping = [feature[0] for feature in self.product_features]
        self.Y = self.build_item_matrix(self.product_features)

    def get_recommendations(self, user_ratings):
        """
        Given a dict of user ratings, return products and user confidence.
        :param user_ratings: dict of (song_id, rating) pairs
        :return: list of (implicit) rating product pairs ordered by ratings
        """

        # Get user latent features
        x_u = self.get_latent_user_features(user_ratings)

        # Compute implicit ratings using product factor matrix and user's latent features
        predicted_ratings = np.dot(self.Y, x_u)
        predicted_products = zip(np.array(predicted_ratings).reshape(-1, ),
                                 self.product_features_mapping)
        predicted_products = sorted(predicted_products, key=lambda x: x[0], reverse=True)

        return predicted_products

    def load_product_features(self):
        """Load the model's latent product matrix"""

        path_to_product_features = os.path.join(PATH_TO_DATA, 'product_features.p')
        product_features = pickle.load(open(path_to_product_features, 'rb'))
        return product_features

    def build_item_matrix(self, product_features):
        """Build the item matrix from the product features"""

        # Consolidate features into the matrix Y
        Y = np.matrix([feature[1] for feature in product_features])
        return Y

    def get_latent_user_features(self, user_ratings):
        """Build the normal equations matrix"""

        Y = self.Y
        r_u = np.zeros((Y.shape[0], 1))
        p_u = np.zeros((Y.shape[0], 1))
        c_u = np.ones((Y.shape[0], 1))

        user_products = user_ratings.keys()

        Y_t = Y.transpose()

        for i, product in enumerate(self.product_features_mapping):
            if product in user_products:
                p_u[i] = 1.0
                r_u[i] = user_ratings[product]
                c1 = self.ALPHA * np.abs(r_u[i])
                c_u[i] = (1.0 + c1)

        d_u = np.multiply(c_u, p_u)

        # A = Y^T * C_u * Y + lambda * I
        A = np.dot(Y_t, np.multiply(c_u, Y)) + len(user_ratings) * self.LAMBDA * np.eye(Y.shape[1])

        # b = Y^T d_u
        b = np.dot(Y_t, d_u)

        # Solve Ax = b to get latent user features
        x_u = np.linalg.solve(A, b)

        return x_u

class Mapper(object):
    """Mapper for different song ids"""

    def __init__(self):
        """Load the mappings"""

        path_to_mappings = os.path.join(PATH_TO_DATA, 'song_mappings.csv')
        self.mappings = pd.read_csv(path_to_mappings, names=['msd_id', 'spotify_id', 'model_id'])

    def model_to_spotify(self, model_ids, how='inner'):
        """Map model ids to Spotify ids"""

        df = pd.DataFrame(model_ids, columns=['model_id'])

        return df.merge(self.mappings, on='model_id', how=how)['spotify_id']

    def spotify_to_model(self, spotify_ids, how='inner'):
        """Map spotify ids to model ids"""

        df = pd.DataFrame(spotify_ids, columns=['spotify_id'])

        #print df.merge(self.mappings, on='spotify_id', how=how)

        return df.merge(self.mappings, on='spotify_id', how=how)['model_id']

    def merge_spotify(self, df, model_column_name, how='inner'):
        """Merge df with model ids spotify ids"""

        merged = df.merge(self.mappings, left_on=model_column_name, right_on='model_id', how=how)
        merged.drop(['msd_id', 'model_id'], 1, inplace=True)
        return merged

class User(object):
    """A Spotify User"""

    def __init__(self, name, spotify_ids):
        """
        :param spotify_ids: list of spotify track ids
        """
        self.name = name
        self.spotify_ids = spotify_ids

def normalize(df):
    result = df.copy()
    for feature_name in df.columns:
        max_value = df[feature_name].max()
        min_value = df[feature_name].min()
        result[feature_name] = (df[feature_name] - min_value) / (max_value - min_value)
    return result

class Orpheus(object):
    """Multi-user Music Recommendation System"""

    def __init__(self, users):
        """
        :param users: A list of users
        """

        self.users = users
        self.model = Recommender()
        self.mapper = Mapper()

    def get_playlist(self, agg_strategy='avg', num_tracks=10):
        """
        Create the playlist using the given aggregation strategy on the user's
        individual recommendations.
        :param agg_strategy: function defining the type of aggregation to perform
        :return: list of Spotify ids
        """

        if agg_strategy == 'avg':
            strat_func = self.avg_strategy
        else:
            strat_func = self.avg_strategy

        # Get recommendations for each user
        recs_by_user = {}
        for user in self.users:
            print 'SPOTIFY IDS:'
            print user.spotify_ids
            song_ids = self.mapper.spotify_to_model(user.spotify_ids)
            print 'SONG IDS:'
            print song_ids
            user_ratings = {s: 1000.0 for s in song_ids}
            recs_by_user[user.name] = self.model.get_recommendations(user_ratings)

        # Apply the aggregation strategy
        agg_recs = strat_func(recs_by_user)

        # Add Spotify mappings
        agg_recs_spotify = self.mapper.merge_spotify(agg_recs.reset_index(), 'index')
        agg_recs_spotify = agg_recs_spotify[:num_tracks]
        agg_recs_spotify['track'] = spotify_ids_to_str(agg_recs_spotify['spotify_id'])

        print agg_recs_spotify

        return agg_recs_spotify

    def avg_strategy(self, recs_by_user):
        """
        Perform the averaging strategy for a group of user's recommendations.
        :param recs_by_user: dictionary of (user, recommendations) pairs
        :return: data frame of songs ordered by aggregated rating
        """

        # Create dataframe storing all user's ratings
        song_ids = sorted(self.model.product_features_mapping)
        user_ratings = pd.DataFrame(index=song_ids, columns=recs_by_user.keys())

        for user, recs in recs_by_user.iteritems():
            ratings_and_score = sorted(recs, key=lambda x: x[1])
            ratings = [rec[0] for rec in ratings_and_score]

            user_ratings[user] = ratings

        # Normalize ratings
        user_ratings = normalize(user_ratings)

        # Calculate the mean ratings of each song
        user_ratings['avg'] = user_ratings.mean(1)

        return user_ratings.sort_values(by='avg', ascending=False)
