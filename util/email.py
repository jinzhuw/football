
from db import settings, weeks, users
from textwrap import dedent
from google.appengine.api import mail
import logging
import time

def _html_template(tmpl):
    html = ['<html><body>']
    for line in tmpl.split('\n\n'):
        line = line.strip()
        html.append('<p>%s</p>' % line.replace('\n', '<br/>\n'))
    html.append('</body></html>')
    return '\n'.join(html)

def _send_mail(emails, subject, plain, html):
    if not settings.email_enabled():
        logging.warning('Email disabled, would have sent:')
        logging.warning('To: %s\nSubject: %s\nBody: %s', emails, subject, plain)
        return
    kwargs = {}
    if len(emails) == 1:
        to = emails[0]
    else:
        to = settings.email_source()
        kwargs['bcc'] = emails
    num_retries = 1
    sleep = 2
    while num_retries > 0:
        try:
            mail.send_mail(
                subject=subject,
                sender=settings.email_source(),
                to=to,
                body=plain,
                html=html,
                **kwargs
            )
            return
        except Exception:
            logging.exception('Failed to send email to %s for %s, retrying', emails, subject)
            return
        num_retries -= 1
        time.sleep(sleep)
        sleep *= 2

new_user_template = dedent('''
    You have been added to to the 2012 Jack Gonzales' NFL Suicide Pool.

    You have %(num_entries)d entries. Click the following link to setup your account and make your Week 1 picks:
    %(link)s

    You have until %(deadline)s to setup your account and select your pick(s) for Week 1.

    Good luck!
''')
html_new_user_template = _html_template(new_user_template)

def email_new_user(email, token, num_entries):
    logging.info('Emailing new user %s', email)
    args = {
        'num_entries': num_entries,
        'link': 'http://www.jgsuicidepool.com/login/' + token,
        'deadline': weeks.deadline(1).strftime('%A, %B %d at %I:%M%p'),
    }
    plain = new_user_template % args
    args['deadline'] = '<strong>%s</strong>' % args['deadline']
    args['link'] = '<a href="%(link)s">Activate Your Account</a>' % args
    html = html_new_user_template % args
    _send_mail([email], '2012 NFL Suicide Pool: Activate Your Account', plain, html)

new_entries_template = dedent('''
    You have %(num_entries)d new unnamed entries. Click the following link to name them:
    %(link)s

    You have until %(deadline)s to name your entries and make your picks for Week %(week)d.

    Good luck!
''')
html_new_entries_template = _html_template(new_entries_template)

def email_new_entries(email, token, num_entries):
    logging.info('Emailing new user %s', email)
    week = weeks.current()
    args = {
        'num_entries': num_entries,
        'link': 'http://www.jgsuicidepool.com/login/' + token,
        'week': week,
        'deadline': weeks.deadline(week).strftime('%A, %B %d at %I:%M%p'),
    }
    plain = new_entries_template % args
    args['deadline'] = '<strong>%s</strong>' % args['deadline']
    args['link'] = '<a href="%(link)s">Name Your Entries</a>' % args
    html = html_new_entries_template % args
    _send_mail([email], '2012 NFL Suicide Pool: Name New Entries', plain, html)

picks_template = dedent('''
    Hello %(name)s!

    You have the following active entries in Jack's NFL Suicide Pool:
    %(entries)s

    Make your picks for Week %(week)d by clicking the following link:
    %(link)s

    You have until 11pm the night before a game to select that game, or %(deadline)s, whichever comes first.

    Good luck!
''')
html_picks_template = _html_template(picks_template)

reminder_picks_template = dedent('''
    Hello %(name)s!

    You still haven't chosen all of your picks for Week %(week)d.

    You have the following active entries without a pick:
    %(entries)s

    Click the following link to make your picks:
    %(link)s

    You have until %(deadline)s to make your picks.

    Good luck!
''')
reminder_html_picks_template = _html_template(reminder_picks_template)

def email_picks_link(user, entries, week, reminder):

    subject = '2012 NFL Suicide Pool: Your Picks for Week %d' % week
    if reminder:
        subject = 'REMINDER: ' + subject
        
    token = users.make_login_token(user)
    args = {
        'name': user.name,
        'entries': '\n'.join(e for e in entries),
        'link': 'http://www.jgsuicidepool.com/login/%s' % token,
        'week': week,
        'deadline': weeks.deadline(week).strftime('%A, %B %d at %I:%M%p'),
    }
    plain_template = picks_template
    html_template = html_picks_template
    if reminder:
        plain_template = reminder_picks_template 
        html_template = reminder_html_picks_template
    plain = picks_template % args
    args['deadline'] = '<b>%s</b>' % args['deadline']
    args['entries'] = args['entries'].replace('\n', '<br/>')
    args['link'] = '<a href="%(link)s">%(link)s</a>' % args
    html = html_template % args
    _send_mail([user.email], subject, plain, html)

plain_breakdown = dedent('''
    The picks for Week %(week)d are in!

    You can view them at the following link:
    %(link)s
    
    Below is the distribution of picks:
    No Pick - %(no_pick)d
    %(picks)s
''')
html_breakdown = _html_template(plain_breakdown)
def email_breakdown(week, no_pick, picks, emails):
    args = {
        'week': week,
        'link': 'http://www.jgsuicidepool.com/results',
        'no_pick': no_pick,
        'picks': '\n'.join('%s - %d' % e for e in sorted(picks.iteritems()))
    }
    plain = plain_breakdown % args
    args['link'] = '<a href="%(link)s">%(link)s</a>' % args
    args['picks'] = args['picks'].replace('\n', '<br/>') 
    html = html_breakdown % args
    logging.info('Sending breakdown:\n%s', plain)
 
    _send_mail(emails, '2012 NFL Suicide Pool: Week %d Breakdown' % week, plain, html)

