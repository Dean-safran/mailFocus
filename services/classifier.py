def classify_email(email) :
    score = 20
    reasons = []

    sender = email["sender"].lower()
    subject = email["subject"].lower()
    snippet = email["snippet"].lower()

    text = f"{sender} {subject} {snippet}"

    # Increase priority for questions
    if "?" in text :
        score += 25
        reasons.append("Contains a question")
    
    # Increase priority for direct requests
    request_phrases = [
        "could you",
        "can you",
        "send",
        "submit",
        "let me know",
        "need you to"
        "fill out"
        "ask"
        "where is"
    ]

    if any(phrase in text for phrase in request_phrases) :
        score += 25
        reasons.append("Contains a direct request")

    # Increase priority for deadlines
    deadline_phrases = [
        "deadline",
        "due",
        "by monday",
        "by tuesday",
        "by wednesday",
        "by thursday",
        "by friday",
        "by tomorrow",
        "before monday",
        "before tuesday",
        "before wednesday",
        "before thursday",
        "before friday",
        "meet tomorrow",
        "meet monday",
        "meet tuesday",
        "meet wednesday",
        "meet thursday",
        "meet friday",
    ]

    if any(phrase in text for phrase in deadline_phrases) :
        score += 25
        reasons.append("Contains possible deadline")

    # Increase priority for unread emails
    if email.get("is_unread", False) :
        score += 10
        reasons.append("Email is unread")

    # Decrease priority for no reply senders
    noreply_terms = [
        "noreply",
        "no-reply",
        "no reply"
        "not reply"
        "cannot reply"
    ]

    if (any(phrase in text for phrase in noreply_terms) or
        "no" in text and "reply" in text) :
        score -= 20
        reasons.append("Email had do not reply")

    # Decrease priority for newsletters
    if "newsletter" in text or "unsubscribe" in text :
        score -= 40
        reasons.append("Appeared to be newsletter")

    # Decrease priority for promotions
    promotion_phrases = [
        "sale",
        "discount",
        "% off",
        "shop now",
        "limited-time offer"
    ]

    if any(phrase in text for phrase in promotion_phrases):
        score -= 25
        reasons.append("Appears to be promotional")

    # Decrease priority for receipts
    receipt_phrases = [
        "receipt",
        "order confirmation",
        "payment confirmation",
        "your order",
    ]

    if any(phrase in text for phrase in receipt_phrases):
        score -= 20
        reasons.append("Appears to be a receipt or confirmation")

    # Decrease priority for automated notifications
    automated_phrases = [
        "automated notification",
        "automatically generated",
        "notification only",
    ]

    if any(phrase in text for phrase in automated_phrases):
        score -= 20
        reasons.append("Appears to be an automated notification")

    # keep score between 0 and 100
    score = max(0,min(100, score))

    if score >= 70 :
        status = "Needs Reply"
    elif score >= 40 :
        status = "Review"
    else :
        status = "No Action"

    if reasons :
        explanation = "; ".join(reasons)
    else :
        explanation = "No priority signals detected"

    return {
        "priority": score,
        "status": status,
        "reasons": explanation
    }