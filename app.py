# app.py
from flask import Flask, render_template, request
import pandas as pd
import numpy as np
import pickle
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

# Load data
books = pd.read_csv("data\Books.csv")
ratings = pd.read_csv("data\Ratings.csv")
users = pd.read_csv("data\\Users.csv")

# Preprocess Top 50 Books
ratings_with_name = ratings.merge(books, on='ISBN')
rating_df = ratings_with_name.groupby('Book-Title')['Book-Rating'].count().reset_index()
rating_df.rename(columns={'Book-Rating':'num_rating'}, inplace=True)
avg_rating_df = ratings_with_name.groupby('Book-Title')['Book-Rating'].mean().reset_index()
avg_rating_df.rename(columns={'Book-Rating':'avg_rating'}, inplace=True)
popular_df = rating_df.merge(avg_rating_df, on='Book-Title')
popular_df = popular_df[popular_df['num_rating'] >= 250].sort_values('avg_rating', ascending=False).head(50)
top_50_df = popular_df.merge(books, on='Book-Title').drop_duplicates('Book-Title')[
    ['Book-Title', 'Book-Author', 'Publisher', 'Image-URL-M', 'num_rating', 'avg_rating']
]

# Recommendation logic
x = ratings_with_name.groupby('User-ID')['Book-Rating'].count() > 200
actual_raters = x[x].index
filtered_raters = ratings_with_name[ratings_with_name['User-ID'].isin(actual_raters)]
y = filtered_raters.groupby('Book-Title')['Book-Rating'].count() >= 50
famous_books = y[y].index
final_ratings = filtered_raters[filtered_raters['Book-Title'].isin(famous_books)]
pt = final_ratings.pivot_table(index='Book-Title', columns='User-ID', values='Book-Rating').fillna(0)
similarity = cosine_similarity(pt)

# Recommendation function
def recommend(book):
    index = np.where(pt.index == book)[0][0]
    similar_items = sorted(list(enumerate(similarity[index])), key=lambda x: x[1], reverse=True)[1:6]
    data = []
    for i in similar_items:
        item = books[books['Book-Title'] == pt.index[i[0]]].drop_duplicates('Book-Title')[
            ['Book-Title', 'Book-Author', 'Image-URL-M']
        ].values[0]
        data.append(item)
    return data

@app.route('/recommend', methods=['POST'])
def rec():
    user_input = request.form.get('book_name')
    try:
        data = recommend(user_input)
        return render_template('recommend.html', data=data, book=user_input)
    except:
        return render_template('recommend.html', error='Book not found or insufficient data.', book=user_input)

@app.route('/')
def home():
    return render_template('home.html', books=top_50_df.values)

# @app.route('/recommend', methods=['GET', 'POST'])
# def rec():
#     if request.method == 'POST':
#         user_input = request.form.get('book_name')
#         try:
#             data = recommend(user_input)
#             return render_template('recommend.html', data=data, book=user_input)
#         except:
#             return render_template('recommend.html', error='Book not found or insufficient data.', book=user_input)
#     return render_template('recommend.html')

if __name__ == '__main__':
    app.run(debug=True)
