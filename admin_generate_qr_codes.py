import os
import random
import string
import segno
from flask import Flask
import sys
from database import db, Qrcode

def create_app():
    app = Flask(__name__)
    db_url = "localhost"
    db_user ="root"
    db_pass = "123qwe"
    if len(sys.argv) == 4:
      db_url = sys.argv[1]
      db_user = sys.argv[2]
      db_pass = sys.argv[3]

    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{db_user}:{db_pass}@{db_url}/cyberpunk_larpware?charset=utf8mb4'
    db.init_app(app)
    return app

def random_hex(length=2):
    return ''.join(random.choices(string.hexdigits, k=length))


def generate_qr_codes(qrtype, qrtext=None, quantity=1, organization_id=None):
    max_id = db.session.query(db.func.max(Qrcode.id)).scalar() or 0
    next_id = max_id + 1

    directory_path = os.path.join('qrcodes', qrtype)
    os.makedirs(directory_path, exist_ok=True)

    sql_statements = []

    local_file_path = './static/flatlinelogo-qr.png'

    for i in range(quantity):
        filename = f"{qrtype}_{next_id}.png"
        filepath = os.path.join(directory_path, filename)

        # Use qrtext as content of the QRCode if provided, else use filename
        content = str(next_id)

        if len(content) > 44:
            raise ValueError("content should not be more than 44 characters")

        # the higher the version, the bigger the data amount, from 1 to 14
        qrcode = segno.make(content, error='h')

        bg_file = open(local_file_path, 'rb')
        # the higher the scale, the higher the print size in pixels
        qrcode.to_artistic(background=bg_file, target=filepath, scale=9)
        
        bg_file.close()

        qr_entry = Qrcode(id=next_id, qrcode=content, qrcodetype=qrtype, organization_id=organization_id)
        db.session.add(qr_entry)

        # Generate SQL statement for each QR code
        sql_statements.append(f"INSERT INTO qrcode (id, qrcode, qrcodetype, organization_id) VALUES ({next_id}, '{content}', '{qrtype}', {organization_id if organization_id else 'NULL'});")  # changed '{filename}' to '{content}'
        next_id += 1

    db.session.commit()
    return sql_statements


def sql_export(sql_statements):
    with open('qrcodes/qr_code_inserts.sql', 'w') as f:
        for statement in sql_statements:
            f.write(statement + '\n')


def qrparams():
    # Define the parameters
    params = [
        {'type': 'accesspoint', 'quantity': 1, 'org_names': ['Entertec Network', 'Club Flatline', 'Night Market', 'Black Dragons', 'Blades', 'Metroplex 8', 'Chip Clinic BAMA', 'Black Arms', 'Prophet', 'Inner Circle', 'Codex Ignis', 'Project Daedalus', 'UNKNOWN_ERROR', 'Rache Bartmoss EDU', 'Cerveau Disco', 'NOT_FOUND', 'MISSING_CODE', 'Zurich-Orbital Banking']},
        {'type': 'lock', 'quantity': 1},
        {'type': 'inventoryadd_app', 'quantity': 1},
        {'type': 'inventoryadd_file', 'quantity': 1},
    ]

    all_sql_statements = []

    for param in params:
        qrtype = param['type']
        quantity = param['quantity']
        org_names = param.get('org_names', [None])

        for idx, org_name in enumerate(org_names, 1):
            qrtext = None
            sql_statements = generate_qr_codes(qrtype, qrtext, quantity, idx)
            all_sql_statements.extend(sql_statements)

    # Export all SQL statements to a file
    sql_export(all_sql_statements)




if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        qrparams()
        db.session.remove()
