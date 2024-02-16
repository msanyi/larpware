import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import File  # Import the necessary models
import sys

db_url = "localhost"
db_user ="root"
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
# Load JSON data from file
with open('files.json', 'r') as f:
    files_data = json.load(f)

# Iterate over the data and add each envelope to the database
for file_data in files_data:
    file = File(
        name=file_data["title"],
        content=file_data["content"],
    )
    session.add(file)
    print(f"imported file: {file.name}")

session.commit()  


print("Files imported successfully.")