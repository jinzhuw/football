
function init_page() {
    function update_week(end_week) {
        results.set_end_week(end_week);
        results.set_table($('#results-table-header'), $('#results-table-data'));
        results.update_controls();
    }

    results_data = {}
    $.ajax({
        'url': '/results/data',
        'method': 'GET',
        'async': false,
        'dataType': 'json',
        'success': function(data) {
            results_data = data; 
        }
    });    

    results = new Results();
    results.set_data(results_data);
    results.set_table($('#results-table-header'), $('#results-table-data'));
    results.set_header($('#results-container'), $('#results-header'));
    results.update_controls();
    
    $('#back-all').click(function() {
        update_week(results._end_week - results._start_week);
        return false;
    });

    $('#back-one').click(function() {
        update_week(results._end_week - 1); 
        return false;
    });

    $('#forward-one').click(function() {
        update_week(results._end_week + 1);
        return false;
    });

    $('#forward-all').click(function() {
        update_week(results._max_week);
        return false;
    });

    $(window).resize(function() {
        results.set_table($('#results-table-header'), $('#results-table-data'));
        results.set_header($('#results-container'), $('#results-header'));
        results.update_controls();
    });
}

var Results = function() {
    this._data = {};
    this._sorted = [];

    this._max_week = null;
    this._end_week = null;
    this._start_week = null;

    this._header_top = null;
    this._week_names = ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5', 'Week 6', 'Week 7', 'Week 8', 'Week 9', 'Week 10', 'Week 11', 'Week 12', 'Week 13', 'Week 14', 'Week 15', 'Week 16', 'Week 17', 'Wildcard', 'Divisional', 'Conference', 'Super Bowl'];
};

Results.prototype.set_data = function(results) {
    this._data = results;
    this._sorted = [];
    this._end_week = null;
    
    for (var s_index in results) {
        var num_weeks = results[s_index].length;
        var last_week = results[s_index][num_weeks - 1];
        var status = 0;
        if (typeof(last_week) != 'string' && last_week.status != 'buyback') {
            status = 1;
        }
        this._sorted.push({'name': s_index, 'weeks': num_weeks, 'status': status});
    }

    this._sorted.sort(function(one, two) {
	    if (one.weeks == two.weeks) {
            if (one.status == two.status) {
	            if (one.name < two.name) {
	                return -1;
                } else if (one.name > two.name) {
                    return 1;
                }
                return 0;
            }
            return one.status - two.status;
        }

	    return one.weeks < two.weeks ? 1 : -1; 
    });

    if (this._sorted.length > 0) {
        this._max_week = this._sorted[0].weeks;
        this._end_week = this._max_week;
    }
};

Results.prototype.set_end_week = function(end_week)
{
    this._end_week = end_week;
};

Results.prototype.set_header = function(container, header) {
    $(window).scroll(function(event) {
        var top = $(window).scrollTop();    
        var header_top = container.position().top;
        var header_margin_top = parseInt(container.css('margin-top'));        

        if (header_top < top) {
            header.css('top', (top - header_top - header_margin_top - 2) + 'px');
        }
        else {
	    header.css('top', '0');
        }
    });
};

Results.prototype.set_table = function(header, div) {
    if (!this._max_week) {
        return;
    }

    var max_width = parseInt(div.css('width'), 10) - 20;
    var max_weeks = parseInt((max_width - 200)/90);
    max_weeks = max_weeks < 1 ? 1 : max_weeks;
    var start_week = this._end_week - max_weeks;
    start_week = start_week < 0 ? 0 : start_week;
    this._start_week = start_week;

    table_html = '<table class="table table-striped table-bordered table-condensed"' +
                 ' style="margin: 0 auto; text-align: center">';
    
    var entry_sorted = null;
    var entry_data = null;

    table_html += '<tr><td class="results-table-entryname"><strong>Entry</strong></td>';

    var team;
    var type;

    for (var week_header = start_week; week_header < this._end_week; week_header++) {
        table_html +=  '<td class="results-table-week"><strong>' + this._week_names[week_header] + '</strong></td>';
    }

    table_html += '</tr>';
    table_html += '</table>';
    header.html(table_html);

    table_html = '<table class="table table-striped table-bordered table-condensed"' +
                 ' style="margin: 0 auto; text-align: center">';

    for (var entry = 0; entry < this._sorted.length; entry++) {
        entry_sorted = this._sorted[entry];
        entry_data = this._data[entry_sorted.name];

        if (entry_sorted.weeks <= start_week) {
	        continue;
        }

        table_html += '<tr><td class="results-table-entryname">';
        table_html += entry_sorted.name;
        table_html += '</td>';

        for (var week_count = start_week; week_count < this._end_week; week_count++) {
            classes = ['results-table-week'];
            team = ''
            
            if (week_count < entry_sorted.weeks) {
                if (typeof(entry_data[week_count]) == 'string') {
                    team = entry_data[week_count];
                }
                else {
                    team = entry_data[week_count].team;
                    classes.push(entry_data[week_count].status);
                }
            } else {
                classes.push('empty');
            }
            table_html += '<td class="';
            for (var i = 0; i < classes.length; i++) {
                table_html += classes[i] + ' ';
            }
            table_html += '">' + team + '</td>';
        }

        table_html += '</tr>';
    }

    table_html += '</table>';

    div.html(table_html);
};

Results.prototype.update_controls = function() {
    if (this._start_week == 0) {
        $('.back').attr('disabled', 'disabled');
    } else {
        $('.back').removeAttr('disabled');
    }
    if (this._end_week == this._max_week) {
        $('.forward').attr('disabled', 'disabled');
    } else {
        $('.forward').removeAttr('disabled');
    }
};
