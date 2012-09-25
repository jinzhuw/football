
from db import settings, breakdown, weeks
from util import view, handler
import webapp2

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

app = webapp2.WSGIApplication([
    webapp2.Route('/breakdown/comments/<week>', CommentsHandler),
    webapp2.Route('/breakdown/data/<week>', BreakdownDataHandler),
    ('/breakdown', BreakdownHandler),
],
config=settings.app_config(),
debug=settings.debug())

