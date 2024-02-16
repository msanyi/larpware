# this is the beginning of database.py
from flask_sqlalchemy import SQLAlchemy  # Import the SQLAlchemy module
from datetime import datetime
from sqlalchemy import Enum, UniqueConstraint, Column
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.ext.mutable import MutableDict

db = SQLAlchemy()  # Create a SQLAlchemy instance


class User(db.Model):  # Define the User model class, which inherits from db.Model
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    balance = db.Column(db.Integer, default=0)
    is_admin = db.Column(db.Boolean, default=False)
    wound = db.Column(db.Enum('unhurt', 'wounded', 'dying', 'dead', name='wound_states'), default='unhurt')
    is_netrunner = db.Column(db.Boolean, default=False)
    is_fixer = db.Column(db.Boolean, default=False)
    passchanged = db.Column(db.Boolean, default=False)
    friends = db.relationship('Friendship', foreign_keys='Friendship.user_id')
    citynet = db.Column(db.Integer, unique=True)  # Unique CityNet number
    inventories = db.relationship('Inventory', backref='user', lazy='select')
    user_envelopes = db.relationship('Userenvelope', back_populates='user', lazy='dynamic')
    is_npc = db.Column(db.Boolean, default=False)
    armor_value = db.Column(db.Integer, default=0)
    reflex_value = db.Column(db.Integer, default=0)
    ui_style = db.Column(db.String(20), default='console-green')

    def add_friend(self, user):
        if not self.is_friends_with(user):
            new_friendship1 = Friendship(user_id=self.id, friend_id=user.id)
            new_friendship2 = Friendship(user_id=user.id, friend_id=self.id)
            db.session.add(new_friendship1)
            db.session.add(new_friendship2)

    def remove_friend(self, user):
        if self.is_friends_with(user):
            Friendship.query.filter_by(user_id=self.id, friend_id=user.id).delete()
            Friendship.query.filter_by(user_id=user.id, friend_id=self.id).delete()

    def is_friends_with(self, user):
        return Friendship.query.filter(
            (Friendship.user_id == self.id) & (Friendship.friend_id == user.id) |
            (Friendship.user_id == user.id) & (Friendship.friend_id == self.id)
        ).count() > 0

    def set_password(self, new_password):
        """This method sets a new password and changes passchanged attribute to True"""
        self.password = generate_password_hash(new_password)
        self.passchanged = True
        db.session.commit()

    def check_password(self, password):
        """This method checks the password provided against the hashed password in the database"""
        return check_password_hash(self.password, password)


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)


class Friendship(db.Model):
    __tablename__ = 'friendship'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    friend_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    friend = db.relationship('User', foreign_keys=[friend_id])


class UserOrganization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_organization_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'))
    endtime = db.Column(db.DateTime)
    user = db.relationship('User', backref='organizations')


class Organizations(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    orgname = db.Column(db.String(120), nullable=False)
    users = db.relationship('UserOrganization', backref='organization')


class Messages(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    messagecontent = db.Column(db.Text, nullable=False)
    timesent = db.Column(db.DateTime, default=datetime.utcnow)
    isread = db.Column(db.DateTime)
    sender = db.relationship('User', foreign_keys=[sender_id])
    receiver = db.relationship('User', foreign_keys=[receiver_id])
    is_system = db.Column(db.Boolean, default=False)


class Bulletinboards(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    boardtype = db.Column(db.Enum('newsfeed', 'public', 'secure', 'darkweb', name='board_types'))
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'))


class Posts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    board_id = db.Column(db.Integer, db.ForeignKey('bulletinboards.id'), nullable=False)
    poster_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    postcontent = db.Column(db.Text, nullable=True)
    timeposted = db.Column(db.DateTime, default=datetime.utcnow)
    file_id = db.Column(db.Integer, db.ForeignKey('file.id'), nullable=True)  # Added file_id column

    board = db.relationship('Bulletinboards', backref=db.backref('posts', lazy=True))
    file = db.relationship('File', back_populates='posts')


class Boardview(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    board_id = db.Column(db.Integer, db.ForeignKey('bulletinboards.id'), primary_key=True)
    last_viewed_timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('user_id', 'board_id', name='_user_board_uc'),)


class Reaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message_id = db.Column(db.Integer, db.ForeignKey('messages.id'), nullable=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=True)
    reaction_type = db.Column(Enum('like', 'dislike', 'seen', name='reaction_types'), nullable=False)  # 'like' or 'dislike'
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('user_id', 'message_id', 'post_id', 'reaction_type', name='_user_message_post_reaction_uc'),)


class AppType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    is_netrunnersonly = db.Column(db.Boolean, default=False)
    type = db.Column(
        db.Enum('attacker', 'defender', 'backdoor', 'cloak', 'tracer', 'siphon', 'crawler', 'sword', 'shield',
                'banhammer', 'zap', 'restore', 'firewall', 'sweep', 'trojan', 'scrub', 'decrypt', 'lockpick', name='app_types'), nullable=False)


class App(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    app_type_id = db.Column(db.Integer, db.ForeignKey('app_type.id'), nullable=False)
    name = db.Column(db.String(80), unique=False, nullable=False)
    use_timestamp = db.Column(db.DateTime, nullable=True)
    inventories = db.relationship('Inventory', backref='app', lazy='select')

    # We can use this relationship to easily access the AppType related to this App
    app_type = db.relationship('AppType', backref='apps')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'app_type_id': self.app_type_id
        }


class Digitalmarketlisting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Integer, nullable=False)
    listing_type = db.Column(db.Enum('App', 'File', 'Physical Item', name='listing_types'))
    app_id = db.Column(db.Integer, db.ForeignKey('app.id'))
    file_id = db.Column(db.Integer, db.ForeignKey('file.id'))
    market_type = db.Column(db.Enum('Public', 'Fixer', 'Darkweb', name='market_types'))
    valid_from = db.Column(db.DateTime, nullable=True)

    # Relationships
    app = db.relationship('App', backref='listings')
    file = db.relationship('File', backref='listings')


class Couriertask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey('digitalmarketlisting.id'))
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(db.Enum('New', 'Pending', 'Completed', name='task_statuses'))

    # Relationships
    listing = db.relationship('Digitalmarketlisting', backref='courier_tasks', primaryjoin="Couriertask.listing_id == Digitalmarketlisting.id")
    buyer = db.relationship('User', backref='purchases')


class Organizationavailability(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey('digitalmarketlisting.id'))
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'))

    # Relationships
    listing = db.relationship('Digitalmarketlisting', backref='availability_rules')
    organization = db.relationship('Organizations', backref='availability_rules')


class Network(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'))

    nodes = db.relationship('Node', backref='network', lazy='dynamic')

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'organization_id': self.organization_id,
            'nodes': [node.serialize() for node in self.nodes.all()]
        }


# Define the association table for the many-to-many relationship
node_app_link = db.Table(
    'node_app_link',
    db.Column('node_type_id', db.Integer, db.ForeignKey('node_type.id')),
    db.Column('app_type_id', db.Integer, db.ForeignKey('app_type.id')),
    db.PrimaryKeyConstraint('node_type_id', 'app_type_id')
)


class Node(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    network_id = db.Column(db.Integer, db.ForeignKey('network.id'), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    order = db.Column(db.Integer, nullable=False)
    is_cracked = db.Column(db.Boolean, default=False)
    file_ids = db.Column(JSON)
    node_type_id = db.Column(db.Integer, db.ForeignKey('node_type.id'))
    crack_timestamp = db.Column(db.DateTime, nullable=True)

    max_users = db.Column(db.Integer, default=2)  # 2 is the default value, -1 means unlimited
    node_type = db.relationship('NodeType', backref='nodes')

    def serialize(self):
        return {
            'id': self.id,
            'network_id': self.network_id,
            'name': self.name,
            'order': self.order,
            'is_cracked': self.is_cracked,
            'file_ids': self.file_ids,
            'node_type_id': self.node_type_id,
            'max_users': self.max_users
        }


class NodeType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    interaction = db.Column(db.Enum('crack', 'restore', 'area', name='interactions'))
    seconds_to_solve = db.Column(db.Integer, default=0)
    send_message = db.Column(db.Boolean, default=False)
    delete_app = db.Column(db.Boolean, default=False)
    changes_wound_status = db.Column(db.Boolean, default=False)
    apps = db.relationship('AppType', secondary=node_app_link, backref=db.backref('nodetypes', lazy=True))


class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    content = db.Column(db.Text, nullable=False)
    original_owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    copied_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    inventories = db.relationship('Inventory', backref='file', lazy='select')
    original_owner = db.relationship('User', foreign_keys=[original_owner_id])
    copied_by = db.relationship('User', foreign_keys=[copied_by_id])
    posts = db.relationship('Posts', back_populates='file')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'content': self.content,
            'original_owner_id': self.original_owner_id,
            'copied_by_id': self.copied_by_id,
            'original_owner_username': self.original_owner.username if self.original_owner else None,
            'copied_by_username': self.copied_by.username if self.copied_by else None,
        }


class NodeOperationsHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    node_id = db.Column(db.Integer, db.ForeignKey('node.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    operation_type = db.Column(db.Enum('login', 'logout', 'move', 'app_use', name='operation_types'))
    timestamp = db.Column(db.DateTime, nullable=False)
    app_used = db.Column(db.Integer, db.ForeignKey('app.id'), nullable=True)


class NodeUsers(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    node_id = db.Column(db.Integer, db.ForeignKey('node.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    # interaction_data = db.Column(MutableDict.as_mutable(JSON))
    interaction_data: 'Column[MutableDict]' = Column(MutableDict.as_mutable(JSON))
    attack_data: 'Column[MutableDict]' = Column(MutableDict.as_mutable(JSON))


class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    app_id = db.Column(db.Integer, db.ForeignKey('app.id'), nullable=True)
    file_id = db.Column(db.Integer, db.ForeignKey('file.id'), nullable=True)


class Qrcode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    qrcodetype = db.Column(db.Enum('lock', 'inventoryadd_app', 'inventoryadd_file', 'accesspoint', 'inventoryadd_cash', name='qrcode_types'), nullable=False)
    targetid = db.Column(db.Integer, nullable=True)  # This will reference different tables based on qrcodetype
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=True)


class MetUsers(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    network_id = db.Column(db.Integer, db.ForeignKey('network.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    met_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    citynet_number = db.Column(db.String(255), nullable=True)
    tracer_used = db.Column(db.Boolean, default=False)
    current_order = db.Column(db.String(255), nullable=True)
    current_node_name = db.Column(db.String(255), nullable=True)

    # Relationships
    network = db.relationship('Network', backref='met_users')
    user = db.relationship('User', foreign_keys=[user_id], backref='met_users_as_user')
    met_user = db.relationship('User', foreign_keys=[met_user_id], backref='met_users_as_met_user')

    __table_args__ = (
        db.UniqueConstraint('network_id', 'user_id', 'met_user_id', name='_network_user_met_user_uc'),
    )

    # Auxiliary table for many-to-many relationship
    user_met_users = db.Table('user_met_users',
                              db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
                              db.Column('met_user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
                              db.Column('tracer_used', db.Boolean, default=False),
                              db.Column('current_location_order', db.Integer),
                              db.Column('current_location_name', db.String(255))
                              )


class Envelope(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, unique=True, nullable=False)
    opening_condition = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_envelopes = db.relationship('Userenvelope', back_populates='envelope', lazy='dynamic')


class Userenvelope(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    envelope_id = db.Column(db.Integer, db.ForeignKey('envelope.id'), nullable=False)
    opened = db.Column(db.Boolean, default=False)
    user = db.relationship('User', back_populates='user_envelopes')
    envelope = db.relationship('Envelope', back_populates='user_envelopes')


class EventQueue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    data = db.Column(db.Text, nullable=False)


class SSEClient(db.Model):
    user_id = db.Column(db.Integer, primary_key=True, nullable=False)
    last_event = db.Column(db.Integer, nullable=False)


# this is the end of database.py
