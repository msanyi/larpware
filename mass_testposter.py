from sqlalchemy import create_engine, exc
from sqlalchemy.orm import sessionmaker
from database import Bulletinboards, Posts, User
import random
from lorem_text import lorem
import sys

db_url = "localhost"
db_user ="root"
db_pass = "123qwe"
if len(sys.argv) == 4:
  db_url = sys.argv[1]
  db_user = sys.argv[2]
  db_pass = sys.argv[3]

DATABASE_URI = f'mysql+pymysql://{db_user}:{db_pass}@{db_url}/cyberpunk_larpware?charset=utf8mb4'
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)


def generate_post(session, board_id, user_id):
    content = lorem.paragraph()
    post = Posts(board_id=board_id, poster_id=user_id, postcontent=content)
    session.add(post)


if __name__ == '__main__':
    session = Session()

    try:
        boards = session.query(Bulletinboards).all()
        users = session.query(User).all()

        if not boards or not users:
            print("No boards or users found in the database!")
            exit()

        for _ in range(100):
            random_board = random.choice(boards)
            random_user = random.choice(users)
            generate_post(session, random_board.id, random_user.id)

        session.commit()
        print("Posts generated successfully!")

    except exc.SQLAlchemyError as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        session.close()
