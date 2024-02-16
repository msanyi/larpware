1. **HomePage (index.html)**
    - Display:
        - Street handle and CityNet Number
        - Current account balance
        - Notifications for unread messages and events
        - (Netrunner only) Current position in the NET (Architecture + Node)
    - Links to:
        - Private messaging
        - Bulletin boards
        - Friend list
        - Bank account
        - Digital inventory
        - The Digital Market
        - Netrunning (Netrunner only)
        - State tracker (Extended scope)
        
2. **Private Messaging (messages.html)**
Always visible:
   - small letter notification on the top of the page about the number of unread messages, if the number is bigger than 0, the number should be red, text example: "5 unread messages"
   
   Buttons under the unread messages text:
   - send message
   - messages history
   - unread messages 
   Clicking on these buttons reveals hidden parts of this html page.

   After clicked on sending message button (messages history, unread messages sections become hidden):
   - friend list: put this too into a fixed height 8 rows scrollable list in alphabetic order, clicking one name selects it for sending
   - select friend to send message: a clicked friend's name appears in top of the message composer input field
   - input field to compose the message: 1 row height text input field
   - send button


   After user clicked unread messages button, this section reveals, send message, messages history sections become hidden
   - first 30 characters (followed by a "..." if the message is longer and truncated) as links of the unread messages
   - clicking on an unread message opens it on the same html page, and allows answering it (input field, send button)

   Messages history button reveals this section, hiding others (send message, unread messages)
   - list of users who already sent or received message to/from current user - as link, clicking on it opens a full list still on the same page of messages in order of creation and focusing on the latest message, a small read / unread note added after current user's last message. 
   - This message list should be on a fixed height scrollable field, with the option of the answer under it, input field, send button. 
   - html and javascript for this client side page. use included scripts.js, Ajax?
           
3. **Bulletin Boards (boards.html)**
    - Display:
        - List of available Bulletin Boards and unread message count
        - Individual messages in each board
    - Input fields:
        - Message input field (to post on the board)
        
4. **Friend List (friends.html)**
    - Display:
        - List of friends' CityNet Numbers and Street Handles
    - Buttons:
        - Delete friend
        - Send Message
        
5. **Bank Account (account.html)**
    - Display:
        - Current balance
        - Transaction history
    - Input fields:
        - CityNet Number input field (for transactions)
        - Transaction amount input field
        - Transaction message input field
        
6. **Digital Inventory (inventory.html)**
    - Display:
        - List of digital items (Files and Apps)
    - Buttons:
        - Transfer
        - Delete
        - Open
        - Run
        
7. **The Digital Market (market.html)**
    - Display:
        - List of available items (with price and description)
    - Buttons:
        - Purchase
        
8. **Netrunning (netrunning.html) - Accessible only by Netrunners**
    - Display:
        - Current position in NET Architecture
        - List of available Apps and their description
    - Buttons:
        - Run App
        - Progress to next node
        - Return to previous node
        
9. **State Tracker (tracker.html) - Extended scope**
    - Display:
        - Current state
    - Buttons:
        - Update state

## HTML Structure Schematic:

```
home.html
│
├── messages.html
│
├── boards.html
│
├── friends.html
│
├── account.html
│
├── inventory.html
│
├── market.html
│
└── netrunning.html (Netrunners only)
    │
    └── tracker.html (Extended scope)
```

Each subpage can link back to the home page.