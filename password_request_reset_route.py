from flask import render_template, request, redirect, url_for, flash, current_app
from flask_mail import Message
from models import User
# import `mail` from wherever you initialize it
# from app import mail

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = (request.form.get('email') or '').strip().lower()
        current_app.logger.info("[FP] POST received. email=%r", email)

        if not email:
            flash('Please enter your email address.', 'warning')
            current_app.logger.info("[FP] Missing email -> flash+redirect")
            return redirect(url_for('forgot_password'))  # 302 expected in logs

        user = User.query.filter_by(email=email).first()
        if not user:
            flash('No user found with that email address.', 'danger')
            current_app.logger.info("[FP] Email not found in DB -> flash+redirect")
            return redirect(url_for('forgot_password'))  # 302 expected

        try:
            token = user.get_reset_token()
            reset_url = url_for('reset_password', token=token, _external=True)
            current_app.logger.info("[FP] User found id=%s; reset_url=%s", user.id, reset_url)

            msg = Message(
                subject='Password Reset Request',
                recipients=[email],
                body=(
                    f"Hello {user.full_name},\n\n"
                    f"To reset your password, open this link:\n{reset_url}\n\n"
                    "If you did not request a password reset, you can ignore this email."
                ),
            )
            current_app.logger.info("[FP] About to send email to %s; SUPPRESS_SEND=%s",
                                    email, current_app.config.get('MAIL_SUPPRESS_SEND'))
            mail.send(msg)
            current_app.logger.info("[FP] Email send() returned OK")

            flash('A password reset link has been sent to your email.', 'info')
        except Exception as e:
            current_app.logger.exception("[FP] Exception during mail send")
            flash('We had trouble sending the email. Please try again later.', 'danger')

        return redirect(url_for('forgot_password'))  # 302 expected

    # GET
    return render_template('forgot_password.html')
