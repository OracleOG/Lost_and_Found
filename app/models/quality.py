#from app import db
#from app.models.base_model import BaseModel
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime

class QualityCheck(db.Model):
    __tablename__ = 'quality_checks'
    id = Column(Integer, primary_key=True)
    date_checked = Column(DateTime, default=datetime.utcnow)
    verified = Column(String(50), nullable=True, default='pending')
    confirmed_owner_user_id = Column(Integer, ForeignKey('users.id'))
    match_id = Column(Integer, ForeignKey('matches.id'))
    match = relationship('Match', back_populates='quality_checks')
    quality_checker_user_id = Column(Integer, ForeignKey('users.id'))
    quality_checker_user = relationship('User', foreign_keys=[quality_checker_user_id])

