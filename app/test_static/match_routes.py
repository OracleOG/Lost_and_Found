from flask import Blueprint, flash, redirect, render_template, request, jsonify, url_for
from flask_login import login_required, current_user

from app.models.user import User
from app.utils.send_notification import send_email
from ..models.match import Match
from ..models.quality import QualityCheck
from app import db
from app.models.db_storage import DBStorage

match_bp = Blueprint('match_bp', __name__)
storage = DBStorage(db)




# Get all matches and display them
@match_bp.route('/matches', methods=['GET'])
@login_required
def list_matches():
    matches = Match.query.all()
    return render_template('list_matches.html', matches=matches)


# Confirm match
@match_bp.route('/matches/<int:match_id>/confirm', methods=['POST'])
@login_required
def confirm_match(match_id):
    match = Match.query.get(match_id)
    if not match:
        flash('Match not found', 'danger')
        return redirect(url_for('match_bp.list_matches'))

    if current_user.role.name != 'QualityChecker':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('match_bp.list_matches'))

    # Create a new QualityCheck record
    quality_check = QualityCheck(
        match_id=match.id,
        quality_checker_user_id=current_user.id,
        confirmed_owner_user_id=match.potential_owner_user_id,
        verified='confirmed'
    )
    storage.new(quality_check)
    
    # Update the match status
    match.status = 'confirmed'
    storage.save()

   # Send confirmation email to the user
    user = User.query.get(match.potential_owner_user_id)
    if user:
        subject = "Match Confirmation"
        recipients = user.email
        text_body = f"Hello {user.username},\n\nYour match for item ID {match.item_id} has been confirmed."
        html_body = render_template('emails/match_confirmation.html', user=user, match=match)
        send_email(subject, recipients, text_body, html_body)

    flash('Match confirmed successfully', 'success')
    return redirect(url_for('match_bp.list_matches'))
