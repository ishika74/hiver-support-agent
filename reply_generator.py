from __future__ import annotations


def draft_reply(customer_text, intent, retrieved_examples, escalate):
    text = customer_text.lower()

    if intent == "PLAYBACK_TECH_ISSUE":
        reply = (
            "Sorry you’re having trouble with playback. Please check that "
            "your app is updated, restart the app, and try switching between "
            "Wi-Fi and mobile data. If the issue continues, please tell us "
            "your device model and app version so we can investigate further."
        )

    elif intent == "ACCOUNT_LOGIN":
        reply = (
            "Sorry you’re having trouble accessing your account. Please "
            "confirm that you’re using the correct login details and try "
            "resetting your password. If you still cannot sign in, please "
            "share the exact error message."
        )

    elif intent == "BILLING_SUBSCRIPTION":
        reply = (
            "Sorry about the billing issue. Please check your subscription "
            "status and payment method in your account settings. If you were "
            "charged incorrectly, please share the charge date and amount "
            "without posting any sensitive payment information."
        )

    elif intent == "HOW_TO_FEATURE_Q":
        reply = (
            "You can usually find this option in the app’s Settings menu. "
            "Please tell us which device you are using and the exact feature "
            "you want to change so we can provide the correct steps."
        )

    elif intent == "PRAISE_THANKS":
        reply = (
            "Thanks so much for your kind words! We’re glad we could help."
        )

    else:
        reply = (
            "Sorry you’re experiencing this issue. Please share a few more "
            "details about what happened, including your device and any "
            "error message, so our team can investigate."
        )

    if escalate:
        reply += (
            " We’re also escalating this to our support team for further "
            "assistance."
        )

    return reply