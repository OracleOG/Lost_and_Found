from app import db
from app.models.base_model import BaseModel


class Match(BaseModel):
    """Confirmed match between a claim and an item"""
    __tablename__ = 'matches'
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'))
    claim_id = db.Column(db.Integer, db.ForeignKey('claims.id'))
    status = db.Column(db.Enum('pending', 'confirmed', name='match_status'), 
                       nullable=False, default='pending')
    item = db.relationship('Item', back_populates='matches')
    claim = db.relationship('Claim', backref='match')