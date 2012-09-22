
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
    $('#entry-' + entry_id + '-team').html('<img src="/img/loading.gif"/>'); 
    $.ajax({
        'url': '/picks/' + entry_id,
        'type': 'POST',
        'data': {'team': team.id},
        'success': function() {
            var entry = $('#entry' + entry_id);
            visually_select_team(team_info, entry_id);

            $('#entry-' + entry_id + '-team').html(team.city + ' ' + team.mascot); 
            entry.collapse('hide');
        },
        'error': function() {
            window.location = '/picks';
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

    /*
    var popover_alignment = 'right';
    if (visiting) {
        popover_alignment = 'left';
    }
    team_info.popover({
        trigger: 'hover',
        placement: popover_alignment,
        html: true,
        content: '<div class="stats"><img src="/img/loading.gif"/></div>'
        title: 'Stats',
    });
    */

    if (selected_id == team.id) {
        visually_select_team(team_info, entry_id);
    }
    return team_info;
}

function make_spread(favorite, spread) {
    s = '<div class="spread">';
    s += '<span class="fav"><strong>Favored:</strong>' + favorite + '</span>';
    s += '<span class="line"><strong>Line:</strong>' + spread + '</span>';
    s += '</div>';
    return $(s);
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
        game_info.append(make_spread(game.favorite, game.spread));
        picker.after(game_info);
    }
    //picker.hide();
    entry_section.find('.games img').replaceWith(picker);
}

function init_page() {
    var week = $('#picker').attr('week');
    $.ajax({
        'url': '/picks/games/' + week,
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
            /*$('.team-stats').hide();
            $('.stats').hide();
            */
        }
    });
}
