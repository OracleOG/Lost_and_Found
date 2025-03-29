import requests
from flask_mail import Mail, Message
from flask import Flask 
from flask import current_app as app
from flask_mail import Message
from app import mail
from ..config import Config  # Import the Config class


def notify_user_and_initiate_quality_check(match):
    # Send notification to the potential owner
    user = User.query.get(match.potential_owner_user_id)
    send_notification(user.email, "Potential match found for your claim")

    # Initiate a quality check
    new_quality_check = QualityCheck(match_id=match.id, confirmed_owner_user_id=None)  # Owner to be confirmed
    db.session.add(new_quality_check)
    db.session.commit()
  
 
 # this is to unify the sending mails 
def send_email(subject, recipients, text_body, html_body=None):
    msg = Message(subject, sender=app.config['MAIL_USERNAME'], recipients=[recipients])
    msg.body = text_body
    if html_body:
        msg.html = html_body
        mail.send(msg)