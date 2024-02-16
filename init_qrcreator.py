from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import random
import string
import sys

from database import Qrcode, Node, NodeType, Network, Organizations, File

# Connect to your database

db_url = "localhost"
db_user ="root"
db_pass = "123qwe"
if len(sys.argv) == 4:
  db_url = sys.argv[1]
  db_user = sys.argv[2]
  db_pass = sys.argv[3]

engine = create_engine(f'mysql+pymysql://{db_user}:{db_pass}@{db_url}/cyberpunk_larpware?charset=utf8mb4', echo=True)
Session = sessionmaker(bind=engine)


def random_hex(length=2):
    return ''.join(random.choices(string.hexdigits, k=length))


def generate_qrcode_prefix(node_count):
    if 1 <= node_count <= 5:
        return "NETWORK"
    elif 6 <= node_count <= 10:
        return "ARCHITECTURE"
    elif 11 <= node_count <= 15:
        return "DATAFORTRESS"
    elif node_count >= 16:
        return "MATRIX"
    else:
        return None


def main():
    # create a new session
    session = Session()

    # query all networks
    networks = session.query(Network).all()
    for network in networks:
        # get organization
        organization = session.query(Organizations).filter_by(id=network.organization_id).first()
        if organization:
            organization_name = organization.orgname

            # generate QR code for first node of each network
            first_node = session.query(Node).filter_by(network_id=network.id).order_by(Node.order).first()
            if first_node:
                network_length = session.query(Node).filter_by(network_id=network.id).count()
                prefix = generate_qrcode_prefix(network_length)

                qr_string = f"{prefix}-{random_hex()}-{organization_name}-{random_hex(4)}-{network.id}"
                new_qrcode = Qrcode(qrcode=qr_string, qrcodetype="accesspoint", targetid=network.id)
                session.add(new_qrcode)

    # commit changes to db
    session.commit()
    session.close()


if __name__ == '__main__':
    main()
