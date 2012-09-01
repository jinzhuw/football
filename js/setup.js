
function setup_1_to_2() {
    var name = $('#name').val();
    if (name) {
        var i = 1;
        $('.entry').each(function() {
            var default_name = name + ' #' + i;
            $(this).attr('default', default_name);
            $(this).attr('placeholder', default_name);
            $(this).val('');
            i += 1;
        });
        $('#finish-name .finish-data').text(name);
        $('#setup_1').fadeOut('fast', function() {
            $('#setup_2').fadeIn('slow');
        });
    }
    return false;
}

function check_server_entry_name(name) {
    return false;
}

function setup_2_to_3() {
    var entry_names = [];
    var errors = false;
    $('.alert').hide();
    $('.entry').each(function() {
        var name = $(this).val();
        if (!name) {
            name = $(this).attr('default');
        }
        if (entry_names.indexOf(name) != -1) {
            $(this).after('<div class="alert alert-error">You already used ' + name + '</div>' );
            errors = true;
            return;
        }
        if (check_server_entry_name(name)) {
            $(this).after('<div class="alert alert-error">' + name + ' is in use by another user</div>' );
            errors = true;
            return;
        }
        entry_names.push(name);
    });
    var list = '<ul class="unstyled">';
    for (var i = 0; i < entry_names.length; i++) {
        list += '<li>' + entry_names[i] + '</li>';
    }
    list += '</ul';
    $('#finish-entries .finish-data').html(list);
    $('#setup_2').fadeOut('fast', function() {
        $('#setup_3').fadeIn('slow');
    });
    return false;
}

function validate_password(empty_allowed) {
    var password = $('#new_password').val();
    var password_confirm = $('#new_password_confirm').val();
    if (password != password_confirm || !empty_allowed && !password) {
        $('#new_password_confirm').after('<div class="alert alert-error">Passwords do no match</div>');
        return ['', false];
    }
    return [password, true];
}

function submit_setup(success) {
    var args = {
        'name': $('#name').val(),
    }
    var password = $('#new_password').val();
    if (password) {
        args['password'] = password;
    }
    $('.entry').each(function() {
        var name = $(this).val();
        if (!name) {
            name = $(this).attr('default');
        }
        var entry_id = $(this).attr('entry-id');
        args['entry_' + entry_id] = name;
    });
    $.post('/setup/activation', args, success);
}

function setup_3_to_4() {
    $('.alert').hide();
    var password = validate_password(true);
    if (!password[1]) {
        return false;
    }
    var has_pass = 'Yes';
    if (password[0] == '') {
        has_pass = 'No';
    }
    $('#finish-password .finish-data').text(has_pass);
    $('#setup_3').fadeOut('fast', function() {
        $('#setup_4').fadeIn('slow');
        submit_setup(function() {
            $('.finish-header').html('<h3>Setup Complete</h3>');
            $('.finish-loading').hide();
            $('.finish-element').show();
        });
    });
}

function change_email() {
    $('.alert').hide();
    var email = $('#email').val();
    var email_regex = /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}$/i;
    if (email.search(email_regex)) {
        $('#email').after('<div class="alert alert-error">Please enter a valid email address.</div>');
        return false;
    }
    args = {
        'email': email
    };
    $.post('/setup/email', args, redirect_to_picks);
    return false;
}

function change_password() {
    $('.alert').hide();
    var password = validate_password(false);
    if (!password[1]) {
        return false;
    }
    $.post('/setup/password', {'password': password[0]}, redirect_to_picks);
    return false;
}

function name_entries() {

    return redirect_to_picks();
    return false;
}

function redirect_to_picks() {
    window.location = '/picks'; 
    return false;
}

function init_page() {
    
    $('.modal').hide();
    $('#setup_1').modal({
        'backdrop': 'static',
        'keyboard': false,
        'show': true,
    }).show().find('.btn-primary').click(setup_1_to_2);
    $('#setup_2').modal({
        'backdrop': 'static',
        'keyboard': false,
        'show': false,
    }).find('.btn-primary').click(setup_2_to_3);
    $('#setup_3').modal({
        'backdrop': 'static',
        'keyboard': false,
        'show': false,
    }).find('.btn-primary').click(setup_3_to_4);
    $('#setup_4').modal({
        'backdrop': 'static',
        'keyboard': false,
        'show': false,
    });

    $('#change_email').modal({
        'backdrop': 'static',
        'keyboard': false,
        'show': true,
    }).show().find('.btn-primary').click(change_email);
    $('#change_password').modal({
        'backdrop': 'static',
        'keyboard': false,
        'show': true,
    }).show().find('.btn-primary').click(change_password);
    $('#new_entries').modal({
        'backdrop': 'static',
        'keyboard': false,
        'show': true,
    }).show().find('.btn-primary').click(name_entries);

    $('.cancel').click(redirect_to_picks);
}
