from services.classifier import classify_email

fake_emails = [
    {
        "sender": "Professor Smith",
        "subject": "Project results",
        "snippet": "Could you send me your results before Friday?",
        "is_unread": True,
    },
    {
        "sender": "newsletter@example.com",
        "subject": "Weekly newsletter",
        "snippet": "Read this week's news. Unsubscribe here.",
        "is_unread": True,
    },
    {
        "sender": "noreply@store.com",
        "subject": "20% off today",
        "snippet": "Limited-time sale. Shop now.",
        "is_unread": False,
    },
    {
        "sender": "orders@store.com",
        "subject": "Order confirmation",
        "snippet": "Your order has been received.",
        "is_unread": True,
    },
]

for email in fake_emails :
    result = classify_email(email)

    print("Priority:", result["priority"])
    print("Status:", result["status"])
    print("Reason:", result["reasons"])
    print("=" * 40)