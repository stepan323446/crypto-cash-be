from celery import shared_task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from project.settings import (
    EMAIL_HOST_USER,
    FRONTEND_ACTIVATE_USER_TEMPLATE,
    FRONTEND_RESET_PASS_TEMPLATE,
    FRONTEND_CONFIRM_CHANGE_EMAIL_TEMPLATE
)

@shared_task
def activation_email(user_username: str, user_email: str, activation_token):
    subject = 'Activate your CryptoCash account'
    from_email = EMAIL_HOST_USER
    
    url = FRONTEND_ACTIVATE_USER_TEMPLATE.format(token=activation_token)
    context = {'activation_url': url, 'username': user_username}
    html_content = render_to_string('users/mail_activation.html', context)
    
    text_content = strip_tags(html_content)

    msg = EmailMultiAlternatives(subject, text_content, from_email, [user_email])
    msg.attach_alternative(html_content, "text/html")
    
    msg.send()

@shared_task
def forgot_pass_email(user_username: str, user_email: str, reset_token):
    subject = 'Reset password'
    from_email = EMAIL_HOST_USER
    
    url = FRONTEND_RESET_PASS_TEMPLATE.format(token=reset_token)
    context = {'reset_url': url, 'username': user_username}
    html_content = render_to_string('users/mail_reset_password.html', context)
    
    text_content = strip_tags(html_content)

    msg = EmailMultiAlternatives(subject, text_content, from_email, [user_email])
    msg.attach_alternative(html_content, "text/html")
    
    msg.send()

@shared_task
def change_new_email(user_username: str, new_user_email: str, confirmation_token: str):
    subject = 'Confirm Your New Email Address'
    from_email = EMAIL_HOST_USER
    
    url = FRONTEND_CONFIRM_CHANGE_EMAIL_TEMPLATE.format(token=confirmation_token)
    context = {'username': user_username, 'confirmation_url': url}
    html_content = render_to_string('users/mail_change_email.html', context)
    
    text_content = strip_tags(html_content)

    msg = EmailMultiAlternatives(subject, text_content, from_email, [new_user_email])
    msg.attach_alternative(html_content, "text/html")
    
    msg.send()

@shared_task
def reset_pass_email_completed(user_username: str, user_email: str):
    subject = 'Reset password completed'
    from_email = EMAIL_HOST_USER
    
    context = {'username': user_username}
    html_content = render_to_string('users/mail_reset_password_completed.html', context)
    
    text_content = strip_tags(html_content)

    msg = EmailMultiAlternatives(subject, text_content, from_email, [user_email])
    msg.attach_alternative(html_content, "text/html")
    
    msg.send()

@shared_task
def authorization_email(user_username: str, user_email: str, code: str):
    subject = 'Log in using e-mail address'
    from_email = EMAIL_HOST_USER
    
    context = {'code': code, 'username': user_username}
    html_content = render_to_string('users/mail_authorization.html', context)
    
    text_content = strip_tags(html_content)

    msg = EmailMultiAlternatives(subject, text_content, from_email, [user_email])
    msg.attach_alternative(html_content, "text/html")
    
    msg.send()