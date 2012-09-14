

function send_picks_email() {
    var buttons = $(this).parent();
    var user_id = buttons.attr('user-id');
    $.ajax({
        'url': '/users/picks-email/' + user_id,
        'type': 'POST',
        'success': function(data) {
            buttons.after('<div class="alert alert-info">Email sent</div>');
        },
        'error': function(data) {
            buttons.after('<div class="alert alert-error">Failed to send email</div>');
        }
    });    
    return false;
}

function resend_activation() {
    var button_column = $(this).parent();
    var user_id = $(this).attr('user-id');
    $.ajax({
        'url': '/users/resend-activation/' + user_id,
        'type': 'POST',
        'success': function(data) {
            button_column.html('<span class="alert alert-info">Sent</span>');
        }
    }); 
    return false;
}

function new_entry() {
    var user_id = $(this).parent().attr('user-id');
    var user_section = $(this).closest('.accordion-body');
    $.ajax({
        'url': '/users/entries/' + user_id,
        'type': 'POST',
        'success': function(data) {
            user_section.find('.alert').hide();
            var entries_alert = '<div class="alert alert-info">' + data + ' new entries</div>';
            user_section.find('.entries-section').after(entries_alert);
        }
    });    
    return false;
}

function buyback_entry() {
    var entry_id = $(this).attr('entry-id');
    var buyback_column = $(this).parent();
    var entry_status = $(this).parent().parent().find('.status');
    $.ajax({
        'url': '/users/buyback/' + entry_id,
        'type': 'POST',
        'success': function() {
            buyback_column.html('');
            entry_status.html('<span class="label label-success">Alive</span>');
        }
    });
    return false;
}

function add_new_user() {
    var button = $(this);
    $('.control-box .alert').hide();
    var email = $('#new-email').val();
    var email_regex = /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}$/i;
    if (email.search(email_regex)) {
        $('#new-email').after('<div class="alert alert-error">Malformed email.</div>');
        return false;
    }

    var num_entries = $('#new-num-entries').val();
    if (parseInt(num_entries) <= 0) {
        $('#new-num-entries').after('<div class="alert alert-error">Invalid number of entries.</div>');
        return false;
    }

    button.html('Creating... <img src="/img/loading.gif"/>');
    $.ajax({
        'url': '/users/newuser',
        'data': {'email': email, 'num_entries': num_entries},
        'type': 'POST', 
        'success': function(data) {
            $('#new-email').val('');
            $('#new-num-entries').val('');
            var new_row = '<tr><td>' + email + '</td><td><a class="btn btn-small btn-info" href="/login/'
                          + data + '">Login</a></td></tr>';
            $('#unactivated-users').prepend(new_row);
        },
        'error': function(xhr) {
            var error_msg = 'Unknown error from server.';
            if (xhr.status == 409) {
                error_msg = 'This email is already used.';
            }
            $('#new-email').after('<div class="alert alert-error">' + error_msg + '</div>');
        }        
    });
    button.html('Create user');

    return false;
}

function init_page() {
    $('.collapse').collapse({toggle: false});

    $('.new-entry-btn').click(new_entry);
    $('.send-pick-links').click(send_picks_email);
    $('#new-user-form').find('.btn-primary').click(add_new_user);
    $('.buyback').click(buyback_entry);
    $('.resend').click(resend_activation);
}
