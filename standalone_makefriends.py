# standalone_makefriends.py
# checks if all existing friendships are mutual, and if not, add the counterpart to make the friendship mutual, and also makes all members of the same organization friends of each other
from flask import Flask
from database import db, User, UserOrganization, Organizations

def make_friends_in_org():
    session = db.session
    organizations = Organizations.query.all()
    for org in organizations:
        org_members = UserOrganization.query.filter_by(organization_id=org.id).all()
        for user_org in org_members:
            user = session.get(User, user_org.user_organization_id)
            for other_user_org in org_members:
                other_user = session.get(User, other_user_org.user_organization_id)
                if user != other_user and not user.is_friends_with(other_user):
                    user.add_friend(other_user)


def main():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123qwe@localhost/cyberpunk_larpware?charset=utf8mb4'
    db.init_app(app)

    with app.app_context():
        make_friends_in_org()
        db.session.commit()


if __name__ == "__main__":
    main()
