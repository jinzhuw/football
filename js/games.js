
function reset_game_data(game, control, scores, original) {
    var visiting = scores.find('.visiting');
    var visiting_score;
    var home = scores.find('.home');
    var home_score;
    if (original) {
        visiting_score = visiting.attr('default');
        home_score = home.attr('default');
    } else {
        visiting_score = visiting.val();
        home_score = home.val();
    }
    var visiting_column = visiting.parent();
    var home_column = home.parent();
    visiting_column.html(visiting_score);
    home_column.html(home_score);
    visiting_score = parseInt(visiting_score);
    home_score = parseInt(home_score);
    if (!isNaN(visiting_score) && !isNaN(home_score)) {
        if (visiting_score > home_score) {
            visiting_column.parent().addClass('winner'); 
        } else {
            home_column.parent().addClass('winner'); 
        }
    }
    game.find('caption small').text('Final');
    control.html('<button class="btn btn-mini"><i class="icon-edit"></i></button>');
    add_edit_scores_handler(game);
}

function submit_scores(control, scores, game) {
    var visiting = scores.find('.visiting');
    var home = scores.find('.home');
    var visiting_score = parseInt(visiting.val());
    var home_score = parseInt(home.val());
    if (isNaN(visiting_score)) {
        visiting_score = parseInt(visiting.attr('default'));
    }
    if (isNaN(home_score)) {
        home_score = parseInt(home.attr('default'));
    }
        
    if (visiting_score >= 0 && home_score >= 0) {
        $.ajax({
            type: 'POST',
            url: 'games/' + game.attr('game-id'),
            data: 'home=' + home_score + '&visiting=' + visiting_score,
            success: function() {
                reset_game_data(game, control, scores, false); 
            }
        });
    } else {
        alert('Scores must be positive');
    }
}

function edit_scores(control, game) {
    game.find('.winner').removeClass('winner');
    var scores = game.find('td.score');
    scores.each(function() {
        var score = $(this).text();
        var team = $(this).attr('team');
        $(this).html('<input type="text" default="' + score + '" class="' + team + '" placeholder="' + score + '"/>');
    });

    control.html(function() {
        var save_btn = '<button class="btn btn-mini btn-primary save">Save</button>';
        var cancel_btn = '<button class="btn btn-mini btn-primary cancel"><strong>x</strong></button>';
        return '<div class="btn-group">' + save_btn + cancel_btn + '</div>';
    });
    control.find('.save').click(function() {
        submit_scores(control, scores, game);
        return false;                
    });
    control.find('.cancel').click(function() {
        reset_game_data(game, control, scores, true);
        return false;
    });
}

function add_edit_scores_handler(game) {
    game.find('button').click(function() {
        edit_scores($(this).parent(), game);
        return false;
    });
}

function init_page() {
    $('.game').each(function() {
        add_edit_scores_handler($(this));
    });
}
