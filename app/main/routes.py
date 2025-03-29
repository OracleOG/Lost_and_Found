from flask import render_template,Blueprint, request, jsonify, abort, current_app as app
from app import db
from app.models.item import Item
from ..models.contact import Contact
from ..models.user import User
from ..models.db_storage import DBStorage, db
from flask import request, redirect, url_for, render_template, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from flask_mail import Message
from app import mail
from ..utils.send_notification import send_email 
from ..utils.forms import *

main = Blueprint('main', __name__)
storage = DBStorage(db)
@main.route('/')
def home():
    return render_template('index.html')


@main.route('/index')
def index():
    return render_template('indexx.html')

@main.route('/landing')
def landing_page():
    return render_template('landing.html', title='Landing_page')

@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            flash('You have been logged in!', 'success')
            login_user(user, remember=form.remember.data)
            return redirect(url_for('main.index'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html', title='Log In', form=form)

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You've Logged OUT successfully", 'success')
    return redirect(url_for('main.login'))


@main.route('/test_mail')
def send_test_email():
    send_email('Test Subject', 'marwaasabon@gmail.com', 'This is a test email body.', '<h1>This is a test email body in HTML</h1>')
    #this is for testing the email
    try:
        msg = Message(
            subject="Test Email",
            recipients=[app.config['MAIL_USERNAME']],
            body="This is a test email sent from Flask using Gmail."
        )
        mail.send(msg)
        return jsonify({'message': 'Test email sent successfully!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
from flask import flash

@main.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Assuming you have an item instance ready to add an image to
        item = Item(name="Example Item", image_url=filepath)
        db.session.add(item)
        db.session.commit()
        
        return redirect(url_for('uploaded_file', filename=filename))
@main.route('/contacts', methods=['GET'])
def get_contacts():
    contacts = storage.query(Contact)
    contacts_list = [{'id': contact.id, 'name': contact.name, 'created_at': contact.created_at,'updated_at': contact.updated_at,'address': contact.address} for contact in contacts]
    return jsonify(contacts_list)

@main.route('/contacts', methods=['POST'])
def create_contact():
    data = request.get_json()
    new_contact = Contact(name=data['name'], address=data['address'])
    storage.new(new_contact)
    storage.save()
    return jsonify({'message': 'Contact created', 'contact': str(new_contact)}), 201

@main.route('/contacts/<int:id>', methods=['GET'])
def get_contact(id):
    contact = storage.get(Contact, id)
    if contact is None:
        return jsonify({'message': 'Contact not found'}), 404
    return jsonify({'contact': str(contact)})

@main.route('/contacts/<int:id>', methods=['PUT'])
def update_contact(id):
    contact = storage.get(Contact, id)
    if contact is None:
        return jsonify({'message': 'Contact not found'}), 404
    data = request.get_json()
    contact.name = data.get('name', contact.name)
    contact.address = data.get('address', contact.address)
    storage.save()
    return jsonify({'message': 'Contact updated', 'contact': str(contact)})

@main.route('/contacts/<int:id>', methods=['DELETE'])
def delete_contact(id):
    contact = storage.get(Contact, id)
    if contact is None:
        return jsonify({'message': 'Contact not found'}), 404
    storage.delete(contact)
    storage.save()
    return jsonify({'message': 'Contact deleted'})
