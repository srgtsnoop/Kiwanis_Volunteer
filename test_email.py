# at top if not already imported
from flask import request, current_app
from flask_mail import Message

@app.route('/_test_mail')
def _test_mail():
    """
    Sends a simple test email. Usage:
      /_test_mail               -> sends to MAIL_USERNAME
      /_test_mail?to=someone@domain.com  -> sends to that address
    """
    to = request.args.get('to') or current_app.config.get('MAIL_USERNAME')
    if not to:
        return "No recipient resolved (set MAIL_USERNAME or pass ?to=...)", 400

    try:
        current_app.logger.info("Sending test email to %s", to)
        msg = Message(
            subject="Flask-Mail test ✅",
            recipients=[to],
            body="If you received this, your Flask-Mail + Gmail setup works!"
        )
        mail.send(msg)
        return f"Sent test email to {to}", 200
    except Exception as e:
        current_app.logger.exception("Mail test failed")
        return f"Mail failed: {e}", 500
