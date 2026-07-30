import base64
from datetime import datetime, timezone
from email.utils import getaddresses, parsedate_to_datetime
from html.parser import HTMLParser
from html import unescape


class HTMLTextExtractor(HTMLParser):
    """Collect visible text from a basic HTML email."""

    def __init__(self):
        super().__init__()
        self.text_parts = []

    def handle_data(self, data):
        cleaned_data = data.strip()

        if cleaned_data:
            self.text_parts.append(cleaned_data)

    def get_text(self):
        return " ".join(self.text_parts)


def html_to_text(html_body):
    """Remove HTML tags while keeping visible text."""

    parser = HTMLTextExtractor()
    parser.feed(html_body)

    return parser.get_text()


def get_message_header(headers, header_name, default_value=""):
    """Find one header in Gmail's list of header dictionaries."""

    for header in headers:
        current_name = header.get("name", "")

        if current_name.lower() == header_name.lower():
            return header.get("value", default_value)

    return default_value


def decode_base64url(data):
    """Decode Gmail's base64url-encoded body text."""

    if not data:
        return ""

    padding = "=" * (-len(data) % 4)
    padded_data = data + padding

    decoded_bytes = base64.urlsafe_b64decode(padded_data)

    return decoded_bytes.decode(
        "utf-8",
        errors="replace",
    )


def collect_body_parts(part, plain_text_parts, html_parts):
    """Recursively search a Gmail MIME part for readable body text."""

    # A nonempty filename normally indicates an attachment.
    if part.get("filename"):
        return

    mime_type = part.get("mimeType", "")
    body = part.get("body", {})
    encoded_data = body.get("data")

    if encoded_data:
        decoded_data = decode_base64url(encoded_data)

        if mime_type == "text/plain":
            plain_text_parts.append(decoded_data)

        elif mime_type == "text/html":
            html_parts.append(decoded_data)

    # A part can contain more nested parts.
    for child_part in part.get("parts", []):
        collect_body_parts(
            child_part,
            plain_text_parts,
            html_parts,
        )


def extract_message_body(payload):
    """Prefer plain text, but use cleaned HTML as a fallback."""

    plain_text_parts = []
    html_parts = []

    collect_body_parts(
        payload,
        plain_text_parts,
        html_parts,
    )

    if plain_text_parts:
        nonempty_parts = [
            part.strip()
            for part in plain_text_parts
            if part.strip()
        ]

        return "\n\n".join(nonempty_parts)

    if html_parts:
        combined_html = "\n".join(html_parts)

        return html_to_text(combined_html)

    return ""


def extract_recipients(headers):
    """Extract email addresses from the To and Cc headers."""

    to_header = get_message_header(headers, "To")
    cc_header = get_message_header(headers, "Cc")

    recipient_headers = [
        header
        for header in [to_header, cc_header]
        if header
    ]

    parsed_recipients = getaddresses(recipient_headers)

    return [
        address
        for _, address in parsed_recipients
        if address
    ]


def parse_received_at(message, headers):
    """Parse the Date header, with Gmail's internal date as a fallback."""

    date_header = get_message_header(headers, "Date")

    if date_header:
        try:
            parsed_date = parsedate_to_datetime(date_header)

            # tzinfo = time zone information
            if parsed_date.tzinfo is not None:
                parsed_date = (
                    parsed_date
                    .astimezone(timezone.utc)
                    .replace(tzinfo=None)
                )

            return parsed_date

        except (TypeError, ValueError, OverflowError):
            pass

    internal_date = message.get("internalDate")

    if internal_date:
        # internal date is in ms, convert to s
        timestamp_seconds = int(internal_date) / 1000

        return datetime.fromtimestamp(
            timestamp_seconds,
            tz=timezone.utc,
        ).replace(tzinfo=None)

    return None


def normalize_gmail_message(message):
    """Convert a Gmail API message into MailFocus's simpler format."""

    payload = message.get("payload") or {}
    headers = payload.get("headers", [])

    return {
        "gmail_message_id": message.get("id", ""),
        "gmail_thread_id": message.get("threadId", ""),
        "sender": get_message_header(
            headers,
            "From",
            "(Unknown sender)",
        ),
        "recipients": extract_recipients(headers),
        "subject": get_message_header(
            headers,
            "Subject",
            "(No subject)",
        ),
        "received_at": parse_received_at(
            message,
            headers,
        ),
        "snippet": unescape(message.get("snippet", "")),
        "body": extract_message_body(payload),
        "is_unread": "UNREAD" in message.get(
            "labelIds",
            [],
        ),
    }