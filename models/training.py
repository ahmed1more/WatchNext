import os
import pandas as pd
from sklearn.decomposition import TruncatedSVD
import pickle



# ===== Load Data =====
movies = pd.read_csv("data/ml-latest-small/movies.csv")
ratings = pd.read_csv("data/ml-latest-small/ratings.csv")

# ===== Convert to Pickle =====
def convert_to_pickle(df: pd.DataFrame, name: str):
    # Save to models directory
    pickle_path = f"models/{name}.pkl"
    with open(pickle_path, "wb") as f:
        pickle.dump(df, f)
    
    print(f"Successfully saved {name} to {pickle_path}")

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

if __name__ == "__main__":
    convert_to_pickle(movies, "movies")
    convert_to_pickle(ratings, "ratings")
    pickle.dump(predicted_df, open("models/predicted_df.pkl", "wb"))
    pickle.dump(user_movie_matrix, open("models/user_movie_matrix.pkl", "wb"))