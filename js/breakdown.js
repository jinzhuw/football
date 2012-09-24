
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
    admin = false;//container.attr('admin') == 'True';
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
    this.blog = container.find('.blog');
    this.stats = container.find('.stats');
    this.change_week(this.week);
}

Breakdown.prototype.make_new_container = function() {
    var layout = null;
    if (this.compact) {
        layout = '<div class="selector"></div>' +
                 '<div class="stats"></div>' +
                 '<div class="blog"></div>';
    } else {
        layout = '<div class="row">' +
                    '<div class="span2 selector"></div>' +
                    '<div class="span7 blog"></div>' +
                    '<div class="span3 stats"></div>' +
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
    this.blog.empty();
    this.blog.html('<div class="pagination-centered"><img src="/img/loading-big.gif"/></div>');
    this.blog.show();
    this.stats.empty();
    this.stats.html('<div class="pagination-centered"><img src="/img/loading.gif"/></div>');
    this.stats.show();
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
                    '<td class="name">Wins</td>' +
                    '<td class="count"><span class="badge badge-success">' + stats.wins + '</span></td>' +
                    '<td class="percent">' + percent(stats.wins, total) + '</td>' +
                '</tr>' +
                '<tr>' +
                    '<td class="name">Losses</td>' +
                    '<td class="count"><span class="badge badge-important">' + stats.losses + '</span></td>' +
                    '<td class="percent">' + percent(stats.losses, total) + '</td>' +
                '</tr>' +
                '<tr>' +
                    '<td class="name">Rule Violations</td>' +
                    '<td class="count"><span class="badge badge-warning">' + stats.violations + '</span></td>' +
                    '<td class="percent">' + percent(stats.violations, total) + '</td>' +
                '</tr>' +
            '</table>';
    s += '<hr/><table class="teams">';
    var team_names = Object.keys(stats.teams);
    team_names.sort();
    for (var i = 0; i < team_names.length; i++) {
        var team_name = team_names[i];
        console.log('Looking at team ' + team_name);
        count = stats.teams[team_name];
        s += '<tr>' +
                '<td class="name">' + team_name + '</td>' +
                '<td class="count">' + count + '</td>' +
                '<td class="percent">' + (100.0 * count / stats.total).toFixed(1) + '</td>' +
             '</tr>';
    }
    s += '</table>';
    return '<div class="stats-data">' + s + '</div>';
}

Breakdown.prototype.set_data = function(data) {

    // TODO: dont reload data on resize
    this.data = data;
    //this.stats.html(this.format_stats());
    if (!data.blog.posted && !this.admin) {
        this.stats.hide();
        this.blog.html(this.format_stats());
        return;
    } else {
        this.stats.html(this.format_stats());
    }

    var title = $('<p>Title: ' + data.blog.title + '</p>');
    var content = $('<p>Content: ' + data.blog.content + '</p>');
    var blog = $(title, content);
    this.blog.empty();
    this.blog.append(blog);
}


/*
function post_blog() {
    var week = $('#breakdown-selector').attr('current-week');
    $.ajax({
        'url': '/breakdown/blog/' + week,
        'type': 'POST',
        'data': {'post':'true'},
        'success': function() {
            update_controls(
            
            update_blog(data, week);
        }
    });
}

function edit_blog() {

}

function save_blog_data(week, data) {
    $.ajax({
        'url': '/breakdown/blog/' + week,
        'type': 'POST',
        'data': data,
        'success': function() {
            update_blog(data, week);
        }
    });
}

function get_blog_input() {
    return {
        'title': $('#blog .title-input').val(),
        'content': $('#blog .content-input').val()
    }
}

function save_blog() {
    var week = $('#breakdown-selector').attr('current-week');
    var data = get_blog_data();
    if (!data.title) {
        alert('You must enter a title!'); 
        return;
    }
    if (!data.content) {
        alert('You havne\'t entered any commentary'); 
        return;
    }
    save_blog_data(week, data);
}

function update_blog(data, week) {
    var is_admin = $('#blog').attr('admin') == 'true';

    var title = $('#blog .title');
    if (data.title && data.posted || ) {
        title.html(data.title);
    } else {
        title.html(make_title_input(data.title));
    }

    var content = $('#blog .content');
    if (data.content) {
        content.html(data.content);
    } else {
        content.html(make_content_input(data.content));
    }

    if (is_admin) {
        var controls = $('#blog .controls');
        if (!data.posted) {
            blog.append($('<div class="alert alert-info">This commentary is not yet visible to users.  Click Post to make visible, or Save it to post later</div>'));
            var post_btn = $('<button class="btn btn-primary">Post</button>');
            post_btn.click(post_blog);
            controls.append(post_btn);
        }
        if (data.title) {
            var edit_btn = $('<button class="btn">Edit</button>');
            edit_btn.click(edit_blog);
            controls.append(edit_btn)
        } else {
            var save_btn = $('<button class="btn">Save</button>');
            save_btn.click(save_blog);
            controls.append(save_btn)
        }
        blog.append(controls);
    }

    $('#blog
    $('#blog').replaceWith(blog);
}

function change_week(week) {
    $('#breakdown-selector').attr('current-week', week);
    $('.loading').show();
    $('#blog').hide();
    $('#comments').hide();
    $.ajax({
        'url': '/breakdown/blog/' + week,
        'dataType': 'json',
        'success': function(data) {
            update_blog(data, week);
        }
    });
    update_stats(week);
}

function setup_selector(compact) {
    var selector = $('#breakdown-selector');
    var max_week = parseInt(selector.attr('current-week'));
    var select_week = max_week;
    playoff_week_names = ['Wildcard', 'Divisional', 'Conference', 'Super Bowl'];

    if (compact) {
        
    }
    var links = $('<ul class="nav nav-list"></ul>');
    for (var i = 1; i <= max_week; i++) {
        var name = 'Week ' + i;
        if (i > 17) {
            name = playoff_week_names[i - 18];
        }
        var week_selector = $('<a week="' + i + '"><i class="icon-chevron-right"></i>' + name + '</a>');
        week_selector.click(function() {
            var new_week = parseInt($(this).attr('week'));
            var old_week = parseInt($('#breakdown-selector').attr('current-week'));
            if (new_week == old_week) return false;
            $('#breakdown-selector .active').removeClass('active');
            $(this).parent().addClass('active');
            change_week(new_week);
            return false;
        });
        links.append($('<li></li>').append(week_selector));
    }
    selector.append(links);
    week_selector.parent().addClass('active');
    change_week(max_week);
}

function setup_layout() {
    
}

function init_page() {
    setup_layout();
    setup_selector(false); 
}
*/

/*
var Breakdown = function()
{
    this.max_comments = 10;
    this.current_week_btn = null;
    this.edit_blurb = false;

    var that = this;

    $('.btn-week').click(function() {
        that.update_week($('#' + this.id));
	that.update_stats();
	that.update_comments();
    });

    $('#new_comment').focusin(function() {
        this.rows = 5;
    });

    $('#new_comment').focusout(function() {
        this.rows = 1;
    });
}

Breakdown.prototype.update_week = function(week_btn) {
    var week = week_btn.text();

    //ajax call to get data for week?

    data = {blurb: '<p>Test blurb.</p><p>Everyone sucks this week...</p>'};

    if (this.current_week_btn) {
	this.current_week_btn.removeClass('btn-primary');
	this.current_week_btn.removeClass('disabled');
    }

    this.current_week_btn = week_btn;
    this.current_week_btn.addClass('btn-primary');
    this.current_week_btn.addClass('disabled');

    $('#wheader').html('Breakdown (Week ' + this.current_week_btn.text() + ')');
    $('#blurb').html(data.blurb + '<p>Week: ' + this.current_week_btn.text() + '</p>');
}


Breakdown.prototype.modify_blurb = function()
{
    var save_btn_html = '<button id="save_blurb" class="btn btn-mini btn-primary save">Save</button>';
    var cancel_btn_html = '<button id="cancel_blurb" class="btn btn-mini btn-primary cancel"><strong>x</strong></button>';
    $('#edit_blurb_div').html('<div class="btn-group">' + save_btn_html + cancel_btn_html + '</div>');

    this.blurb = $('#blurb').html();
    $('#blurb').html('<div style="margin: 0; text-align: center"><textarea id="modify_blurb"'
		     + 'style="width: 90%">' + this.blurb + '</textarea></div>');

    $('#save_blurb').click(function() {analysis.update_blurb(true)});
    $('#cancel_blurb').click(function() {analysis.update_blurb(false)});
}

Breakdown.prototype.update_blurb = function(save)
{
    if (save) {
	var blurb_text = $('#modify_blurb').val();
	$('#blurb').html(blurb_text);
	//ajax to save text?
    }
    else {
	$('#blurb').html(this.blurb);
    }
    
    delete this.blurb;

    $('#edit_blurb_div').html('<button id="edit_blurb" class="btn btn-mini"><i class="icon-edit"></i></button>');
    $('#edit_blurb').click(function() {analysis.modify_blurb()});
}

Breakdown.prototype.update_stats = function()
{
    var week = this.current_week_btn.text();

    //ajax call to get stats?
    //data = [{label: 'Eliminated', value: '55%'}];
    //build stats inside of $('#stats')
}

Breakdown.prototype.update_comments = function()
{
    var week = this.current_week_btn.text();

    //ajax call to get comments based on this.max_comments?

    data = [{user: 'Jack Conradson', timestamp: '09-09-09 03:03:03', comment: "Ryan, you suck."}];
}

Breakdown.prototype.post_comment = function()
{
    //ajax call to post comment, make sure to sanitize input!

    update_comments();
}
*/

