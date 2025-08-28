from flask import current_app
from flask_mail import Message

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        if not email:
            flash('Please enter your email address.', 'warning')
            return redirect(url_for('forgot_password'))

        user = User.query.filter_by(email=email).first()
        if not user:
            flash('No user found with that email address.', 'danger')
            return redirect(url_for('forgot_password'))

        # User exists — build and send reset email
        try:
            token = user.get_reset_token()
            reset_url = url_for('reset_password', token=token, _external=True)
            msg = Message(
                subject='Password Reset Request',
                recipients=[email],
                body=f'''Hello {user.full_name},

To reset your password, click the link below:

{reset_url}

If you did not request a password reset, you can safely ignore this email.
'''
            )
            mail.send(msg)
            flash('A password reset link has been sent to your email.', 'info')
        except Exception:
            current_app.logger.exception('Error sending reset email')
            flash('We had trouble sending the email. Please try again later.', 'danger')

        return redirect(url_for('forgot_password'))

    return render_template('forgot_password.html')
