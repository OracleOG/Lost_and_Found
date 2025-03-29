from app import db
from app.models.base_model import BaseModel
class Test(db.Model):
    __tablename__ = 'tests2'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True)
    testname = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return 'Test: [id: {}, username: {}, testname: {}'.format(self.id, self.username, self.testname)
