# The Complete Roadmap

## Phase 1: Build fake dashboard
Purpose: Learn how python produces webpages before introducing Gmail or databases

- create Flask app ✅
- create dashboard.html ✅
- store fake emails in python list ✅
- pass list from Flask to Jinja ✅
- display every email ✅
- sort emails by priority ✅
- give each fake email a unique ID ✅
- display status for each email ✅
- add simple buttons ✅


## Phase 2 : Make fake dashboard interactive ✅
- add **mark done** form
    - changes an email from `needs reply` to `done`
- create flask route that receives the email ID
- find matching email
- change its status
- redirect back to dashboard
- add buttons for waiting and ignore



## Phase 3 : Save information in a database
When a user marks a message done, if we restart,
it stays done

- install Flask-SQLAlchemy
- create an `Email` model
- add columns such as 
    - id
    - sender
    - subject
    - snippet
    - priority
    - status
    - reason
    - gmail_thread_id
    - received_at
- create SQLite database file
- insert fake emails into database
- load emails from SQLite instead of python list
- update database rows when buttons are clicked
- prevent the same email from being inserted twice


## Phase 4 : Build the priority system using fake emails
Instead of manually inputting priority scores, 
we automate with python script

 - create `services/classifier.py`
 - add a function: classify_email(email)
 - increase priority for:
    - Questions
    - Direct requests
    - Deadlines
    - unread emails
 - decrease priority for
    - `no reply` senders
    - newsletters
    - promotions
    - receipts
    - automated notifications
 - return 
    - priority score
    - suggested status
    - explanation
 - test classifier with several fake emails
 - display automatic score, status and reason on dashboard


## Phase 5 : Create google login and Gmail access
We start to connect with google to replace 
fake messages with real messages

- Create a Google Cloud project.
- Enable the Gmail API.
- Configure the OAuth consent screen.
- Add yourself as a test user.
- Create OAuth credentials for a web app.
- Download the credentials file.
- Add credentials and tokens to .gitignore.
- Add a Connect Gmail button.
- Redirect the user to Google login.
- Request read-only Gmail permission.
- Handle the OAuth callback.
- Save the login token locally.
- Fetch one Gmail message.
- Print its subject in the terminal.
- Fetch ten recent messages.
- Display them on the dashboard.

## Phase 6 : Convert Gmail data into our app's format
Google's API response will not be a neat dictionary 
like our fake emails, we need to transform them

- Extract:
    - Sender
    - Recipients
    - Subject
    - Date
    - Snippet
    - Body
    - Message ID
    - Thread ID
- Decode encoded email bodies.
- Handle plain-text and HTML emails.
- Handle missing fields safely.
- Ignore attachments for now.
- Create an Open in Gmail link.
- Save the cleaned email data in SQLite.
- Prevent duplicate imports.


## Phase 7 : Analyze conversations instead of isolated messages
*Our unique, central feature*
An email might appear to need a reply when we already replied,
an email unit should be a **conversation**, not an isolated email,
our dashboard understands who currently owes next action

- fetch every email in a gmail thread 
- sort the messages by date 
- Identify the newest message.
- Determine whether you sent the newest message.
- Mark the thread Needs Reply when another person is waiting on you.
- Mark the thread Waiting when you sent the newest message.
- Detect questions and direct requests in the newest external message.
- Avoid prioritizing questions you already answered.
- Display one dashboard item per thread instead of per message.

## Phase 8 : Create the real task dashboard
Organize imported emails instead of 
just being an inbox copy with metadata

- Add filters for:
    - Needs Reply
    - Review
    - Waiting
    - Done
    - Ignored
- Add totals for each status.
- Sort threads by priority.
- Show the classification reason.
- Show how long ago the email arrived.
- Include Sync Gmail button.
- Add search.
- Add sender filters.
- Add an email detail page.
- Add an Open in Gmail button.
- Let users manually change classifications.


## Phase 9 : Learn from user corrections
If the user changes an email from `needs reply` to
`ignore`, our app should remember that correction

- Store whether a classification was automatic or manual.
- Save every manual correction.
- Track senders frequently marked important.
- Track senders frequently ignored.
- Increase scores for important senders.
- Decrease scores for ignored senders.
- Create a sender-preferences database table.
- Apply sender preferences during classification.

## Phase 10  : Add AI analysis
Improve uncertain classifications

- Use AI only when rule-based confidence is low.
- Remove quoted reply history before sending email text.
- Send only the minimum necessary email content.
- Request structured JSON.
- Extract:
    - Whether a reply is needed
    - Requested action
    - Deadline
    - Priority
    - Status
    - Short explanation
- Validate the AI response before saving it.
- Fall back to rules when the AI call fails.
- Label AI-generated results clearly.
- Avoid sending unnecessary sensitive information.


## Phase 11 : Improve visual design
Use bootstrap and more CSS to make things pretty

- Add a CSS file or Bootstrap.
- Create a sidebar or top navigation.
- Display emails as cards.
- Add priority badges.
- Style buttons consistently.
- Add mobile-friendly layouts.
- Add empty-state messages.
- Add loading messages.
- Add clear error messages.
- Improve spacing, fonts, and readability.

## Phase 12 :  Make project portfolio ready
Someone reviewing our GitHub can understand, 
install, and run the project

- Organize files into clear folders.
- Remove all secrets and real email data.
- Add error handling.
- Add classifier tests.
- Add database tests where useful.
- Create a complete README.md.
- Include installation instructions.
- Include Google API setup instructions.
- Add screenshots.
- Add a fake-data demo mode.
- Deploy the Flask app.
- Record a short demo video.
- Explain privacy limitations.
- Confirm credentials are not in GitHub.
- Confirm the app works from a fresh installation.