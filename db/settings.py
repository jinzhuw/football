import webapp2

SYMMETRIC_KEY = 'awp3o9j&^%@q2fw3'

NODEADLINE = False

DEBUG = False

ADMINS = (
    'rjernst@gmail.com',
    'ryan@iernst.net',
    'test@example.com',
    'jgonzales6@gmail.com',
)

EMAIL_SOURCE = 'Jack Gonzales <jgonzales6@gmail.com>'
EMAIL_ENABLED = True

APP_CONFIG = webapp2.Config()
APP_CONFIG['webapp2_extras.sessions'] = {'secret_key': 'abcdefg'}


