from flask import Flask
from database import db, NodeType, Organizations, UserOrganization, AppType, Bulletinboards, User, Network
from werkzeug.security import generate_password_hash
import sys


def create_app():
    dbinit_app = Flask(__name__)
    db_url = "localhost"
    db_user ="root"
    db_pass = "123qwe"
    if len(sys.argv) == 4:
      db_url = sys.argv[1]
      db_user = sys.argv[2]
      db_pass = sys.argv[3]

    dbinit_app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{db_user}:{db_pass}@{db_url}/cyberpunk_larpware?charset=utf8mb4'
    db.init_app(dbinit_app)
    return dbinit_app


def init_node_types(dbinit_app):
    with dbinit_app.app_context():
        node_types = [
            NodeType(name="Password", interaction='crack', seconds_to_solve=None, send_message=False, delete_app=False, changes_wound_status=False,
                     description="Ellenőrzi a kriptokulcsodat. Ha nem az üzemeltető szervezetbe tartozol, nem léphetsz tovább a következő Node-ba. A Backdoor segítségével feltörhető."),

            NodeType(name="White IC", interaction='crack', seconds_to_solve=None, send_message=True, delete_app=False, changes_wound_status=False,
                     description="Ha továbblépsz a következő Node-ba és nem ugyanabban a frakcióban vagy, mint amelyik birtokolja az Architektúrát, üzenetet küld azonosító adataiddal a frakció üzenőfalára. A Cloak megszakítja az üzenetet, és bármilyen Támadó programmal semlegesíthető az IC, feltörve a Node-ot."),

            NodeType(name="Grey IC", interaction='crack', seconds_to_solve=30, send_message=False, delete_app=True, changes_wound_status=False,
                     description="Ha nem vagy ugyanabban a frakcióban, mint amelyik birtokolja az Architektúrát, nem léphetsz tovább. Továbbá, ha nem használsz Támadó programot 30 másodpercen belül a Node-ba lépés után, töröl egy véletlenszerű App-ot. A támadó program használata feltöri a Node-ot."),

            NodeType(name="Black IC", interaction='crack', seconds_to_solve=30, send_message=False, delete_app=False, changes_wound_status=True,
                     description="Ha nem vagy ugyanabban a frakcióban, mint amelyik birtokolja az Architektúrát, és továbblépsz a következő/előző Node-ba vagy több mint 30 másodpercet töltesz ebben a Node-ban, DYING állapotba kerülsz. Egy Támadó ÉS egy Védő program használata 2 percen belül a Node-ba lépés után feltöri. Az egyik program használata esetén WOUNDED állapotba kerülsz a DYING helyett, amikor továbblépsz vagy letelik a 30 másodperc (amelyik előbb következik)."),

            NodeType(name="Account Info", interaction='crack', seconds_to_solve=None, send_message=False, delete_app=False, changes_wound_status=False,
                     description="Ezt a Node-ot egy Siphon alkalmazással törheted fel. Ennek során megadhatsz egy CityNet számot, akinek a számlájára átutalhatsz egy összeget, amelyet az Architektúra egyik tagjától emelsz el."),

            NodeType(name="Intel", interaction='crack', seconds_to_solve=None, send_message=False, delete_app=False, changes_wound_status=False,
                     description="Ha a node nem cracked állapotú, egy Crawler appal letölthetsz innen egy véletlenszerű csatolt fájlt, ezzel crackelve a Node-ot. A fájl nem törlődik a Node-ból."),

            NodeType(name="Blank", interaction='area', seconds_to_solve=None, send_message=False, delete_app=False, changes_wound_status=False,
                     description="Ennek a Node-nak nincs különleges hatása."),

            NodeType(name="Area", interaction='area', seconds_to_solve=None, send_message=False, delete_app=False, changes_wound_status=False,
                     description="A felhasználók beléphetnek ebbe a node-ba védelemért.")
        ]

        for node_type in node_types:
            db.session.add(node_type)

        db.session.commit()


def init_organizations(dbinit_app):
    with dbinit_app.app_context():
        organizations = [
            Organizations(id=1, orgname='Entertec Network'),
            Organizations(id=2, orgname='Club Flatline'),
            Organizations(id=3, orgname='Night Market'),
            Organizations(id=4, orgname='Black Dragons'),
            Organizations(id=5, orgname='Blades'),
            Organizations(id=6, orgname='Metroplex 8'),
            Organizations(id=7, orgname='Chip Clinic BAMA'),
            Organizations(id=8, orgname='Black Arms'),
            Organizations(id=9, orgname='Prophet'),
            Organizations(id=10, orgname='Inner Circle'),
            Organizations(id=11, orgname='Codex Ignis'),
            Organizations(id=12, orgname='Project Daedalus'),
            Organizations(id=13, orgname='UNKNOWN_ERROR'),
            Organizations(id=14, orgname='Rache Bartmoss EDU'),
            Organizations(id=15, orgname='Cerveau Disco'),
            Organizations(id=16, orgname='NOT_FOUND'),
            Organizations(id=17, orgname='MISSING_CODE'),
            Organizations(id=18, orgname='Zurich-Orbital Banking')
        ]

        for organization in organizations:
            db.session.add(organization)

        db.session.commit()


# UNTESTED ************************
# TODO testing and finalizing
def init_networks(dbinit_app):
    with dbinit_app.app_context():
        # Query all existing organizations
        organizations = Organizations.query.all()

        for organization in organizations:
            # Create a Network entry for each organization
            network_name = f"Network Name {organization.id}"
            new_network = Network(name=network_name, organization_id=organization.id)

            # Add the new network to the session
            db.session.add(new_network)

        # Commit the session to save the networks to the database
        db.session.commit()


def init_app_types(dbinit_app):
    with dbinit_app.app_context():
        app_types = [
            AppType(name="Backdoor", description="Feltör egy Jelszó csomópontot.", is_netrunnersonly=True, type='Backdoor'),
            AppType(name="Cloak", description="Automatikusan megszakít egy Programot vagy Jeget, amely felfedné az személyazonosságodat.", is_netrunnersonly=True, type='Cloak'),
            AppType(name="Tracer", description="Felfedi más Netrunnerek személyazonosságát (Street Handle és CityNet Szám) és helyzetét ugyanabban az architektúrában.", is_netrunnersonly=True, type='Tracer'),
            AppType(name="Siphon", description="Amikor egy Számla Info csomópontnál használod, véletlenszerűen kiválasztja az Architektúra tulajdonosának egy tagját, és 10-30% közötti véletlenszerű százalékát átutalja az ő bankjából egy általad meghatározott számlára.", is_netrunnersonly=True, type='Siphon'),
            AppType(name="Crawler", description="Véletlenszerű adatot húz ki egy Intel csomópontból.", is_netrunnersonly=True, type='Crawler'),
            AppType(name="Sword", description="Támadó program (Szükséges a Jegek semlegesítéséhez). Ha egy másik Netrunnerre irányítod, töröl tőle egy véletlenszerű Appot.", is_netrunnersonly=True, type='attacker'),
            AppType(name="Shield", description="Védelmi program (Szükséges a Fekete Jég teljes semlegesítéséhez). Ha egy támadó programot irányítanak rád, az egyik Shield programod automatikusan lefut és semlegesíti azt.", is_netrunnersonly=True, type='defender'),
            AppType(name="Banhammer", description="Támadó program (Szükséges a Jegek semlegesítéséhez). Ha egy másik Netrunnerre használod, erőszakosan kidobja őt az Architektúrából, és újra be kell jelentkeznie.", is_netrunnersonly=True, type='attacker'),
            AppType(name="Zap", description="Támadó program (Szükséges a Jegek semlegesítéséhez). Ha egy másik Netrunnerre használod, ő SEBESÜLT lesz.", is_netrunnersonly=True, type='attacker'),
            AppType(name="Restore", description="Egy feltört csomópontnál használva, visszaállítja a csomópont teljes funkcionalitását.", is_netrunnersonly=True, type='Restore'),
            AppType(name="Firewall", description="Megbont egy Számla Info vagy Intel csomópontot bármilyen más hatás nélkül, ezzel használhatatlanná teszi azt más Netrunnerek számára, amíg az regenerálódik. Ez az egyetlen módja, hogy a saját frakciódhoz tartozó Csomópontot feltörj.", is_netrunnersonly=True, type='Firewall'),
            AppType(name="Sweep", description="Eltávolítja a Hálózatot birtokló frakció ideiglenes tagsági jelzéseit.", is_netrunnersonly=True, type='Sweep'),
            AppType(name="Trojan", description="Amikor egy Hálózaton belül használod, saját magadat vagy egy kiválasztott CityNet számot a Hálózatot birtokló frakció ideiglenes tagjává tesz, véletlenszerűen 2-4 órára.", is_netrunnersonly=True, type='Trojan'),
            AppType(name="Scrub", description="Eltávolítja a másoló nevét a másolt dokumentumról", is_netrunnersonly=True, type='Scrub'),
            # AppType(name="Decrypt", description="Megnyit egy titkosított fájlt.", is_netrunnersonly=False, type='defender'),
            AppType(name="Lockpick", description="Kinyit egy digitális zárat.", is_netrunnersonly=False, type='defender')
        ]
        for app_type in app_types:
            db.session.add(app_type)
        db.session.commit()


def init_node_to_app_mapping(dbinit_app):
    with dbinit_app.app_context():
        node_to_app_mappings = [
            {"node_type": "Password", "app_types": ["Backdoor", "Restore", "Tracer", 'Trojan', 'Sweep']},
            {"node_type": "White IC", "app_types": ["Cloak", "Sword", "Banhammer", "Zap", "Restore", "Tracer", 'Trojan', 'Sweep']},
            {"node_type": "Grey IC", "app_types": ["Sword", "Banhammer", "Zap", "Restore", "Tracer", 'Trojan', 'Sweep']},
            {"node_type": "Black IC", "app_types": ["Sword", "Banhammer", "Zap", "Shield", "Restore", "Tracer", 'Trojan', 'Sweep']},
            {"node_type": "Account Info", "app_types": ["Siphon", "Firewall", "Restore", "Tracer", 'Trojan', 'Sweep']},
            {"node_type": "Intel", "app_types": ["Crawler", "Firewall", "Restore", "Tracer", 'Trojan', 'Sweep']},
            {"node_type": "Blank", "app_types": ["Tracer", 'Trojan', 'Sweep']},
            {"node_type": "Area", "app_types": ["Tracer", 'Trojan', 'Sweep']}
        ]

        for mapping in node_to_app_mappings:
            node_type = NodeType.query.filter_by(name=mapping["node_type"]).first()
            for app_type_name in mapping["app_types"]:
                app_type = AppType.query.filter_by(name=app_type_name).first()
                if node_type and app_type:
                    node_type.apps.append(app_type)

        db.session.commit()


def init_bulletinboards(dbinit_app):
    with dbinit_app.app_context():
        # Step 1: Newsfeed
        newsfeed_board = Bulletinboards(name="NewsFeed", boardtype="newsfeed")
        db.session.add(newsfeed_board)

        # Step 2: Public
        public_board = Bulletinboards(name="Public Board", boardtype="public")
        db.session.add(public_board)

        # Step 3: Secure Boards
        organizations = Organizations.query.all()
        for org in organizations:
            secure_board = Bulletinboards(name=f"Secure {org.orgname}", boardtype="secure", organization_id=org.id)
            db.session.add(secure_board)

        # Step 4: Darkweb
        darkweb_board = Bulletinboards(name="DarkWeb", boardtype="darkweb")
        db.session.add(darkweb_board)

        # Step 5: Commit
        db.session.commit()


def create_watchdog_users(dbinit_app):
    # TODO: add users to the userorg table
    with dbinit_app.app_context():
        # 1. Fetch all the organizations from the database
        all_orgs = Organizations.query.all()

        # 2. Default password
        default_password = "12321"
        hashed_password = generate_password_hash(default_password)

        for org in all_orgs:
            # 3. Generate watchdog username for the organization
            watchdog_username = f"{org.orgname} Architecture Watchdog"

            # Check if the user already exists, if not, then create
            user_exists = User.query.filter_by(username=watchdog_username).first()
            if not user_exists:
                # 4. Create new watchdog user for the organization
                new_watchdog = User(username=watchdog_username, password=hashed_password, is_admin=False)  # Here we are assuming watchdog users are not admins
                db.session.add(new_watchdog)
                db.session.flush()
                
                user_org = UserOrganization(
                    user_organization_id=new_watchdog.id,
                    organization_id=org.id
                )
                db.session.add(user_org)

        # Commit the changes to the database
        db.session.commit()

        print("Watchdog users created successfully.")


if __name__ == "__main__":
    app = create_app()
    init_node_types(app)
    init_organizations(app)
    init_networks(app)
    init_app_types(app)
    init_node_to_app_mapping(app)
    init_bulletinboards(app)
    create_watchdog_users(app)
