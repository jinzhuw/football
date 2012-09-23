
from db import settings, breakdown, weeks
from util import view, handler
import webapp2

# TODO: add user auth restriction to all pages here

class BreakdownHandler(handler.BaseHandler):
    def get(self):
        week = weeks.current() - 1
        if self.user.is_admin and not weeks.check_deadline(weeks.current()):
            week += 1
        view.render(self, 'breakdown', {'week': week}, js=True, css=True)

class BlogHandler(handler.BaseHandler):
    def get(self, week):
        blog = breakdown.get_blog(int(week))
        data = {
            'updated': str(blog.updated), # TODO: format this date
            'title': blog.title,
            'content': blog.content,
            'posted': blog.posted,
        }
        view.render_json(self, data)

    def post(self, week):
        week = int(week)
        title = self.request.POST.get('title')
        content = self.request.POST.get('content')
        if content:
            breakdown.save_blog(week, title, content)
        post = self.request.POST.get('post') == 'true'
        if post:
            breakdown.post_blog(week)

class CommentsHandler(handler.BaseHandler):
    def get(self, week):
        count = self.request.get('count')
        created_after = self.request.get('created-after')
        created_before = self.request.get('created-before')
        data = []
        for c in breakdown.get_comments(int(week), count, after=created_after, before=created_before):
            data.append({
                'created': str(c.created), # TODO: format this time
                'text': c.text,
                'user': c.user,
            })
        view.render_json(self, data)

    def post(self, week):
        week = int(week)
        if week + 1 < weeks.current() or weeks.deadline_passed(week + 1):
            self.abort(403)
        text = self.request.POST.get('text')
        breakdown.save_comment(int(week), self.user, text)

class StatsHandler(handler.BaseHandler):
    # TODO: add caching
    def get(self, week):
        week = int(week)
        (no_pick, picks) = breakdown.get_team_counts(week)
        status = breakdown.get_status_counts(week)
        data = {
            'no-pick': no_pick,
            'teams': picks,
            'wins': status.wins,
            'losses': status.losses,
            'violations': status.violations,
        }
        view.render_json(self, self.request.path, data)
        

app = webapp2.WSGIApplication([
    webapp2.Route('/breakdown/stats/<week>', StatsHandler),
    webapp2.Route('/breakdown/comments/<week>', CommentsHandler),
    webapp2.Route('/breakdown/blog/<week>', BlogHandler),
    ('/breakdown', BreakdownHandler),
],
config=settings.app_config(),
debug=settings.debug())

