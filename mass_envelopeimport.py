import json
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from database import Envelope, Userenvelope, User  # Import the necessary models
import sys

db_url = "localhost"
db_user = "root"
db_pass = "123qwe"
if len(sys.argv) == 4:
    db_url = sys.argv[1]
    db_user = sys.argv[2]
    db_pass = sys.argv[3]

DATABASE_URI = f'mysql+pymysql://{db_user}:{db_pass}@{db_url}/cyberpunk_larpware?charset=utf8mb4'

# Create engine and session
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)
session = Session()

# Load JSON data from file
with open('envelopes.json', 'r') as f:
    envelopes_data = json.load(f)

# Iterate over the data and add each envelope to the database
for envelope_data in envelopes_data:
    envelope = Envelope(
        number=envelope_data["number"],
        opening_condition=envelope_data["opening_condition"],
        content=envelope_data["content"]
    )
    session.add(envelope)
    session.commit()  # Commit the envelope immediately to obtain its ID

    print(f"envelope #{envelope.number} created.")
    # If user_envelopes are present in the JSON, create Userenvelope entries
    for user_envelope_data in envelope_data.get("user_envelopes", []):
        user = session.scalars(select(User).filter_by(username=user_envelope_data).limit(1)).first()
        if user is not None:
          user_envelope = Userenvelope(
              user_id=user.id,
              envelope_id=envelope.id,  # envelope.id is now available
              opened=False
          )
          print(f"added envelope #{envelope.number} to user {user.username}")
          session.add(user_envelope)
        else:
            print(f"user named {user_envelope_data} does not exist")

    session.commit()  # Commit Userenvelope entries

print("Envelopes imported successfully.")
