
from db import settings, breakdown, weeks
from util import view, handler, timezone
import webapp2
import copy

# TODO: add user auth restriction to all pages here

class BreakdownHandler(handler.BaseHandler):
    def get(self):
        week = weeks.current() - 1
        if not weeks.check_deadline(weeks.current()):
            # after the deadline users can see the stats breakdown
            week += 1
        view.render(self, 'breakdown', {'week': week}, js=True, css=True)

def build_blog_response(blog):
    return {
        'updated': str(blog.updated), # TODO: format this date
        'title': blog.title,
        'content': blog.content,
        'posted': blog.posted,
    }

class BreakdownDataHandler(handler.BaseHandler):
    def get(self, week):
        week = int(week)
        blog = breakdown.get_blog(week)
        (no_pick, picks, total) = breakdown.get_team_counts(week)
        status = breakdown.get_status_counts(week)
        data = {
            'blog': build_blog_response(blog),
            'stats': {
                'no_pick': no_pick,
                'teams': picks,
                'total': total,
                'wins': status.wins,
                'losses': status.losses,
                'violations': status.violations,
            },
        }
        view.render_json(self, data)

    def post(self, week):
        week = int(week)
        title = self.request.POST.get('title')
        content = self.request.POST.get('content')
        if content:
            blog = breakdown.save_blog(week, title, content)
            view.render_json(self, build_blog_response(blog))
        post = self.request.POST.get('post') == 'true'
        if post:
            breakdown.post_blog(week)

class CommentsHandler(handler.BaseHandler):

    def return_comments(self, week, limit, before=None, after=None):
        data = []
        count = 0
        for c in breakdown.get_comments(week, limit + 1, before=before, after=after):
            count += 1
            dt = copy.copy(c.created).replace(tzinfo=timezone.utc).astimezone(timezone.Pacific)
            data.append({
                'created_str': dt.strftime('%B %d, %H:%M %p').replace(' 0', ' '),
                'created': c.created_ts(),
                'text': c.text,
                'user': c.username,
            })
            if count == limit:
                break
        if data and before and data[-1]['created'] == int(before):
            # remove incorrectly match element from results...
            data = data[:-1]
            count -= 1
        data = {
            'limited': count >= limit,
            'comments': data
        }
        view.render_json(self, data)
    
    def get(self, week):
        count = int(self.request.get('count'))
        created_before = self.request.get('created-before')
        self.return_comments(int(week), count, before=created_before)

    def post(self, week):
        week = int(week)
        if week + 1 < weeks.current() or not weeks.check_deadline(week + 1):
            self.abort(403)
        text = self.request.POST.get('text')
        count = int(self.request.get('count'))
        created_after = self.request.get('created-after')
        breakdown.save_comment(week, self.user, text)
        self.return_comments(week, count, after=created_after)

app = webapp2.WSGIApplication([
    webapp2.Route('/breakdown/comments/<week>', CommentsHandler),
    webapp2.Route('/breakdown/data/<week>', BreakdownDataHandler),
    ('/breakdown', BreakdownHandler),
],
config=settings.app_config(),
debug=settings.debug())

