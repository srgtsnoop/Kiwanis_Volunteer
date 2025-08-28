from flask import current_app
from flask_mail import Message
# ... you already have: from models import db, User

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = (request.form.get('email') or '').strip().lower()

        # Always respond the same → no user enumeration
        flash('If that email exists, we’ve sent a reset link.', 'info')

        if email:
            user = User.query.filter_by(email=email).first()
            if user:
                try:
                    token = user.get_reset_token()  # uses your models.py helper
                    reset_url = url_for('reset_password', token=token, _external=True)
                    msg = Message(
                        subject="Reset your Kiwanis Volunteer password",
                        recipients=[email],
                        body=(
                            "We received a request to reset your password.\n\n"
                            f"Reset link (valid ~30 minutes): {reset_url}\n\n"
                            "If you didn’t request this, you can ignore this email."
                        ),
                    )
                    mail.send(msg)
                    current_app.logger.info("[FP] Reset email queued for %s", email)
                except Exception:
                    # Don’t leak details to user; log it for you
                    current_app.logger.exception("[FP] Error while sending reset email")
        # PRG pattern so POST returns 302 in your logs
        return redirect(url_for('forgot_password'))

    # GET
    return render_template('forgot_password.html')
