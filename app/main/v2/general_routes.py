from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app as app
from flask_mail import Message
from werkzeug.utils import secure_filename
import os
from app.models.contact import Contact
from flask_mail import Message
from app import mail
from app.utils.send_notification import send_email
from app import db
from app.models.user import User
from app.models.db_storage import DBStorage
from app.utils.forms import *  # Assuming you have this
from flask_bcrypt import Bcrypt
from flask import current_app
from flask_wtf import FlaskForm
from itsdangerous import URLSafeTimedSerializer

# usecase for when username already exist
general_bp = Blueprint('general_bp', __name__)
storage = DBStorage(db)
bcrypt = Bcrypt()
# Initialize the URLSafeTimedSerializer
def get_serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])


@general_bp.route('/')
def landing_page():
    """Landing page for unauthenticated users"""
    return render_template('/v2/landing.html', title='Lost & Found')


@general_bp.route('/test_mail')
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

@general_bp.route('/upload', methods=['POST'])
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
@general_bp.route('/contacts', methods=['GET'])
def get_contacts():
    contacts = storage.query(Contact)
    contacts_list = [{'id': contact.id, 'name': contact.name, 'created_at': contact.created_at,'updated_at': contact.updated_at,'address': contact.address} for contact in contacts]
    return jsonify(contacts_list)

@general_bp.route('/contacts', methods=['POST'])
def create_contact():
    data = request.get_json()
    new_contact = Contact(name=data['name'], address=data['address'])
    storage.new(new_contact)
    storage.save()
    return jsonify({'message': 'Contact created', 'contact': str(new_contact)}), 201

@general_bp.route('/contacts/<int:id>', methods=['GET'])
def get_contact(id):
    contact = storage.get(Contact, id)
    if contact is None:
        return jsonify({'message': 'Contact not found'}), 404
    return jsonify({'contact': str(contact)})

@general_bp.route('/contacts/<int:id>', methods=['PUT'])
def update_contact(id):
    contact = storage.get(Contact, id)
    if contact is None:
        return jsonify({'message': 'Contact not found'}), 404
    data = request.get_json()
    contact.name = data.get('name', contact.name)
    contact.address = data.get('address', contact.address)
    storage.save()
    return jsonify({'message': 'Contact updated', 'contact': str(contact)})

@general_bp.route('/contacts/<int:id>', methods=['DELETE'])
def delete_contact(id):
    contact = storage.get(Contact, id)
    if contact is None:
        return jsonify({'message': 'Contact not found'}), 404
    storage.delete(contact)
    storage.save()
    return jsonify({'message': 'Contact deleted'})
