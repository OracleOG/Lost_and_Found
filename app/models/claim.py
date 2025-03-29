from app import db
from app.models.base_model import BaseModel
from datetime import datetime

class Claim(BaseModel):
    """Tracks verified claims on items"""
    __tablename__ = 'claims'
    date_claimed = db.Column(db.DateTime, default=datetime.utcnow)
    additional_information = db.Column(db.Text, nullable=True)
    proof_image_url = db.Column(db.String(255), nullable=True)  # Proof of ownership
    status = db.Column(db.Enum('pending', 'approved', 'rejected', name='claim_status'), 
                       nullable=False, default='pending')
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    item = db.relationship('Item', back_populates='claims')
    user = db.relationship('User', back_populates='claims')
    location_lost = db.Column(db.String(255), nullable=True)
    date_lost = db.Column(db.DateTime, nullable=True)
