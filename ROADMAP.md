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

- install Flask-SQLAlchemy  ✅
- create an `Email` model  ✅
- add columns such as  ✅
    - id
    - sender
    - subject
    - snippet
    - priority
    - status
    - reason
    - gmail_thread_id
    - received_at
- create SQLite database file  ✅
- insert fake emails into database ✅
- load emails from SQLite instead of python list ✅
- update database rows when buttons are clicked ✅
- prevent the same email from being inserted twice ✅


## Phase 4 : Build the priority system using fake emails
Instead of manually inputting priority scores, 
we automate with python script

 - create `services/classifier.py` ✅
 - add a function: classify_email(email) ✅
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
 - test classifier with several fake emails ✅
 - display automatic score, status and reason on dashboard ✅


## Phase 5 : Create google login and Gmail access ✅
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

- Extract:  ✅
    - Sender
    - Recipients
    - Subject
    - Date
    - Snippet
    - Body
    - Message ID
    - Thread ID
- Decode encoded email bodies.  ✅
- Handle plain-text and HTML emails.  ✅
- Handle missing fields safely.  ✅
- Ignore attachments for now.  ✅
- Create an Open in Gmail link. ✅
- Save the cleaned email data in SQLite. ✅
- Prevent duplicate imports. ✅


## Phase 7 : Analyze conversations instead of isolated messages ✅
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
Organize imported emails better

- Build default `todo now` page that shows
  small actionable task the user should do first  ✅
- Move current full list of gmails to `all threads` page  ✅
- Add status tabs and counts for:  ✅
    - Needs Reply
    - Review
    - Waiting
    - Done
    - Ignored
- Add manual status correction ✅
- Add search ✅
- Add modular details page for each email if clicked on
    - add javascript to create route link and create route function
    - show both relative time and time in user's timezone

## Phase 9 : Add Thread Details Modal ✅

- make each thread card clickable
- Open a reusable modal without leaving the current page
- load the selected thread using its database ID
- show :
    - sender + recipients
    - subject
    - full newest message body
    - relative time
    - exact local time 
    - status
    - priority
    - classification reason
    - open in gmail link
- allow status changes inside modal 
- add close-button, background-click, and escape key behavior
- make modal work from all pages (todoNow, all_pages, filters and search)

## Phase 10 : Install and Integrate Small Ollama Model
- Install Ollama locally for development.
- Choose a small instruction model suitable for email classification.
- Test the model manually with sample emails.
- Create an Ollama service module in Flask.
- Send classification requests through Ollama’s local API.
- Request structured JSON containing:
    - Status
    - Priority
    - Reason
    - **Change original rule classifier before adding these** --> 
    - Requested action
    - Deadline
    - Confidence
- Validate every response before saving it.
- Fall back to the current rule classifier when Ollama fails.
- Keep deterministic thread logic, such as marking threads Waiting when the user sent the newest message.
- Classify only new or changed threads to avoid unnecessary model calls.

## Phase 11 : Improve classification quality 
- Build a small set of manually labeled test emails.
- Compare Ollama’s classifications against the expected results.
- Improve the prompt and examples.
- Test several small Ollama models.
- Select the smallest model that performs reliably.
- Remove quoted reply history and signatures before classification.
- Send only the newest message and limited thread context.
- Add onboarding questions about:
    - Important organizations or domains
    - Newsletters and promotions
    - Receipts and automated notifications
- Store user preferences locally.
- Apply preferences during classification.
- Save every manual status correction.
- Track frequently important or ignored senders and domains.
- Use corrections to adjust future classifications.
- Preserve manual choices until a new message arrives.

## Phase 12 : Improve visual design
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

# Phase 13 : Package MailFocus Locally

- Run Flask and Ollama together locally.
- Add Docker Compose for development and testing.
- Store model files in a persistent local volume.
- Download the selected model during first-time setup.
- Store Gmail tokens, settings, and email data locally.
- Create a launcher that starts MailFocus and opens the browser.
- Reduce or hide technical setup steps.
- Test installation on clean computers.
- Add uninstall and update instructions.

# Phase 14 : Create Public Website

- Explain what MailFocus does.
- Emphasize that Gmail data and AI processing remain local.
- List supported operating systems and hardware requirements.
- Provide the MailFocus download.
- Add installation instructions.
- Add screenshots and a demo video.
- Publish privacy and security information.
- Provide version history and update downloads.

# Phase 15 : Make Project Portfolio Ready 

- Organize the Flask app into clear modules.
- Remove secrets and real email data.
- Add logging and error handling.
- Add tests for:
    - Gmail parsing
    - Thread analysis
    - Ollama response validation
    - Classification fallback
    - User preferences
- Add a fake-data demo mode.
- Write a complete README.
- Document Google OAuth and Ollama setup.
- Confirm a fresh installation works.
- Record a project demonstration.
- Explain limitations and future plans.