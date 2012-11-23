
function make_title_input(title) {
    var t = '<input type="text" class="title-input" placeholder="Pithy title summarizing this week"';
    if (title) {
        t += ' value="' + title + '"';
    }
    t += '/>';
    return t;
}

function make_content_input(content) {
    var c = '<textarea class="content-input" placeholder="Bold commentary on this week\'s results">';
    if (content) {
        c += content;
    }
    c += '</textarea>';
    return c;
}

playoff_week_names = ['Wildcard', 'Divisional', 'Conference', 'Super Bowl'];
function week_name(week) {
    if (week > 17) {
        return playoff_week_names[week - 18];
    }
    return 'Week ' + week;
}

function percent(x, y) {
    return (100.0 * x / y).toFixed(1) + '%';
}

function display_error(msg, element) {
    element.find('.blog-error').hide();
    var error_msg = $('<div class="alert alert-error blog-error">' + msg + '</div>');
    element.prepend(error_msg);
}

function init_page() {
    
    container = $('#breakdown');
    week = parseInt(container.attr('current-week'));
    admin = container.attr('admin') == 'True';
    breakdown = new Breakdown(container, week, admin);

    $(window).resize(function() {
        breakdown.resize();
        breakdown.rebuild();
    });
    $(window).scroll(function() {
        if (breakdown.more_comments_handler) {
            breakdown.more_comments_handler();
        }
    });
    breakdown.load_week(week);
}

var Breakdown = function(container, max_week, admin) {
    this.container = container;
    this.max_week = max_week;
    this.week = max_week;
    this.admin = admin
    this.data = null;
    this.compact = null;
    this.more_comments_handler = null;
    this.resize();
}

Breakdown.prototype.resize = function() {
    compact = parseInt(this.container.css('width'), 10) < 800;
    if (this.compact == compact) {
        return;
    }
    this.compact = compact;
    container = this.make_new_container();
    this.build_selector(container);
    this.container.replaceWith(container); 
    this.container = container;
    this.main = container.find('.main');
    this.sidebar = container.find('.sidebar');
}

Breakdown.prototype.make_new_container = function() {
    var layout = null;
    if (this.compact) {
        layout = '<div class="selector"></div>' +
                 '<div class="sidebar"></div>' +
                 '<div class="main"></div>';
    } else {
        layout = '<div class="row">' +
                    '<div class="span2 selector"></div>' +
                    '<div class="span7 main"></div>' +
                    '<div class="span3 sidebar"></div>' +
                 '</div>';
    }
    return $('<div id="breakdown">' + layout + '</div>');
}

Breakdown.prototype.build_selector = function(container) {

    var selector = container.find('.selector');
    var breakdown = this;
    var make_link = null;
    var links = null;
    if (this.compact) {
        links = $('<select></select>');
        links.change(function() {
            breakdown.load_week(parseInt(links.val()));
        });
        make_link = function(week, selected) {
            var link = $('<option value="' + week + '">' + week_name(week) + '</option>');
            if (selected) {
                link.attr('selected', 'selected');
            }
            return link;
        };
    } else {
        links = $('<ul class="nav nav-list"></ul>');
        make_link = function(week, selected) {
            var selector = $('<a week="' + week + '">' +
                                '<i class="icon-chevron-right"></i>' + week_name(week) + 
                             '</a>');
            selector.click(function() {
                links.children('.active').removeClass('active');
                $(this).parent().addClass('active');
                breakdown.load_week(parseInt($(this).attr('week')));
            });
            var link = $('<li></li>').append(selector);
            if (selected) {
                link.addClass('active');
            }
            return link;
        };
    }
    selector.append(links);

    for (var i = 1; i <= this.max_week; i++) {
        links.append(make_link(i, this.week == i));
    }
}

Breakdown.prototype.rebuild = function() {

    this.rebuild_sidebar(this.sidebar);
    if (!this.data.blog.posted && !this.admin) {
        //this.main.hide();
        this.main.html('<div class="alert alert-invo">Jack has not posted commentary yet for this week</div>');
        return;
    }

    var blog = $('<div class="blog"></div>');
    this.rebuild_blog(blog, !this.data.blog.posted);
    var comments = null;
    if (this.data.blog.posted) {
        comments = $('<div class="comments"></div>');
        comments.html('<div class="pagination-centered"><img src="/img/loading-big.gif"/></div>');
        if (this.data.comments) {
            this.rebuild_comments(comments);
        } else {
            this.load_comments(comments);
        }
    }
    this.main.empty();
    this.main.append(blog);
    if (comments) {
        this.main.append($('<hr/>'));
        this.main.append(comments);
    }
}

Breakdown.prototype.rebuild_sidebar = function(sidebar) {
    var stats = this.data.stats;
    var total = stats.total;
    var s = '<h4>Stats</h4>' +
            '<table class="overall">' +
                '<tr>' +
                    '<td class="name">Winners</td>' +
                    '<td class="count"><div class="count-win">' + stats.wins + '</div></td>' +
                    '<td class="percent">' + percent(stats.wins, total) + '</td>' +
                '</tr>' +
                '<tr>' +
                    '<td class="name">Losers</td>' +
                    '<td class="count"><div class="count-loss">' + stats.losses + '</div></div></td>' +
                    '<td class="percent">' + percent(stats.losses, total) + '</td>' +
                '</tr>' +
                '<tr>' +
                    '<td class="name">Rule Violations</td>' +
                    '<td class="count"><div class="count-violation">' + stats.violations + '</div></td>' +
                    '<td class="percent">' + percent(stats.violations, total) + '</td>' +
                '</tr>' +
            '</table>';
    s += '<hr/><table class="teams">';
    var team_names = Object.keys(stats.teams);
    team_names.sort();
    for (var i = 0; i < team_names.length; i++) {
        var team_name = team_names[i];
        count = stats.teams[team_name];
        s += '<tr>' +
                '<td class="name">' + team_name + '</td>' +
                '<td class="count">' + count + '</td>' +
                '<td class="percent">' + percent(count, total) + '</td>' +
             '</tr>';
    }
    s += '</table>';
    this.sidebar.html('<div class="stats-data">' + s + '</div>');
}

Breakdown.prototype.rebuild_blog = function(blog, edit) {
     
    var breakdown = this;
    var title = $('<div class="title"></div>');
    var content = $('<div class="content"></div>');
    var controls = null;
    var alert_msg = null;
    if (this.admin) {
        controls = $('<div class="blog-controls"></div>');
    }

    if (edit) {
        title.html(make_title_input(this.data.blog.title));
        content.html(make_content_input(this.data.blog.content));

        var save_btn = $('<button class="btn"><i class="icon-ok"></i> Save</button>');
        save_btn.click(function() {
            if (!breakdown.save_blog(blog)) return false;
            breakdown.rebuild_blog(blog, false);
            return false;
        });
        controls.append(save_btn);

    } else {
        title.html(this.data.blog.title);
        content.html(this.data.blog.content);
        if (this.admin) {
            var edit_btn = $('<button class="btn"><i class="icon-edit"></i> Edit</button>');
            edit_btn.click(function() {
                breakdown.rebuild_blog(blog, true);
                return false;
            });
            controls.append(edit_btn);
        }
    }

    if (!this.data.blog.posted) {
        alert_msg = $('<div class="alert alert-info">This commentary is not visible to users. Click Post to make it visible.</div>');
        var post_btn = $('<button class="btn btn-primary"><i class="icon-share"></i> Post</button>');
        post_btn.click(function() {
            if (edit) {
                if (!breakdown.save_blog(blog)) return false;
            }
            if (!breakdown.post_blog(blog)) return false;
            breakdown.rebuild_blog(blog, false);
            return false;
        });
        controls.prepend(post_btn);
    }

    blog.empty();
    if (alert_msg) {
        blog.append(alert_msg);
    }
    blog.append(title);
    blog.append(content);
    if (controls) {
        blog.append(controls);
    }
}

Breakdown.prototype.rebuild_comments = function(comments) {
    var breakdown = this; 
    var header = $('<div><h5>Comments</h5></div>');
    var list = $('<ul class="comment-data"></ul>');
    var refresh_btn = $('<button class="btn btn-mini pull-right"><i class="icon-refresh"></i></button>');
    refresh_btn.click(function() {
        refresh_btn.replaceWith('<img class="pull-right" src="/img/loading.gif"/>');
        breakdown.load_comments(comments);
        return false;
    });
    header.prepend(refresh_btn);

    var controls = $('<div class="form-inline comment-controls"></div>');
    var input = $('<input type="text" id="new-comment" placeholder="Write a comment"/>');
    var add_btn = $('<button class="btn"><i class="icon-pencil"></i> Add</button>');
    var add_function = function() {
        var loading = $('<img class="pull-right" src="/img/loading.gif"/>');
        var parent = add_btn.parent();
        add_btn.detach();
        parent.append(loading);
        breakdown.save_comment(list);
        loading.replaceWith(add_btn);
        return false;
    };
    input.keypress(function(e) {
        if (e.which == 13) {
            add_function();
        }
    });
    add_btn.click(add_function);
    controls.append(input);
    controls.append(add_btn);

    this.add_comments(list, this.data.comments, true);

    comments.empty(); 
    comments.append(header);
    comments.append(controls);
    comments.append(list);
}

Breakdown.prototype.load_week = function(week) {
    this.main.empty();
    this.main.html('<div class="pagination-centered"><img src="/img/loading-big.gif"/></div>');
    this.main.show();
    this.sidebar.empty();
    if (!this.compact) {
        this.sidebar.html('<div class="pagination-centered"><img src="/img/loading.gif"/></div>');
    }
    this.sidebar.show();
    this.week = week;
    var breakdown = this;
    $.ajax({
        'url': '/breakdown/data/' + week,
        'dataType': 'json',
        'success': function(data) {
            breakdown.data = data;
            breakdown.rebuild();
        }
    });
}

Breakdown.prototype.load_comments = function(comments, append) {
    var num_comments = 10;
    var url = '/breakdown/comments/' + this.week + '?count=' + num_comments;
    if (append) {
        // when appending, find the last element's id 
        var last_comment = this.data.comments[this.data.comments.length - 1];
        url += '&created-before=' + last_comment.created;
    }
    var breakdown = this;
    $.ajax({
        'url': url,
        'dataType': 'json',
        'success': function(data) {
            if (append) {
                // comments is the comments list
                breakdown.add_comments(comments, data.comments, true);
            } else {
                breakdown.data.comments = data.comments;
                breakdown.rebuild_comments(comments);
            }
        }
    });
}

Breakdown.prototype.save_comment = function(list) {
    var comment = $('#new-comment').val();
    if (!comment) {
        return;
    }

    var data = { 'text': comment, 'count': 10 };
    if (this.data.comments.length > 0) {
        data['created-after'] = this.data.comments[0].created;
    }
    var breakdown = this;
    $.ajax({
        'url': '/breakdown/comments/' + this.week,
        'type': 'POST',
        'async': false,
        'data': data,
        'dataType': 'json',
        'success': function(data) {
            if (data.limited) {
                var add_to = list.clone(); 
                add_to.empty();
                breakdown.add_comments(add_to, data.comments, true);
                list.replaceWith(add_to);
            } else {
                breakdown.add_comments(list, data.comments, breakdown.data.comments.length == 0);
            }
            $('#new-comment').val('');
        }
    });
}


Breakdown.prototype.save_blog = function(blog) {
    var breakdown = this;
    var data = {
        'title': blog.find('.title-input').val(),
        'content': blog.find('.content-input').val()
    };
    if (!data.title) {
        display_error('You must enter a title', blog);
        return false;
    }
    if (!data.content) {
        display_error('You must enter some commentary', blog); 
        return false;
    }

    var result = false;
    $.ajax({
        'url': '/breakdown/data/' + this.week,
        'type': 'POST',
        'async': false,
        'data': data,
        'dataType': 'json',
        'success': function(data) {
            breakdown.data.blog = data; 
            result = true;
        },
        'error': function(xhr) {
            var msg = 'Server Error (' + xhr.status + '): ' + xhr.responseText;
            display_error(msg, blog);
        }
    });
    return result;
}

Breakdown.prototype.post_blog = function(blog) {
    var breakdown = this;
    var result = false;
    $.ajax({
        'url': '/breakdown/data/' + this.week,
        'type': 'POST',
        'async': false,
        'data': {'post':'true'},
        'success': function() {
            breakdown.data.blog.posted = true; 
            result = true;
        },
        'error': function(xhr) {
            var msg = 'Server Error (' + xhr.status + '): ' + xhr.responseText;
            display_error(msg, blog);
        }
    });
    return result;
}

Breakdown.prototype.add_comments = function(list, data, append) {
    if (append) {
        this.data.comments = this.data.comments.concat(data);
    } else {
        this.data.comments = data.concat(this.data.comments);
    }
    console.log('Num comments: ' + this.data.comments.length);

    var extra = $([]);
    var s = '';
    for (var i = 0; i < data.length; i++) {
        var comment = data[i];
        s += '<div class="comment">' +
                '<div class="head">' + 
                    '<span class="name">' + comment.user + '</span>' +
                    '<span class="date">' + comment.created_str + '</span>' +
                '</div>' +
                '<div class="text">' + comment.text + '</div>' +
             '</div>';
    }

    var new_comments = $(s);
    if (append) {
        var breakdown = this;
        var more_comments_trigger = new_comments.first();
        this.more_comments_handler = function() {
            if (!more_comments_trigger.closest('html').length) {
                // not yet in the dom
                return;
            }
            var bottom = $(window).scrollTop() + $(window).height();
            if (more_comments_trigger.offset().top < bottom) {
                breakdown.more_comments_handler = null;
                breakdown.load_comments(list, true);
            }
        };
        list.append(new_comments);
    } else {
        list.prepend(new_comments);
    }
}

