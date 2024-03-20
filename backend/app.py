import os
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import pandas as pd
import html
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)
CORS(app)


csv_file_path = 'data/semicleanedbg.csv'
data_df = pd.read_csv(csv_file_path)

# Vectorize the descriptions
vectorizer = TfidfVectorizer(stop_words='english')
tfidf_matrix = vectorizer.fit_transform(data_df['description'])


def csv_search(query, min_age, min_players, max_players, category):

    if query:
        query_vector = vectorizer.transform([query])
        cosine_similarities = cosine_similarity(query_vector, tfidf_matrix).flatten()
        # Get indices of the games with the highest similarity scores
        similar_indices = cosine_similarities.argsort()[:-11:-1]  # Top 10 results
        matches = data_df.iloc[similar_indices]
    else:
        matches = data_df
    if min_age is not None:
        matches = matches[matches['minage'] >= min_age]
    if min_players is not None:
        matches = matches[matches['minplayers'] >= min_players]
    if max_players is not None:
        matches = matches[matches['maxplayers'] <= max_players]
    if category:
        matches = matches[matches['boardgamecategory'].str.contains(category, case=False, na=False)]

    # Return only the relevant columns
    return matches[['name', 'description', 'average']].to_json(orient='records')

@app.route("/")
def home():
    return render_template('base.html', title="sample html")

@app.route("/games")
def episodes_search():
    text = request.args.get("title")
    min_age = request.args.get("min_age", type=int)
    min_players = request.args.get("min_players", type=int)
    max_players = request.args.get("max_players", type=int)
    category = request.args.get("category")
    results = csv_search(text, min_age, min_players, max_players, category)
    return jsonify(results)

@app.route("/about/<game_id>")
def about(game_id):
    game_id = int(game_id)
    game_details_query = data_df[data_df['objectid'] == game_id]
    if not game_details_query.empty:
        game_details = game_details_query.iloc[0].to_dict()
        return render_template('about.html', game=game_details)
    else:
        return "Game not found", 404

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
