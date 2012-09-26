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

var dateFormat = function () {
    var token = /d{1,4}|m{1,4}|yy(?:yy)?|([HhMsTt])\1?|[LloSZ]|"[^"]*"|'[^']*'/g,
        timezone = /\b(?:[PMCEA][SDP]T|(?:Pacific|Mountain|Central|Eastern|Atlantic) (?:Standard|Daylight|Prevailing) Time|(?:GMT|UTC)(?:[-+]\d{4})?)\b/g,
        timezoneClip = /[^-+\dA-Z]/g,
        pad = function (val, len) {
            val = String(val);
            len = len || 2;
            while (val.length < len) val = "0" + val;
            return val;
        };

    // Regexes and supporting functions are cached through closure
    return function (date, mask, utc) {
        var dF = dateFormat;

        // You can't provide utc if you skip other args (use the "UTC:" mask prefix)
        if (arguments.length == 1 && Object.prototype.toString.call(date) == "[object String]" && !/\d/.test(date)) {
            mask = date;
            date = undefined;
        }

        // Passing date through Date applies Date.parse, if necessary
        date = date ? new Date(date) : new Date;
        if (isNaN(date)) throw SyntaxError("invalid date");

        mask = String(dF.masks[mask] || mask || dF.masks["default"]);

        // Allow setting the utc argument via the mask
        if (mask.slice(0, 4) == "UTC:") {
            mask = mask.slice(4);
            utc = true;
        }

        var _ = utc ? "getUTC" : "get",
            d = date[_ + "Date"](),
            D = date[_ + "Day"](),
            m = date[_ + "Month"](),
            y = date[_ + "FullYear"](),
            H = date[_ + "Hours"](),
            M = date[_ + "Minutes"](),
            s = date[_ + "Seconds"](),
            L = date[_ + "Milliseconds"](),
            o = utc ? 0 : date.getTimezoneOffset(),
            flags = {
                d:    d,
                dd:   pad(d),
                ddd:  dF.i18n.dayNames[D],
                dddd: dF.i18n.dayNames[D + 7],
                m:    m + 1,
                mm:   pad(m + 1),
                mmm:  dF.i18n.monthNames[m],
                mmmm: dF.i18n.monthNames[m + 12],
                yy:   String(y).slice(2),
                yyyy: y,
                h:    H % 12 || 12,
                hh:   pad(H % 12 || 12),
                H:    H,
                HH:   pad(H),
                M:    M,
                MM:   pad(M),
                s:    s,
                ss:   pad(s),
                l:    pad(L, 3),
                L:    pad(L > 99 ? Math.round(L / 10) : L),
                t:    H < 12 ? "a"  : "p",
                tt:   H < 12 ? "am" : "pm",
                T:    H < 12 ? "A"  : "P",
                TT:   H < 12 ? "AM" : "PM",
                Z:    utc ? "UTC" : (String(date).match(timezone) || [""]).pop().replace(timezoneClip, ""),
                o:    (o > 0 ? "-" : "+") + pad(Math.floor(Math.abs(o) / 60) * 100 + Math.abs(o) % 60, 4),
                S:    ["th", "st", "nd", "rd"][d % 10 > 3 ? 0 : (d % 100 - d % 10 != 10) * d % 10]
            };

        return mask.replace(token, function ($0) {
            return $0 in flags ? flags[$0] : $0.slice(1, $0.length - 1);
        });
    };
}();

// Some common format strings
dateFormat.masks = {
    "default":      "ddd mmm dd yyyy HH:MM:ss",
    shortDate:      "m/d/yy",
    mediumDate:     "mmm d, yyyy",
    longDate:       "mmmm d, yyyy",
    fullDate:       "dddd, mmmm d, yyyy",
    shortTime:      "h:MM TT",
    mediumTime:     "h:MM:ss TT",
    longTime:       "h:MM:ss TT Z",
    isoDate:        "yyyy-mm-dd",
    isoTime:        "HH:MM:ss",
    isoDateTime:    "yyyy-mm-dd'T'HH:MM:ss",
    isoUtcDateTime: "UTC:yyyy-mm-dd'T'HH:MM:ss'Z'"
};

// Internationalization strings
dateFormat.i18n = {
    dayNames: [
        "Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat",
        "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"
    ],
    monthNames: [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
        "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"
    ]
};

// For convenience...
Date.prototype.format = function (mask, utc) {
    return dateFormat(this, mask, utc);
};
