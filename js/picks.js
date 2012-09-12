
function visually_select_team(team_info, entry_id) {
    var id = 'entry-' + entry_id + '-selected';
    var old = $('#' + id);
    old.removeClass('selected-team');
    old.children('.status').html('').hide();
    old.removeAttr('id');
    team_info.children('.status').html('Picked').show();
    team_info.addClass('selected-team');
    team_info.attr('id', id);
}

function select_team(entry_id, team, team_info) {
    $.ajax({
        'url': '/picks/' + entry_id,
        'type': 'POST',
        'data': {'team': team.id},
        'success': function() {
            var entry = $('#entry' + entry_id);
            visually_select_team(team_info, entry_id);

            $('#entry-' + entry_id + '-team').html(team.city + ' ' + team.mascot); 
            entry.collapse('hide');
        }
    });
}

function sort_game(a, b) {
    if (a.datetime == b.datetime) {
        if (a.home_team.short < b.home_team.short) {
            return -1;
        } else {
            return 1;
        }
        // not possible for team codes to be the same
    }
    return a.datetime - b.datetime;
}

function make_team_info(entry_id, team, visiting, selected_id) {
    var t = '<div class="team-info';
    if (visiting) {
        t += ' visiting';
    }
    t += '"><div class="status alert"></div>';
    t += '<div class="team-box">';
    t += '<div class="team-logo" style="background-position:-' + team.logo_x + 'px -' + team.logo_y + 'px"></div>';
    t += '<div class="team-city">' + team.city + '</div>';
    t += '<div class="team-mascot">' + team.mascot + '</div>';
    t += '</div></div>';

    var team_info = $(t);
    team_info.click(function() { select_team(entry_id, team, team_info); });
    team_info.hover(function() { $(this).addClass('hilight-team'); },
                    function() { $(this).removeClass('hilight-team'); });
    if (selected_id == team.id) {
        visually_select_team(team_info, entry_id);
    }
    return team_info;
}

function add_picker_for_entry(entry_section, games, start_ndx) {
    var entry_id = entry_section.attr('entry-id');
    var selected_team_id = entry_section.attr('selected-team-id');
    var picker = $([]);
    for (var ndx = start_ndx; ndx < games.length; ndx++) {
        var game = games[ndx];
        var h = '<div class="visual-pick">'
        h += '<div class="pick-header">';
        h += '<div class="pull-right">' + game.time_str + '</div>';
        h += '<div class="date">' + game.date_str + '</div>';
        h += '</div></div>';
        var game_info = $(h);
        game_info.append(make_team_info(entry_id, game.visiting_team, true, selected_team_id));
        game_info.append(make_team_info(entry_id, game.home_team, false, selected_team_id));
        game_info.append('<div class="at">at</div>');
        picker.after(game_info);
    }
    //picker.hide();
    entry_section.find('.games img').replaceWith(picker);
}

function init_page() {
    //$('.collapse').collapse({toggle: false});
    $.ajax({
        'url': '/picks/data',
        'type': 'GET',
        'async': false,
        'dataType': 'json',
        'success': function(data) {
            // sort the games once, and figure out which games are past their deadline
            var current_time = parseInt($('#picker').attr('current-time'));
            data.sort(sort_game);     
            var start_ndx = 0;
            while (current_time > data[start_ndx].deadline) {
                start_ndx++;
            }

            $('.accordion-group').each(function() {
                add_picker_for_entry($(this), data, start_ndx);
            });
        }
    });
}
