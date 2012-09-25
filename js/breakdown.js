
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

function init_page() {
    
    container = $('#breakdown');
    week = parseInt(container.attr('current-week'));
    admin = container.attr('admin') == 'True';
    breakdown = new Breakdown(container, week, admin);

    $(window).resize(function() {
        breakdown.resize();
    });
}

var Breakdown = function(container, max_week, admin) {
    this.container = container;
    this.max_week = max_week;
    this.week = max_week;
    this.admin = admin
    this.data = null;
    this.compact = null;
    this.resize();
}

Breakdown.prototype.resize = function() {
    compact = parseInt(this.container.css('width'), 10) < 800;
    console.log('resizing, compact = ' + compact);
    if (this.compact == compact) {
        return;
    }
    this.compact = compact;
    container = this.make_new_container();
    this.setup_selector(container);
    this.container.replaceWith(container); 
    this.container = container;
    this.main = container.find('.main');
    this.sidebar = container.find('.sidebar');
    this.change_week(this.week);
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

Breakdown.prototype.setup_selector = function(container) {

    var selector = container.find('.selector');
    var breakdown = this;
    var make_link = null;
    var links = null;
    if (this.compact) {
        links = $('<select></select>');
        links.change(function() {
            breakdown.change_week(parseInt(links.val()));
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
                breakdown.change_week(parseInt($(this).attr('week')));
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

Breakdown.prototype.change_week = function(week) {
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
            breakdown.set_data(data);
        }
    });
}

Breakdown.prototype.format_stats = function() {
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
    return '<div class="stats-data">' + s + '</div>';
}

Breakdown.prototype.rebuild_blog = function(blog, edit) {
     
    var breakdown = this;
    var title = $('<div class="title"></div>');
    var content = $('<div class="content"></div>');
    var controls = null;
    if (this.admin) {
        controls = $('<div class="controls"></div>');
    }

    if (edit) {
        title.html(make_title_input(this.data.blog.title));
        content.html(make_content_input(this.data.blog.content));

        var save_btn = $('<button class="btn">Save</button>');
        save_btn.click(function() {
            if (!breakdown.save_blog(blog)) return false;
            breakdown.rebuild_blog(blog);
            return false;
        });
        controls.append(save_btn);

    } else {
        title.html(this.data.blog.title);
        content.html(this.data.blog.content);
        if (this.admin) {
            console.log('adding edit button');
            var edit_btn = $('<button class="btn">Edit</button>');
            edit_btn.click(function() {
                breakdown.rebuild_blog(blog, true);
                return false;
            });
            controls.append(edit_btn);
        }
    }

    if (!this.data.blog.posted) {
        var alert_msg = $('<div class="alert alert-info">This commentary is not yet visible to users.  Click Post to make visible, or Save it to post later</div>');
        controls.before(alert_msg);
        var post_btn = $('<button class="btn btn-primary">Post</button>');
        post_btn.click(function() {
            if (edit) {
                if (!breakdown.save_blog(blog)) return false;
            }
            if (!breakdown.post_blog(blog)) return false;
            breakdown.rebuild_blog(blog);
            return false;
        });
        console.log('adding post button');
        controls.prepend(post_btn);
    }

    blog.empty();
    blog.append(title);
    blog.append(content);
    if (controls) {
        blog.append(controls);
    }
}

function display_error(msg, blog) {
    blog.find('.blog-error').hide();
    var error_msg = $('<div class="alert alert-error blog-error">' + msg + '</div>');
    blog.prepend(error_msg);
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
            var msg = 'Server Error (' + xhr.status + '): ' + xhr.responseText + '</div>';
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
            var msg = 'Server Error (' + xhr.status + '): ' + xhr.responseText + '</div>';
            display_error(msg, blog);
        }
    });
    return result;
}

Breakdown.prototype.set_data = function(data) {

    // TODO: dont reload data on resize
    this.data = data;
    this.sidebar.html(this.format_stats());
    if (!data.blog.posted && !this.admin) {
        this.main.hide();
        return;
    }

    var blog = $('<div class="blog"></div>');
    this.rebuild_blog(blog, !data.blog.posted);
    var comments = null;
    if (data.blog.posted) {
        comments = $('<div class="comments"></div>');
        comments.html('<div class="pagination-centered"><img src="/img/loading-big.gif"/></div>');
    }
    this.main.empty();
    this.main.append(blog);
    if (comments) {
        this.main.append(comments);
    }
}

