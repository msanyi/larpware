# CyberpunkLarpWare
LARP support software for a Cyberpunk game

# prerequisites
- MySql 8
- Python 3.10
- Flask
- sqlalchemy
- flask_sqlalchemy
- pymysql



# How to run
- python3 -m venv .venv  ##create venv
- pip install install dependencies
- python init_database.py creates MySql database structure based on database.py
- first admin creation: python init_admincreator.py from command line, add admin username and pass, it automatically makes the new user and set admin.
- python init_fixdata creates fix elements in the db (organizations, node and app types etc.)
- you'll need to run startserver.py from a command line, it will start the three commandline threads.
- Import some users with "python mass_adduser.py" - which checks ./users/userlist.txt: username,is_netrunner,is_fixer,balance,org_id
  - this list can be extended, only new users will be added.
  - created users are written out to ./users_with_default_passwords.txt with an initial pw and citynet number to ensure they can log in
  - apps can be added in the format of 1:2;2:8;3:11 where the first ID is app type, second number separated by  : is the amount ot the given app, different apps separated by ;
- ...and/or create them on the admin page one by one
- flatline-citynet.fly.dev/admin/login
- flatline-citynet.fly.dev/user/login
- After all networks, apps, files, locks are created, admins should run python init_qrcreator.py to fill up the qrcode table with all accessible game elements.

# TODO
- DONE nodeusers table bejegyzések ne cserélődjenek, hanem updatelődjenek (és csak akkor amikor kell)
- node ID meg a többi változók session-be pakolása onnan ahol jók, majd a node user management szétszedése és változók sessionből olvasása.
- DONE greyic_entry_time session variable-t kiüríteni amikor már nem kell.
- node_user_management check, szétszedni lehet nem árt, elemzés, optimalizálás
- DONE Black IC-t végigtolni, minden funkció menjen
- FRONTEND fix: app used SSE üzenetek korrektül updateljék a node oldalak next node gombjait
- FRONTEND fix: home user password next node button működjön
- FRONTEND fix: támadó node-ok warning üzeneteit home user ne kapja meg
- FRONTEND fix: hálóba belépéskor ne legyen ottragadt üzenet
- White IC check
- Grey IC check
- Netrunner fight
- Node display csinosítás
- dead code kiirtás

# Known issues:

- "modify network" on admin page fails when attempting to modify a network which was ever visited by a user (constraints with node_user and node actions tables fail)

# Features missing for stable version

- Transfer apps (like files)
- Health status indicator: can be freely set by player, displayed on home page.
- Netrunner vs netrunner actions: Zap, Sword, Banhammer, Shield
- New board message notif on homepage
- Private message inbox structured by partners - not unlike fb messenger's home screen
- Separate "Profile/Social" (citynet number, add friend) and "Transfer" (account and files) pages
- Show hardware descriptions on market page
- If a market is empty, display it regardless, have it say "There are currently no listings available."
- Set up a consistent and responsive stylesheet, have it not break the scanner on mobile devices
- Can we catch "failed to open camera" error messages from the scanner? Suggesting closing all other camera-using apps to the user did the trick in most of these cases.

# Admin features
- Handle envelopes admin-side: Monitor (who has what and is it opened) Update (change contents), Create, Delete, Assign (to user)
- Scheduled market listing creator - it could be a command line tool which runs a thread which adds listings from a file
- Remove hardware listings from the admin page when they are shipped
- The ability to delete a market listing (could only do from database)
- Update multiple courier orders simultaneously
- Admin-side NPC messenger - the ability to see and reply to the messages of multiple NPCs in a single configurable view (user table maybe needs an is_npc field?)
- Assign organization membership from admin page (this was easy to do from db, but would be nice from admin page)
- Separate view to handle & create files from digital market
- The ability to add non-market files to QR

# Future ideas:

- player uploads app from inventory to QR?
- send file, send app -> inventory
- send money: dropdown target selector instead of buttons
- netrunner teamwork (send app helps maybe, but: calling in netrunners)
- app spawn / create / shop automate etc. -> solution to no app available
- Netrunning, node actions: more feedback
- DB schema redesign / refactor
- push notifications on new messages
- time zone handling for message timestamps - using local time instead of utc won't work as nearest app server is in different time zone
- sound notifs? 
- Better FB messenger like team chat?
- HTML5 + bootstrap + https://cdpn.io/gwannon/fullpage/LYjvOLK?anon=true&view=

Issue tracker:
https://docs.google.com/spreadsheets/d/12WjUhpWAUn0-rV8JngKCejgpuOY6ZAJ4443HmsGKBus/edit#gid=0
