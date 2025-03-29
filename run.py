from app import create_app, db
from flask_migrate import Migrate
from flask_cors import CORS



app = create_app()

cors = CORS(app, resources={r"*": {"origins": "*"}})


with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, port=5000)

