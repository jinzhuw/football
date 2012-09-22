var Analysis = function()
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

Analysis.prototype.update_week = function(week_btn) {
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

    $('#wheader').html('Analysis (Week ' + this.current_week_btn.text() + ')');
    $('#blurb').html(data.blurb + '<p>Week: ' + this.current_week_btn.text() + '</p>');
}


Analysis.prototype.modify_blurb = function()
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

Analysis.prototype.update_blurb = function(save)
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

Analysis.prototype.update_stats = function()
{
    var week = this.current_week_btn.text();

    //ajax call to get stats?
    //data = [{label: 'Eliminated', value: '55%'}];
    //build stats inside of $('#stats')
}

Analysis.prototype.update_comments = function()
{
    var week = this.current_week_btn.text();

    //ajax call to get comments based on this.max_comments?

    data = [{user: 'Jack Conradson', timestamp: '09-09-09 03:03:03', comment: "Ryan, you suck."}];
}

Analysis.prototype.post_comment = function()
{
    //ajax call to post comment, make sure to sanitize input!

    update_comments();
}