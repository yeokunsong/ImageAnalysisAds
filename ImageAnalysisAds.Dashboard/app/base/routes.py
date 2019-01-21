from flask import render_template, redirect, request, url_for
from flask_login import (
    current_user,
    login_required,
    login_user,
    logout_user
)
from .forms import LoginForm, CreateAccountForm

from app import db, login_manager
from app.base import blueprint
from app.base.models import User
from validate_email import validate_email

@blueprint.route('/')
def route_default():
    return redirect(url_for('base_blueprint.login'))


@blueprint.route('/<template>')
@login_required
def route_template(template):
    return render_template(template + '.html')


@blueprint.route('/fixed_<template>')
@login_required
def route_fixed_template(template):
    return render_template('fixed/fixed_{}.html'.format(template))


@blueprint.route('/page_<error>')
def route_errors(error):
    return render_template('errors/page_{}.html'.format(error))

## Login & Registration

@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm(request.form)
    create_account_form = CreateAccountForm(request.form)
    if 'login' in request.form:
        username = str(request.form['username'])
        password = str(request.form['password'])
        user = User.query.filter_by(username=username).first()
        if user and password == user.password:
            login_user(user)
            return redirect(url_for('base_blueprint.route_default'))
        return render_template('errors/page_403.html')
    elif 'create_account' in request.form:
        login_form = LoginForm(request.form)
        user = User(**request.form)
        if user.username == '' or user.email == '' or user.password == '':
            return render_template('errors/page_register.html', error_msg = 'Username/Email/Password cannot be empty.')

        is_username_exsiting = User.query.filter_by(username=user.username).first()
        is_email_existing = User.query.filter_by(email=user.email).first()
        if is_username_exsiting or is_email_existing:
            return render_template('errors/page_register.html', error_msg = 'Username/Email is already existing.')
        
        is_email_valid = validate_email(user.email)
        if not is_email_valid:
            return render_template('errors/page_register.html', error_msg = 'Email is not valid.')

        db.session.add(user)
        db.session.commit()
        return redirect(url_for('base_blueprint.login'))
    if not current_user.is_authenticated:
        return render_template(
            'login/login.html',
            login_form=login_form,
            create_account_form=create_account_form
        )
    return redirect(url_for('home_blueprint.image_process'))


@blueprint.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('base_blueprint.login'))


@blueprint.route('/shutdown')
def shutdown():
    func = request.environ.get('server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the server')
    func()
    return 'Server shutting down...'

## Errors


@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template('errors/page_403.html'), 403


@blueprint.errorhandler(403)
def access_forbidden(error):
    return render_template('errors/page_403.html'), 403


@blueprint.errorhandler(404)
def not_found_error(error):
    return render_template('errors/page_404.html'), 404


@blueprint.errorhandler(500)
def internal_error(error):
    return render_template('errors/page_500.html'), 500
