from fastapi import FastAPI
import pandas as pd
import pickle



# ===== Load Data =====
movies = pd.read_csv("data/ml-latest-small/movies.csv")
ratings = pd.read_csv("data/ml-latest-small/ratings.csv")



app = FastAPI(title="WatchNext AI API")


predicted_df = pickle.load(open("models/predicted_df.pkl", "rb"))
user_movie_matrix = pickle.load(open("models/user_movie_matrix.pkl", "rb"))

# ===== Recommendation Function =====
def recommend_for_user(user_id, n=10):
    if user_id not in user_movie_matrix.index:
        return ["User not found"]

    user_ratings = user_movie_matrix.loc[user_id]
    seen_movies = user_ratings[user_ratings > 0].index

    user_predictions = predicted_df.loc[user_id]
    user_predictions = user_predictions.drop(seen_movies)

    top_movies = user_predictions.sort_values(ascending=False).head(n)

    return movies[movies["movieId"].isin(top_movies.index)]["title"].tolist()


# ===== Routes =====
@app.get("/")
def home():
    return {"message": "WatchNext AI is running"}


@app.get("/recommend/{user_id}")
def get_recommendations(user_id: int):
    return {
        "user_id": user_id,
        "recommendations": recommend_for_user(user_id)
    }

@app.get("/similar/{movie_id}")
def similar_movies(movie_id: int, n: int = 10):
    if movie_id not in user_movie_matrix.columns:
        return {"error": "Movie not found"}

    movie_vector = predicted_df[movie_id]

    similarities = predicted_df.corrwith(movie_vector)

    similar = similarities.sort_values(ascending=False).head(n + 1)

    similar_movies_ids = similar.index[1:]

    return {
        "movie_id": movie_id,
        "similar_movies": movies[movies["movieId"].isin(similar_movies_ids)]["title"].tolist()
    }

@app.get("/movie/{movie_id}")
def get_movie(movie_id: int):
    movie = movies[movies["movieId"] == movie_id]
    
    if movie.empty:
        return {"error": "Movie not found"}
    
    return movie.iloc[0].to_dict()