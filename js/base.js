function do_login() {
    $('.login-box .alert').hide();
    var email_field = $('#login-email');
    var email = email_field.val();
    var email_regex = /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}$/i;
    if (email.search(email_regex)) {
        alert_user(email_field, 'Badly formed email');
        return false;
    }
    var password_field = $('#login-password');
    var password = password_field.val();
    if (!password) {
        alert_user(email_field, 'Empty password');
        return false;
    }
    $.ajax({
        'url': '/login',
        'type': 'POST',
        'data': {'email': email, 'password': password},
        'dataType': 'json',
        'success': function(data) {
            window.location = data.redirect;
        },
        'statusCode': {
            403: function() {
                alert_user($('#login-password'), 'Invalid password');
            }
        }
    });
}

function make_login() {
    var input =  '<label>Email</label>' +
                 '<input type="text" id="login-email"/>' +
                 '<label>Password</label>' +
                 '<input type="password" id="login-password"/>';
    var submit = $('<button class="btn btn-primary login-btn">Sign in</button>');
    submit.click(do_login);
    return $(input).after(submit).after('<div class="clearfix"></div>');
}

function rework_for_mobile() {
    // move login button to inactive "header" link
    var head = $('.login-head');
    var nav = head.closest('.nav');
    var data = head.text();
    nav.prepend('<li><a>' + data + '</a></li>');
    head.replaceWith('');

    // resize input boxes    
    $('.login-box input').addClass('input-large');

    $('.hero-unit').each(function() {
        $(this).removeClass('hero-unit');
        $(this).addClass('well');
        $(this).css('text-align', 'center');
    });
}

function check_mobile() {
    var width = $(window).width();
    return width < 480;
}

function alert_user(element, message) {
    if (check_mobile()) {
        alert(message);
    } else {
        element.after('<div class="alert alert-error">' + message + '</div>');
    }
}

function init_page() {}

function init() {
    $('.login-box').append(make_login());
    $('.dropdown-toggle').dropdown();
    // Fix input element click problem
    $('.login-box input, .login-box label').click(function(e) {
        e.stopPropagation();
        return false;
    });
    var width = $(window).width();
    if (width < 400) {//800) {
        rework_for_mobile();
    }
    
    init_page();
}
