# Cyberpunk LarpWare Specification

## Notes on scope
This specification includes two scope levels, differentiated by the **Extended scope** note. Extended scope features are those which are not required for the game to work, but are nice improvements on overall functionality.

## Glossary

- **Agent:** The device you use the application from
- **Net or CityNet:** The application itself.
- **Street handle:** The name other cyberpunks know your character by, also your username.
- **Eurodollars or €$:** The currency in the game
- **Architecture or NET Architecture**: Internal networks of various factions to be hacked by Netrunners.
- **Node:** A single location inside an Architecture.
- **Digital Inventory:** Things on your Agent, which can be either Files or Apps.
- **Files:** Things in your Digital Inventory you can read.
- **Apps:** Things in your Digital Inventory you can run for some in-game effects. Each App can only be run once. Some Apps can only be run by Netrunners.

## Users

### Creating users

Users are created by the **administrator**. It should be possible to bulk create users from an export made from the event's registration engine, exact format is up to discussion (JSON?).
The registration engine provides the following information for a user:
- Street handle: This is the username in the system, also displayed in messaging.
- Password: The initial password the user can log in with.
- Organization memberships: A list of organization flags the user has initially.
- Is the user a Netrunner? Yes/No; This provides access to the Netrunning and the Darkweb Market subsystem.
- Is the user a Fixer? Yes/No; This provides access to the Fixer Contacts subsystem.

When a  user is created, a random unique 7-digit number is generated and assigned to the user. This is their **CityNet Number** which can be used in the banking, inventory and messaging subsystems.

### Logging in
The user logs in using the street handle and password received from the administrator.

### Organization memberships
The user can be a member of one or more organizations. An organization membership can have a set time when it ends - this is used to assign temporary memberships. Memberships assigned at user creation never time out.

### Bank account
The user's digital account of Eurodollars, or €$ for short. It is an integer value. You can **Transfer** an amount of €$ to another user, provided you have the funds for it. You can attach a short message to a transaction. You can view your transaction history, with the CityNet Number of the sending/receiving side, the amount and the attached message.

### Digital inventory
The user's digital inventory represents in-game files on their device. You can do the following things with items in your Digital Inventory:
- **Transfer:** Give it to another user, identified by their CityNet Number. You can attach a message to the transfer.
- **Delete:** Removes the item from your inventory.
- **Open:** Read the contents of a File.
- **Run:** The App does its thing, then deletes itself - it was specialized to a single system and now that the defense measures have adapted to it, it is no longer useful. There are some Apps only Netrunners can Run.

This also means that items in your digital inventory are either **Files** or **Apps**. Files have a name and a text content, while Apps only have a Class - what type of App it is. Anyone can have any App on their devices, but most classes of Apps can only be run by Netrunners jacked into an Architecture. Files can be encrypted, in which case a password is required to Open them. You can use a Decrypt app to Open an encrypted file once, but it will not "stay open".

### State tracker

**Extended scope** Provides the player with a way to track their Wound State (UNHURT - WOUNDED - DYING - DEAD). It is not expected to track these real-time in-app, it's just a helper to sum things up after combat, so the view is just a big dropdown and two numbers with plus/minus steps.
(**CUT from scope:** Armor and Reflex values longterm)

**Extended scope** Provides a kind of "bleedout timer" in the DYING state.

### Friend list

You can send friend request to a CityNet Number. If they accept the request, you learn their Street Handle, and it is displayed in addition to their CityNet Number in the views where the number appears.

You can view your friend list, initiate private messaging from that view, and delete contacts.  If you delete a contact, the friendship is lost on the other side as well.

## Basic functionality

### Home screen

The home screen of the frontend application displays the following after logging in:
- Your street handle and CityNet Number
- Your current account balance
- A notification with the number of your unread messages
- A notification with events (received items or money, friend requests) you did not see yet
- (Netrunner only) where exactly are you in the NET (Architecture + Node)

### Private messaging

The messaging screen displays a list of your conversations. Each list item displays the following:
- The name of the partner
- Time of the last message
- A piece of the last message.
If you have unread messages in a conversation, it is highlighted.

Clicking on a conversation opens it up, with some way of paging long conversations. You can **send** a message in this conversation view.

You can also initiate a conversation from the messaging screen if you know the CityNet Number of the recipient.

### Bulletin boards

There are a number of available Bulletin Boards in the Net:
- Newsfeed: Everyone can read but only members of the "Media" organization can post
- Public: Everyone can read and post
- Secure: Every organization has a secure board. Only members can read or post.
- Darkweb: Only Netrunners can read or post.

In the list view you can see the bulletin boards available to you and how many new messages it has since your last visit. Opening a bulletin board lets you see the messages and allows you to post.

### Permission check - QR codes

There should be a unique URL endpoint for every organization, which, when opened, returns ACCESS GRANTED if the user logged in is a member of the organization, and ACCESS DENIED if not. These endpoints are later loaded into QR codes via external app and used for in-game locks.

### Item QR codes

Admins are able to maintain a list of Item Codes, and assign either a Digital Inventory item (files or apps) or an amount of €$ to them. 

Each Item Code has a URL endpoint assigned, which, when opened, behaves depending on the current user:
- If the user is an admin, it routes them to the edit view of that Item Code.
- If the user is not an admin, it displays the contents of the item code, and prompts them to add it to their digital inventory. This clears the contents of the item code, leaving it empty.

Item Code URLs are printed via an external app into QR codes and put on various in-game items. This method makes them reusable when they are returned to the org room.

### Apps everyone can Run

Every App can only be Run once, then it deletes itself. These apps are usually more expensive than Netrunner apps, as those require specialized knowledge to use.

- **Decrypt:** Open an encrypted file.
- **Lockpick:** Each Lockpick is keyed to a specific organization and counts as a separate App. When you Run a Lockpick, it grants you membership in that organization for 10 minutes.

## The Digital Market

The Digital Market has three variants, all of them working the same way: the admin can add items with a set price, and players with access to that market can purchase it with the €$ in their account. Each Digital Market listing can only be purchased once, then it is removed from the shop.

Items in store can either be Apps or Files, which appear in the buyer's digital inventory, or physical game items which are delivered by an NPC courier to the Night Market. This also means that the admin interface requires some kind of "courier task list", which lists the items yet to be delivered, and giving the ability to mark these deliveries as completed, removing them from the list.

**Extended scope:** When adding an item for the shop, the admin can also set the number of items available. This creates a number of separate instances of the listing equal to the set number.

**Extended scope:** Faction-specific availability. When adding an item for the shop, the admin can restrict the item's availability to specific factions (default is all), and it will not appear to anyone outside of that faction.

**Extended scope:** Faction-specific discount. When adding an item for the shop, the admin can define faction-specific price overrides. An override consists of the factions it exists for, and the overridden price value. The price displayed for a specific user is equal to the price of the first override rule that is valid for the user - if none of those exist, the user sees the item for the default price.

### Public Listings

This is the one that is available to every user. It sells mostly various Apps, sometimes files.

### Fixer Contacts

This is only available to Fixer characters. The Fixer Contacts shop is the primary source for physical in-game items to supply shopkeeper-type characters.

### Darkweb Market

This is only available to Netrunners, selling mostly Netrunner-specific Apps. 

## Netrunning

### Netrunner-exclusive Apps

These are the Apps only Netrunners can Run. Every App can only be Run once, then it deletes itself. All apps target the current Node the netrunner it is at - or, in case of some apps, a Netrunner who is at the same Node (targeting other Netrunners is **extended scope**).

- **Backdoor:** Cracks a Password node.
- **Cloak:** Automatically cancels a Program or IC which would reveal your identity.
- **Tracer:** Reveals the identity (Street Handle and CityNet Number) and location of other Netrunners in the same architecture. 
- **Siphon:** When used at an Account Info node, selects a random member of the faction that owns the Architecture and moves a random percentage between 10-30% of their bank account to an account you specifiy.
- **Crawler:** Pulls a random piece of data from an Intel node.
- **Sword:** Attacker program (Necessary to neutralize IC). Extended scope:  When directed at another Netrunner, deletes one random App of theirs.
- **Shield:** A defender program (Necessary to completely neutralize Black IC). Extended scope: If an attacker program is directed at you, one of your Shield programs runs automatically and negates it.
- **Banhammer:** Attacker program (Necessary to neutralize IC). Extended scope: When directed at another Netrunner, forcibly ejects them from the Architecture, making them have to log in again.
- **Zap:** Attacker program (Necessary to neutralize IC). Extended scope: When directed at another Netrunner, they become WOUNDED.
- **Restore:** Used at a cracked node, it restores the node to full functionality.
- **Firewall:** Cracks Account Info or Intel node without any other effect, rendering it unusable to other Netrunners until it regenerates. This is the only way you can make a Node of your own faction Cracked.
- **Sweep:** Clears any temporary membership flags from the faction that owns the architecture.
- **Trojan:** When used at the deepest level of an Architecture, flags you or a player device you select as the member of that same faction which owns the Architecture for a random number of hours between 2-4.
- **Scrub** Removes copier name from a copied document


### Anatomy of a NET Architecture

A NET Architecture consists of a name, an owning faction and a number of Nodes connected in a linear topology, with the Access Point landing the Netrunner on the topmost node. A Netrunner can either proceed to the next node, or return to the previous one.

Each Node has a Type, which tells what exactly is in it - either an obstacle, or some kind of loot. Some effects can "crack" a Node: a cracked node is rendered nonfunctional, losing all of its special effects, behaving like a "Blank" node. A cracked node automatically restores itself after 1 hour or when a Restore program is run on it.

(**CUT from scope:** Architectures can have a tree topology, allowing branching paths of progress to happen.)

### Access Points and Jacking In

Every Architecture has a unique Access Point link, which points to its topmost node. Access Point links are generated into a QR code via a third party app. A Netrunner can enter an Architecture via an Access Point link.

A Netrunner can only be in one architecture at a time, and also in only a single node. Node transitions are only valid if they are one of the following:
- **Backtrack:** Return to the previous node.
- **Progress:** Enter the next node, provided there is no node effect blocking it.
- **Jack out:** Leave the architecture altogether.
- **Jack in:** Enter an architecture at its topmost node via Access Point link.

Direct links to any other non-connected non-topmost nodes are unauthorized transitions.

When you are in a Node, you see the following things:
- What type of Node it is
- Is it cracked or not
- Are you able to progress
- Who are the other Netrunners here (CityNet Number only)
- If the Node has a timed countermeasure, the remaining time until it triggers automatically unless you neutralize it or leave.

### Multiple Netrunners in the same Architecture

Interaction of multiple Netrunners in the same Architecture.
The Apps **Sword**, **Banhammer** and **Zap** can be used to target Netrunners in the same Node. Running these apps successfully delivers a notification to the target Netrunner. The app Zap which makes the Netrunner WOUNDED is an effect outside of the application - it is a regular game mechanics feature.

### Types of Nodes

- **Password:** Asks you for the password. If you don't know the password, you cannot pass to the next Node. Can be cracked with Backdoor.
- **White IC:** If you proceed to the next Node and you are not in the same faction that owns the Architecture, it sends a message with your identity information to the faction's bulletingn board. The message is cancelled by Cloak, and the IC can be neutralized by any kind of Attacker program, cracking the Node.
- **Grey IC:** If you are not in the same faction that owns the Architecture, you are unable to proceed. Furthermore, if you do not use an Attacker program within 2 minutes of entering the Node, it deletes a random App of yours. Using the program cracks the Node.
- **Black IC:** If you are not in the same faction that owns the Architecture, and proceed to the next Node or spend more than 2 minutes in this Node, you become DYING. Using an Attacker AND a Defender program within 2 minutes of entering the Node cracks it. Using one of those programs makes you WOUNDED instead of DYING when proceeding or 2 minutes being up (whichever comes first).
- **Account Info:** You can crack this Node by using a Siphon app.
- **Intel:** You can use a Crawler at this node, letting you add a random file attached to this Node to your app inventory. The file is not removed from the Node.
- **Blank:** This Node has no special effect.
- **Area:** Users can enter this node for protection.



