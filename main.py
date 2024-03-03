# This is a sample Python script.
import os
import openai
from flask_mongoengine import MongoEngine
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired
from flask import session, flash
from flask import Flask, render_template, redirect, url_for, request
from flask_wtf import FlaskForm
from werkzeug.utils import secure_filename
from wtforms import SubmitField, MultipleFileField, TextAreaField
from wtforms.validators import InputRequired
from PyPDF2 import PdfReader
from mongoengine import *
from openai import ChatCompletion
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from mongoengine import Document, StringField
import re
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
from database.db import initialize_db, db
from database.models import LoginForm
from database.models import User

app = Flask(__name__)

app.config['SECRET_KEY'] = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = 'static/files'
app.config['MONGODB_SETTINGS'] = {
    'db': 'DatabaseName',
    'host': '127.0.0.1',
    'port': 27017  # Port par défaut de MongoDB
}



initialize_db(app)
# Configuration du clé API OpenAI
openai.api_key = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'




class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField("Login")


@app.route('/login', methods=['POST', 'GET'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        user = User.objects(email=email).first()

        if user and user.password == password:
            flash('You are successfully logged in', 'success')
            return redirect('/home')
        else:
            flash('Incorrect email or password', 'danger')
    # Si la méthode de requête n'est pas POST ou si la validation échoue, affichez simplement le formulaire de connexion
    return render_template('login.html', form=form, title='Login')




def extract_text_from_pdf(pdf_path):
    text = ""
    with open(pdf_path, 'rb') as file:
        reader = PdfReader(file)
        for page in reader.pages:
            text += page.extract_text()
    return text


class UploadFileForm(FlaskForm):
    file = MultipleFileField("File", validators=[InputRequired()])
    job_description = TextAreaField("Paste Job Description:", validators=[InputRequired()])
    submit = SubmitField("Upload File")


def fit_percentage(resume_text, job_description):

    vectorizer = CountVectorizer()

    vectorized_documents = vectorizer.fit_transform([resume_text, job_description])

    resume_vector = vectorized_documents[0]
    job_vector = vectorized_documents[1]

    cosine_sim = cosine_similarity(resume_vector, job_vector)

    fit_percentage = cosine_sim[0][0] * 100

    return fit_percentage


@app.route('/results', methods=['GET'])
def display_results():
    # Récupérer les résultats depuis la session Flask
    results = session.get('results', [])
    return render_template('results.html', results=results)

def extract_candidate_name(cv_text):
    lines = cv_text.split('\n')
    candidate_name = lines[0].strip()
    return candidate_name



@app.route('/', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
def home():
    form = UploadFileForm()
    if form.validate_on_submit():

        results = []
        for uploaded_file in form.file.data:
            filename = secure_filename(uploaded_file.filename)
            uploaded_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            # Analyser le CV avec l'API OpenAI
            cv_text = extract_text_from_pdf(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            job_description = form.job_description.data
            # Concaténer le contenu du CV et de la description du poste
            combined_text = cv_text + "\n" + job_description

            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "you are a helpful assistant that your role match between resume and job description and you can give the pourcent of similarity "},
                    {"role": "user", "content": combined_text},
                ],
            )

            # Concaténer le contenu de toutes les réponses
            analysis_result = ""
            for choice in response.choices:
                analysis_result += choice.message.content + " "



            candidate_name = extract_candidate_name(cv_text)
            print(candidate_name)

            similarity_percentage = fit_percentage(cv_text, job_description)
            print("Pourcentage de correspondance :", similarity_percentage)


            results.append({
                'candidate_name': candidate_name,
                'filename': filename,
                'similarity_percentage': similarity_percentage,
                'analysis_result': analysis_result
            })


        session['results'] = results


        return redirect(url_for('display_results'))

    return render_template('index.html', form=form)


if __name__ == '__main__':

    app.run(debug=True)
