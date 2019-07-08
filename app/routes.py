from app import app
from flask import render_template

@app.route('/')
@app.route('/index')
def index():
    user = {'username': 'Tony'}
    posts = [
            {'author': {'username': 'John'},
                'body': "123"}, 
            {'author': {'username': 'Neil'}, 
                'body': "456"}
            ]
    return render_template('index.html', title='Home', user=user, posts = posts)
