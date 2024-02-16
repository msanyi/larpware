# db structure plan

User table:

- id: Integer, unique, primary key
- username: String (80 characters), unique, not nullable
- password: String (120 characters), not nullable
- balance: Integer, default value 0
- is_admin: Boolean, default=False
- wound: Enum, 4 states: 1 unhurt, 2 wounded, 3 dying, 4 dead
- netrunner_skill: String, nullable
- fixer_skill: String, nullable
- passchanged:  Boolean, default=False

Transaction table:
- id: Integer, unique, primary key
- sender_id: Integer, foreign key referencing User.id, not nullable
- receiver_id: Integer, foreign key referencing User.id, not nullable
- app_id: Integer, foreign key referencing App.id, not nullable
- file_id: Integer, foreign key referencing File.id, not nullable
- amount: Integer, not nullable
- timestamp: DateTime, not nullable
- messageid: Integer, foreign key referencing Message.id, nullable

Friendship table:
- user_id: Integer, foreign key referencing User.id
- friend_id: Integer, foreign key referencing User.id

UserOrganization table:
- id: Integer, foreign key referencing User.id, not nullable
- organization_id: Integer, foreign key referencing Organizations.id, nullable
- endtime (null for permanent memberships)

Organizations
- id: Integer, unique, primary key
- orgname: String (120 characters), not nullable


App table
- id: Integer, unique, primary key
- name: String, not nullable
- is_attacker: Boolean, default=False
- is_defender: Boolean, default=False
- is_backdoor: Boolean, default=False
- is_cloak: Boolean, default=False
- is_tracer: Boolean, default=False
- is_siphon: Boolean, default=False
- is_crawler: Boolean, default=False
- is_sword: Boolean, default=False
- is_shield: Boolean, default=False
- is_banhammer: Boolean, default=False
- is_zap: Boolean, default=False
- is_restore: Boolean, default=False
- is_firewall: Boolean, default=False
- is_sweep: Boolean, default=False
- is_trojan: Boolean, default=False

Messages
- id: Integer, unique, primary key
- sender_id: Integer, foreign key referencing User.id, not nullable
- receiver_id: Integer, foreign key referencing User.id, not nullable
- messagecontent: Text, not nullable
- timesent: DateTime, not nullable
- isread: DateTime, nullable

Bulletinboards table
- id: Integer, unique, primary key
- boardtype: Integer (newsfeed, public, secure, darkweb)
- organization_id: Integer, foreign key referencing Organizations.id, nullable

Posts table
- id: Integer, unique, primary key
- board_id: Integer, foreign key referencing Bulletinboards.id, not nullable
- poster_id: Integer, foreign key referencing User.id, not nullable
- postcontent: Text, not nullable
- timeposted: DateTime, not nullable


# TODO BELOW
# Marketplace

itemcodes

- itemcodeid (primary key)
- itemtype (digitalinventory item or €$)
- itemid (foreign key -> digitalinventory, null for €$)
- amount (for €$)
- url

marketlistings
- listingid (primary key)
- itemtype (app, file, physical item)
- itemid (foreign key -> digitalinventory, null for physical items)
- price
- issold
- faction (for faction-specific listings, default is all)
- discount_price: Integer, nullable
- discount_organization: Integer, foreign key referencing Organizations.id, nullable

couriertasks
- taskid (primary key)
- listingid (foreign key -> marketlistings)
- isdelivered


