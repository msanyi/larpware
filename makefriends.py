# makefriends.py
# this is called from mass_useradd.py, not standalone
from database import db, User, UserOrganization, Organizations


def make_friends_in_org():
    print("making friends in same organization")
    organizations = Organizations.query.all()
    for org in organizations:
        print(f"checking organization {org.orgname}")
        org_members = UserOrganization.query.filter_by(organization_id=org.id).all()
        for user_org in org_members:
            user = User.query.get(user_org.user_organization_id)
            print(f"making friends for user {user.username}")
            for other_user_org in org_members:
                other_user = User.query.get(other_user_org.user_organization_id)
                if user != other_user and not user.is_friends_with(other_user):
                    print(f"adding {other_user.username} for {user.username}")
                    user.add_friend(other_user)


def main():
    make_friends_in_org()
    db.session.commit()


if __name__ == "__main__":
    main()
