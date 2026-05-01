import pandas as pd
from sklearn.decomposition import TruncatedSVD
import pickle



# ===== Load Data =====
movies = pd.read_csv("data/ml-latest-small/movies.csv")
ratings = pd.read_csv("data/ml-latest-small/ratings.csv")

# ===== Build Matrix =====
user_movie_matrix = ratings.pivot_table(
    index="userId",
    columns="movieId",
    values="rating"
).fillna(0)

# ===== Train Model =====
svd = TruncatedSVD(n_components=50, random_state=42)
matrix_reduced = svd.fit_transform(user_movie_matrix)

predicted_matrix = svd.inverse_transform(matrix_reduced)

predicted_df = pd.DataFrame(
    predicted_matrix,
    index=user_movie_matrix.index,
    columns=user_movie_matrix.columns
)

pickle.dump(predicted_df, open("models/predicted_df.pkl", "wb"))
pickle.dump(user_movie_matrix, open("models/user_movie_matrix.pkl", "wb"))