import os
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import pandas as pd
import html
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


import requests
from bs4 import BeautifulSoup
app = Flask(__name__)
CORS(app)


csv_file_path = 'data/semicleanedbg.csv'
data_df = pd.read_csv(csv_file_path)

# for cosine sim
data_df['processed_description'] = data_df['description'].apply(lambda x: x.lower() if isinstance(x, str) else '')
tfidf_vectorizer = TfidfVectorizer()
tfidf_matrix = tfidf_vectorizer.fit_transform(data_df['processed_description'].values.astype('U'))  # 'U' for Unicode



@app.route("/")
def home():
    return render_template('base.html', title="sample html")

#for the suggestions box pls do not touch; it checks all the games for games with the query in it (not accounting for typos)
# this then returns the top 5 matching titles
@app.route("/suggestions")
def suggestions():
    query_partial = request.args.get("query", "")
    if not query_partial:
        return jsonify([])
    matching_games = data_df[data_df['name'].str.contains(query_partial, case = False)]['name'].unique().tolist()
    suggestions = matching_games[:5]
    return jsonify(suggestions)


@app.route("/games")
def search():
    text = request.args.get("title")
    min_age = request.args.get("min_age", type=int)
    min_players = request.args.get("min_players", type=int)
    max_players = request.args.get("max_players", type=int)
    category = request.args.get("category")
    mode = request.args.get("mode")

    if mode == 'recommendation':
        matches = recommendation_search(text)
    else:
        matches = matches = data_df[data_df['name'].str.lower().str.contains(text.lower())]

    if min_age is not None:
        matches = matches[matches['minage'] >= min_age]
    if min_players is not None:
        matches = matches[matches['minplayers'] >= min_players]
    if max_players is not None:
        matches = matches[matches['maxplayers'] <= max_players]
    if category:
        matches = matches[matches['boardgamecategory'].str.contains(category, case=False, na=False)]
    matches_filtered = matches[['name', 'description', 'average', 'objectid', 'minage', 'minplayers', 'maxplayers', 'boardgamecategory']]
    matches_filtered['name'] = matches_filtered['name'].apply(html.unescape)
    matches_filtered['description'] = matches_filtered['description'].apply(html.unescape)
    matches_filtered_json = matches_filtered.to_json(orient='records')

    return matches_filtered_json

def recommendation_search(query):
    if query:
        #some preprocessing: 1- fetch the game 2- get its processed desc
        game_row = data_df[data_df['name'].str.lower() == query.lower()].iloc[0]
        game_description = game_row['processed_description']
        #cos sim
        query_vector = tfidf_vectorizer.transform([game_description])
        cosine_similarities = cosine_similarity(query_vector, tfidf_matrix).flatten()
        #get the top 1000       
        similar_indices = cosine_similarities.argsort()[-(1000+1):][::-1]
    # game itself is the most similar one, so we exclude it if so.
    similar_indices = similar_indices[1:]

    # Fetch the details of the top N similar games then return
    similar_games = data_df.iloc[similar_indices]
    return similar_games
    

@app.route("/about/<game_id>")
def about(game_id):
    game_id = int(game_id)
    game_details_query = data_df[data_df['objectid'] == game_id]
    if not game_details_query.empty:
        game_details = game_details_query.iloc[0].to_dict()
        # game_img = fetch_game_link(game_details_query["gamelink"])
        game_img = fetch_game_link(game_details_query.reset_index(drop=True).at[0, "gamelink"])
        game_details["img"] = game_img
        game_reviews = fetch_game_reviews(game_details_query.reset_index(drop=True).at[0, "gamelink"])
        game_details["reviews"] = game_reviews
        return render_template('about.html', game=game_details)
    else:
        return "Game not found", 404
    
def fetch_game_link(game_link):
    # game_link = game_link[game_link.index("/"):]
    game_url = f"https://boardgamegeek.com{game_link}"
    response = requests.get(game_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        # img_tag = soup.find('meta', attrs={"property": "og:image", })
        link_tags = soup.find_all('link', attrs={"rel": "preload", "as": "image"})
        if len(link_tags) > 1:
            return link_tags[1]['href']
        else:
            return link_tags[0]['href']
    else:
        return f"Cannot find image"
    
def fetch_game_reviews(game_link):
    game_url = f"https://boardgamegeek.com{game_link}/ratings"
    print("Fetching reviews from:", game_url)
    response = requests.get(game_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        review_list_items = soup.find_all('li', class_="summary-item summary-rating-item ng-scope")
        reviews = []
        for item in review_list_items:
            expandable_div = item.find('div', class_="expandable-body")
            if expandable_div:
                review_span = expandable_div.find('span', {"ng-bind-html": "::item.textfield.comment.rendered|to_trusted", "class": "ng-binding ng-scope"})
                if review_span:
                    review_text = review_span.get_text(strip=True)
                    reviews.append(review_text)
        print(f"Found {len(reviews)} reviews.")
        return reviews
    else:
        print("Failed to fetch reviews.")
        return []
    
if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
