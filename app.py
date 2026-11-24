import os
import re
import sqlite3
from contextlib import contextmanager
from flask import Flask, flash, jsonify, redirect, render_template, request, url_for

app = Flask(__name__)
app.config.update(SECRET_KEY=os.environ.get('SECRET_KEY', 'devfolio-demo-key'), DATABASE=os.environ.get('DATABASE', os.path.join(os.path.dirname(__file__), 'devfolio.db')))
THEMES = ('ocean', 'sunset', 'minimal')

@contextmanager
def db():
    connection = sqlite3.connect(app.config['DATABASE'])
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()

def init_db():
    with db() as conn:
        conn.executescript('''
        CREATE TABLE IF NOT EXISTS profiles (id INTEGER PRIMARY KEY, name TEXT NOT NULL, headline TEXT NOT NULL, bio TEXT NOT NULL, email TEXT NOT NULL, github TEXT NOT NULL DEFAULT '', theme TEXT NOT NULL DEFAULT 'ocean');
        CREATE TABLE IF NOT EXISTS projects (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, description TEXT NOT NULL, tech TEXT NOT NULL, link TEXT NOT NULL DEFAULT '');
        CREATE TABLE IF NOT EXISTS skills (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE, category TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, sender TEXT NOT NULL, email TEXT NOT NULL, message TEXT NOT NULL);
        ''')
        conn.execute("INSERT OR IGNORE INTO profiles (id,name,headline,bio,email,github,theme) VALUES (1,'Demo Developer','Full Stack Developer','I build useful web applications.','demo@example.com','','ocean')")

def get_data():
    with db() as conn:
        return (conn.execute('SELECT * FROM profiles WHERE id=1').fetchone(), conn.execute('SELECT * FROM projects ORDER BY id DESC').fetchall(), conn.execute('SELECT * FROM skills ORDER BY category,name').fetchall())

def valid_email(value):
    return bool(re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', value or ''))

def safe_link(value):
    return not value or value.startswith(('https://', 'http://'))

@app.route('/')
def home():
    profile, projects, skills = get_data()
    return render_template('home.html', profile=profile, projects=projects, skills=skills)

@app.route('/editor')
def editor():
    profile, projects, skills = get_data()
    return render_template('editor.html', profile=profile, projects=projects, skills=skills, themes=THEMES)

@app.route('/profile', methods=['POST'])
def update_profile():
    fields = {key: request.form.get(key, '').strip() for key in ('name','headline','bio','email','github','theme')}
    if not all(fields[key] for key in ('name','headline','bio','email')) or not valid_email(fields['email']) or fields['theme'] not in THEMES or not safe_link(fields['github']):
        flash('Invalid profile details.', 'error')
        return redirect(url_for('editor'))
    with db() as conn:
        conn.execute('UPDATE profiles SET name=?,headline=?,bio=?,email=?,github=?,theme=? WHERE id=1', tuple(fields[key] for key in ('name','headline','bio','email','github','theme')))
    flash('Profile saved successfully.', 'success')
    return redirect(url_for('editor'))

@app.route('/projects/add', methods=['POST'])
def add_project():
    fields = {key: request.form.get(key, '').strip() for key in ('title','description','tech','link')}
    if not all(fields[key] for key in ('title','description','tech')) or not safe_link(fields['link']):
        flash('Invalid project details.', 'error')
        return redirect(url_for('editor'))
    with db() as conn:
        conn.execute('INSERT INTO projects (title,description,tech,link) VALUES (?,?,?,?)', tuple(fields.values()))
    flash('Project added successfully.', 'success')
    return redirect(url_for('editor'))

@app.route('/projects/<int:project_id>/delete', methods=['POST'])
def delete_project(project_id):
    with db() as conn:
        cursor = conn.execute('DELETE FROM projects WHERE id=?', (project_id,))
    flash('Project deleted.' if cursor.rowcount else 'Project not found.', 'success' if cursor.rowcount else 'error')
    return redirect(url_for('editor'))

@app.route('/skills/add', methods=['POST'])
def add_skill():
    name = request.form.get('name', '').strip()
    category = request.form.get('category', '').strip()
    if not name or category not in ('Frontend','Backend','Database','Tools','Other'):
        flash('Invalid skill details.', 'error')
        return redirect(url_for('editor'))
    try:
        with db() as conn:
            conn.execute('INSERT INTO skills (name,category) VALUES (?,?)', (name,category))
    except sqlite3.IntegrityError:
        flash('Skill already exists.', 'error')
    else:
        flash('Skill added successfully.', 'success')
    return redirect(url_for('editor'))

@app.route('/skills/<int:skill_id>/delete', methods=['POST'])
def delete_skill(skill_id):
    with db() as conn:
        cursor = conn.execute('DELETE FROM skills WHERE id=?', (skill_id,))
    flash('Skill deleted.' if cursor.rowcount else 'Skill not found.', 'success' if cursor.rowcount else 'error')
    return redirect(url_for('editor'))

@app.route('/portfolio')
def portfolio():
    profile, projects, skills = get_data()
    return render_template('portfolio.html', profile=profile, projects=projects, skills=skills)

@app.route('/contact', methods=['POST'])
def contact():
    sender = request.form.get('sender','').strip()
    email = request.form.get('email','').strip()
    message = request.form.get('message','').strip()
    if not sender or not valid_email(email) or not message:
        flash('Invalid contact message.', 'error')
        return redirect(url_for('portfolio'))
    with db() as conn:
        conn.execute('INSERT INTO messages (sender,email,message) VALUES (?,?,?)', (sender,email,message))
    flash('Message received (stored locally; no email sent).', 'success')
    return redirect(url_for('portfolio'))

@app.route('/dashboard')
def dashboard():
    with db() as conn:
        counts = {table: conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0] for table in ('projects','skills','messages')}
        messages = conn.execute('SELECT * FROM messages ORDER BY id DESC LIMIT 10').fetchall()
    return render_template('dashboard.html', counts=counts, messages=messages)

@app.route('/api/health')
def health():
    with db() as conn:
        conn.execute('SELECT 1')
    return jsonify(status='ok', service='DevFolio')

@app.route('/api/metrics')
def metrics():
    with db() as conn:
        return jsonify({table: conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0] for table in ('projects','skills','messages')})

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
