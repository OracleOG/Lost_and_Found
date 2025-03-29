from flask import Blueprint, flash, redirect, render_template, request, jsonify, url_for
from flask_login import login_required, current_user

from app.models.item import Item
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
    page = request.form.get('page', 1, type=int)
    if not match:
        flash('Match not found', 'danger')
        return redirect(url_for('quality_bp.Q_list', page=page))

    if current_user.role.name != 'QualityChecker':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('quality_bp.Q_list', page=page))
   # Check if the user has already confirmed a match for this item
    existing_confirmed_match = QualityCheck.query.filter_by(
        quality_checker_user_id=current_user.id,
        match_id=match.id,
        verified='confirmed'
    ).first()
    if existing_confirmed_match:
        flash('You have already confirmed a match for this item.', 'danger')
        return redirect(url_for('quality_bp.Q_list', page=page))
    # Create a new QualityCheck record,
    quality_check = QualityCheck(
        match_id=match.id,
        quality_checker_user_id=current_user.id,
        confirmed_owner_user_id=match.potential_owner_user_id,
        verified='confirmed'
    )
    storage.new(quality_check)
    
    # Update the match status
    match.status = 'confirmed'
    # Update the mainn item's status to 'closed'
    item = Item.query.get(match.item_id)
    if item:
        item.status = 'Closed'
        storage.new(item)
    storage.save()
    flash('Match confirmed successfully', 'success')
    return redirect(url_for('quality_bp.Q_list'))
   # Send confirmation email to the user
    user = User.query.get(match.potential_owner_user_id)
    if user:
        subject = "Match Confirmation"
        recipients = user.email
        text_body = f"Hello {user.username},\n\nYour match for item ID {match.item_id} has been confirmed."
        html_body = render_template('match_confirmation.html', user=user, match=match)
        send_email(subject, recipients, text_body, html_body)




# reject match
@match_bp.route('/matches/<int:match_id>/reject', methods=['POST'])
@login_required
def reject_match(match_id):
    match = Match.query.get(match_id)
    page = request.form.get('page', 1, type=int)
    if not match:
        flash('Match not found', 'danger')
        return redirect(url_for('quality_bp.Q_list'))

    if current_user.role.name != 'QualityChecker':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('quality_bp.Q_list', page=page))
        #    # Check if the user has already confirmed a match for this item
        #     existing_confirmed_match = QualityCheck.query.filter_by(
        #         quality_checker_user_id=current_user.id,
        #         match_id=match.id,
        #         verified='rejected'
        #     ).first()
        #     if existing_confirmed_match:
        #         flash('You have already rejected a match for this item.', 'danger')
        #         return redirect(url_for('quality_bp.quality_checker'))
        # Create a new QualityCheck record
    quality_check = QualityCheck(
        match_id=match.id,
        quality_checker_user_id=current_user.id,
        confirmed_owner_user_id=match.potential_owner_user_id,
        verified='rejected'
    )
    storage.new(quality_check)
    
    # Update the match status
    match.status = 'rejected'
    storage.save()

 

    flash('Match reject successfully', 'success')
    return redirect(url_for('quality_bp.Q_list'))