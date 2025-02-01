from flask import Flask, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import FloatField, TextAreaField, SubmitField, StringField
from wtforms.validators import DataRequired, NumberRange
from flask_bootstrap import Bootstrap
from flask_migrate import Migrate
import requests

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:kali1@localhost/testdb'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize Bootstrap and SQLAlchemy
Bootstrap(app)
db = SQLAlchemy(app)

# Initialize Flask-Migrate
migrate = Migrate(app, db)

# CREATE TABLE
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.Text, nullable=True)
    img_url = db.Column(db.String(500), nullable=False)

# Movie Rating Form
class RateMovieForm(FlaskForm):
    rating = FloatField('Rating', validators=[DataRequired(), NumberRange(min=0, max=10)])
    review = TextAreaField('Review', validators=[DataRequired()])
    submit = SubmitField('Submit')

# Function to add a movie if not already in the database
def add_movie_if_not_exists(title, year, description, rating, ranking, review, img_url):
    existing_movie = Movie.query.filter_by(title=title).first()
    if not existing_movie:
        new_movie = Movie(
            title=title,
            year=year,
            description=description,
            rating=rating,
            ranking=ranking,
            review=review,
            img_url=img_url
        )
        db.session.add(new_movie)
        db.session.commit()

# Initialize DB and add movies if not exist
with app.app_context():
    db.create_all()

    # Add movies only if they do not exist in the database
    add_movie_if_not_exists(
        title="Phone Booth",
        year=2002,
        description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
        rating=7.3,
        ranking=10,
        review="My favourite character was the caller",
        img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
    )
    
    add_movie_if_not_exists(
        title="Avatar The Way of Water",
        year=2022,
        description="Set more than a decade after the events of the first film, learn the story of the Sully family (Jake, Neytiri, and their kids), the trouble that follows them, the lengths they go to keep each other safe, the battles they fight to stay alive, and the tragedies they endure.",
        rating=7.3,
        ranking=9,
        review="I liked the water.",
        img_url="https://image.tmdb.org/t/p/w500/t6HIqrRAclMCA60NsSmeqe9RmNV.jpg"
    )

API_KEY = '878bc8198645dbdd07fdad84e816f03d'  # Replace with your actual API key

@app.route("/select_movie/<title>", methods=["GET", "POST"])
def select_movie(title):
    # Make a request to the Movie Database API to search for movies by title
    url = f"https://api.themoviedb.org/3/search/movie?api_key={API_KEY}&query={title}"
    response = requests.get(url)
    data = response.json()

    # Get the list of movies matching the title
    movies = data['results']
    
    # Render the select page with the movies list
    return render_template("select_movie.html", movies=movies)

@app.route("/movie_details/<int:movie_id>", methods=["GET"])
def movie_details(movie_id):
    # Fetch movie details from The Movie Database API
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={API_KEY}"
    response = requests.get(url)
    movie_data = response.json()

    # Extract relevant data
    title = movie_data['title']
    img_url = f"https://image.tmdb.org/t/p/w500/{movie_data['poster_path']}"
    year = movie_data['release_date'][:4]
    description = movie_data['overview']

    # Add the movie to the database
    new_movie = Movie(
        title=title,
        img_url=img_url,
        year=year,
        description=description,
        rating=None,
        ranking=None,
        review=None
    )
    db.session.add(new_movie)
    db.session.commit()

    # Redirect to the edit page for the user to add rating and review
    return redirect(url_for('edit_movie', movie_id=new_movie.id))

@app.route("/edit_movie/<int:movie_id>", methods=["GET", "POST"])
def edit_movie(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    form = RateMovieForm()
    if form.validate_on_submit():
        # Update the movie with the new rating and review
        movie.rating = form.rating.data
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    
    # Prefill the form with current movie data
    form.rating.data = movie.rating
    form.review.data = movie.review
    return render_template('edit.html', form=form, movie=movie)

@app.route("/delete_movie/<int:movie_id>", methods=["POST"])
def delete_movie(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for('home'))

class AddMovieForm(FlaskForm):
    title = StringField('Movie Title', validators=[DataRequired()])
    submit = SubmitField('Add Movie')

@app.route("/add_movie", methods=['POST', 'GET'])
def add_movie():
    form = AddMovieForm()
    if form.validate_on_submit():
        movie_title = form.title.data
        return redirect(url_for('select_movie', title=movie_title))
    return render_template('add_movie.html', form=form)

@app.route("/")
def home():
    movies = Movie.query.order_by(Movie.rating.desc()).all()

    # Assign ranking dynamically
    for index, movie in enumerate(movies, start=1):
        movie.ranking = index  

    db.session.commit()  # Save rankings

    return render_template("index.html", movies=movies)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
