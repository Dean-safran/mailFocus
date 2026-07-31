from email.utils import parseaddr

from services.classifier import classify_email


def extract_email_address(sender):
    """Extract and normalize an address from a From header."""

    _, email_address = parseaddr(sender)

    return email_address.strip().lower()


def analyze_thread(normalized_thread, user_email):
    """
    Determine who most likely owes the next action
    in a normalized Gmail thread.
    """

    messages = normalized_thread.get("messages", [])

    if not messages:
        return {
            "status": "Review",
            "priority": 0,
            "reasons": "Thread contains no messages",
            "newest_message": None,
            "newest_sent_by_user": False,
        }

    newest_message = messages[-1]

    newest_sender = extract_email_address(
        newest_message.get("sender", "")
    )

    normalized_user_email = user_email.strip().lower()

    newest_sent_by_user = (
        newest_sender == normalized_user_email
    )

    if newest_sent_by_user:
        return {
            "status": "Waiting",
            "priority": 40,
            "reasons": (
                "You sent the newest message, so you may "
                "be waiting for the other person"
            ),
            "newest_message": newest_message,
            "newest_sent_by_user": True,
        }

    classification = classify_email(newest_message)

    return {
        "status": classification["status"],
        "priority": classification["priority"],
        "reasons": classification["reasons"],
        "newest_message": newest_message,
        "newest_sent_by_user": False,
    }