@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.verify_reset_token(token)
    if not user:
        flash('That is an invalid or expired reset link.', 'danger')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        pw = request.form.get('password', '').strip()
        if not pw:
            flash('Please enter a new password.', 'warning')
            return redirect(url_for('reset_password', token=token))
        user.set_password(pw)
        db.session.commit()
        flash('Your password has been reset! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('reset_password.html', token=token)
