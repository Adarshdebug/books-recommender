from flask import Flask, render_template, request
import pickle
import numpy as np
import re

# ---------------- LOAD DATA ----------------
popular_df = pickle.load(open('popular.pkl', 'rb'))
pt = pickle.load(open('pt.pkl', 'rb'))
books = pickle.load(open('books.pkl', 'rb'))
similarity_scores = pickle.load(open('similarity_scores.pkl', 'rb'))

# ---------------- INIT APP ----------------
app = Flask(__name__)

# ---------------- HELPER FUNCTION ----------------
def clean_text(text):
    """Lowercase, strip spaces, remove special characters for robust matching"""
    return re.sub(r'[^a-z0-9 ]', '', text.lower().strip())

# ---------------- CREATE BOOK LOOKUP ----------------
book_info = {}
for _, row in books.iterrows():
    book_info[row['Book-Title']] = {
        'author': row['Book-Author'],
        'image': row['Image-URL-M'],
        'rating': row.get('avg_rating', 'N/A'),
        'votes': row.get('num_ratings', 0)
    }

# ---------------- HOME PAGE ----------------
@app.route('/')
def index():
    return render_template(
        'index.html',
        book_name=list(popular_df['Book-Title'].values),
        author=list(popular_df['Book-Author'].values),
        image=list(popular_df['Image-URL-M'].values),
        votes=list(popular_df['num_ratings'].values),
        rating=list(popular_df['avg_rating'].values)
    )

# ---------------- RECOMMEND PAGE ----------------
@app.route('/recommend')
def recommend_ui():
    return render_template('recommend.html')

# ---------------- RECOMMEND BOOKS FUNCTION ----------------
@app.route('/recommend_books', methods=['POST'])
def recommend():
    user_input = request.form.get('user_input')
    if not user_input:
        return render_template('recommend.html', message="❌ Please enter a book name.")

    # Clean user input
    user_input_clean = clean_text(user_input)

    # Clean pivot table index
    pt_index_clean = pt.index.to_series().apply(clean_text)

    # Find matches
    matches = np.where(pt_index_clean == user_input_clean)[0]

    if len(matches) == 0:
        return render_template('recommend.html', message="❌ Book not found. Please try another title.")

    index = matches[0]

    # Get top 4 similar books
    similar_items = sorted(
        list(enumerate(similarity_scores[index])),
        key=lambda x: x[1],
        reverse=True
    )[1:5]

    # Prepare data for rendering
    data = []
    for i in similar_items:
        title = pt.index[i[0]]
        info = book_info.get(title)
        if info:
            data.append([title, info['author'], info['image'], info['rating'], info['votes']])

    return render_template('recommend.html', data=data)

# ---------------- RUN APP ----------------
if __name__ == '__main__':
    app.run(debug=True)
