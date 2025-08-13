from app import create_app, db
from app.utils import create_admin_if_not_exists

app = create_app()

with app.app_context():
    db.create_all()
if __name__ == '__main__':
    """
    with app.app_context():
        create_admin_if_not_exists()
    """
    app.run(host='0.0.0.0', port=5002, debug=True)
