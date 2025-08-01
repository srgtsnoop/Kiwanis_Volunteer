from flask_mail import Message, Mail

mail = Mail(app)

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user:
            token = user.get_reset_token()
            reset_url = url_for('reset_password', token=token, _external=True)
            msg = Message('Password Reset Request', recipients=[email])
            msg.body = f'''To reset your password, visit the following link:
{reset_url}

If you did not make this request, simply ignore this email.
'''
            mail.send(msg)
            flash('A password reset link has been sent to your email.', 'info')
        else:
            flash('No user found with that email address.', 'danger')
        return redirect(url_for('forgot_password'))
    return render_template('forgot_password.html')

