
from db import settings, weeks
from textwrap import dedent
from google.appengine.api import mail
import logging

def html_template(tmpl):
    html = ['<html><body>']
    for line in tmpl.split('\n\n'):
        line = line.strip()
        html.append('<p>%s</p>' % line.replace('\n', '<br/>\n'))
    html.append('</body></html>')
    return '\n'.join(html)

new_user_template = dedent('''
    You have been added to to the 2012 Jack Gonzales' NFL Suicide Pool.

    You have %(num_entries)d entries. Click the following link to setup your account and make your Week 1 picks:
    %(link)s

    You have until %(deadline)s to setup your account and select your pick(s) for Week 1.

    Good luck!
''')
html_new_user_template = html_template(new_user_template)

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

    num_retries = 3
    sleep = 2
    while num_retries > 0:
        try:
            mail.send_mail(
                sender=settings.email_source(),
                to=email,
                subject='2012 NFL Suicide Pool: Activate Your Account',
                body=plain,
                html=html
            )
            return
        except Exception:
            logging.exception('Failed to send activation for %r, retrying', email) 
        num_retries -= 1
        time.sleep(sleep)
        sleep *= 2

picks_template = dedent('''
    Hello %(name)s!

    You have the following active entries in Jack's NFL Suicide Pool:
    %(entries)s

    Make your picks for Week %(week)d by clicking the following link:
    %(link)s

    You have until %(deadline)s to save your picks.

    Good luck!
''')
html_picks_template = html_template(picks_template)

def email_picks_link(user, week):

    alive_entries = Entry.gql('WHERE alive = True and user_id = :1', user.key().id())
    if alive_entries.count() == 0:
        logging.info('No active entries for %s', user.name)
        return
    token = users.make_login_token(user)
    args = {
        'name': player.name,
        'entries': '\n'.join(e.name for e in active_entries),
        'link': 'http://football.iernst.net/choose?handle=%s' % handle,
        'week': week,
        'deadline': weeks.deadline(week).strftime('%A, %B %d at %I:%M%p'),
    }
    plain = plain_pick % args
    args['deadline'] = '<b>%s</b>' % args['deadline']
    args['entries'] = args['entries'].replace('\n', '<br/>')
    args['link'] = '<a href="%(link)s">%(link)s</a>' % args
    html = html_pick % args

    num_retries = 3
    sleep = 2
    while num_retries > 0:
        try:
            mail.send_mail(
                sender=settings.email_source(),
                to='%s <%s>' % (player.name, player.email),
                subject='Suicide Pool: Your Picks for Week %d' % week,
                body=plain,
                html=html
            )
            return
        except Exception:
            logging.exception('Failed to send team picker for %r, email = %r, retrying',
                              player.name, player.email) 
        num_retries -= 1
        time.sleep(sleep)
        sleep *= 2

plain_breakdown = dedent('''
    The picks for Week %(week)d are in!

    You can view them at the following link:
    %(link)s
    
    Below is the distribution of picks:
    No Pick - %(nopick)d
    %(picks)s
''')
html_breakdown = html_template(plain_breakdown)
def email_breakdown(week):
    picks, nopick = count_picks(week) 
    args = {
        'week': week,
        'link': 'http://football.iernst.net/results',
        'nopick': nopick,
        'picks': '\n'.join('%s - %d' % e for e in sorted(picks.iteritems()))
    }
    plain = plain_breakdown % args
    args['link'] = '<a href="%(link)s">%(link)s</a>' % args
    args['picks'] = args['picks'].replace('\n', '<br/>') 
    html = html_breakdown % args
 
    email_all('Suicide Pool: Week %d Breakdown' % week, plain, html)
   
def email_all(subject, plain, html):
    addresses = []
    for p in Player.all():
        addresses.append(p.email)

    logging.info('Sending breakdown email to %d players', len(addresses))

    mail.send_mail(
        sender=settings.email_source(),
        to='football@iernst.net',
        bcc=addresses,
        subject=subject,
        body=plain,
        html=html
    )
