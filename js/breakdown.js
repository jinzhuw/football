
function make_title_input(title) {
    var t = '<input type="text" placeholder="Some title summarizing this week"';
    if (title) {
        t += ' value="' + title + '"';
    }
    t += '/>';
    return t;
}

function make_content_input(content) {
    var c = '<textarea placeholder="A pithy commentary on this week\'s results">';
    if (content) {
        c += content;
    }
    c += '</textarea>';
    return c;
}

function post_blog() {
    var week = $('#breakdown-selector').attr('current-week');
    var data = get_blog_data();
    $.ajax({
        'url': '/breakdown/blog/' + week,
        'type': 'POST',
        'data': {'post':'true'},
        'success': function() {
            update_blog(data);
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
            update_blog(data);
        }
    });
}

function get_blog_data() {
    return {
        'title': $('.title input').val(),
        'content': $('.content textarea').val()
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

function update_blog(data) {
    var is_admin = $('#blog').attr('admin') == 'true';
    var blog = $('#blog').clone();
    blog.html('');

    var title = '<div class="title">';
    if (data.title) {
        title += data.title;
    } else {
        title += make_title_input(data.title);
    }
    title += '</div>';
    blog.append($(title));

    var content = '<div class="content">';
    if (data.content) {
        content +=  data.content;
    } else {
        content += make_content_input(data.content);
    }
    content += '</div>';
    blog.append($(content));

    if (is_admin) {
        var controls = $('<div class="controls pull-right"></div>');
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

    $('#blog').replaceWith(blog);
}

function change_week(week) {
    $('#breakdown-selector').attr('current-week', week);
    $('#blog').html('<div style="text-align:center"><img src="/img/loading-big.gif"/></div>'); 
    $('#commens').html('');
    $.ajax({
        'url': '/breakdown/blog/' + week,
        'dataType': 'json',
        'success': update_blog
    });
    //update_stats(week);
    //update_comments(week); 
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

