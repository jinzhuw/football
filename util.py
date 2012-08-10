
def increment(d, k):
    if k not in d:
        d[k] = 0
    d[k] += 1

def html_template(tmpl):
    html = ['<html><body>']
    for line in tmpl.split('\n\n'):
        line = line.strip()
        html.append('<p>%s</p>' % line.replace('\n', '<br/>\n'))
    html.append('</body></html>')
    return '\n'.join(html)

