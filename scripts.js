var app_ids = {};

$(document).ready(function() {
    $.ajax({
        url: "https://luca-vercelli.github.io/AppImageRepository/appimages.json",
        success: function(data, textStatus, jqXHR) {
            $("#search_input").prop('disabled', true);
            $("#search_input").val("");
            loadapps(data);
            $("#search_input").prop('disabled', false);
        },
        error: function(jqXHR, textStatus, errorThrown ) {
            alert2("Error loading remote data!<br/>Text status: '" + textStatus + "' Error thrown: '" + errorThrown +"'");
        }
    });
    $("#search_input").keyup(search_on_keyup);
});

function alert2(text, alert_class="alert-danger") {
    // see https://getbootstrap.com/docs/4.0/components/alerts/
    $("#messages").html("<div class='alert " + alert_class + "' role='alert'>" + text + "</div>");
}

function alert2_dismiss() {
    $("#messages").html();
}

/**
* Draw all app boxes
*/
function loadapps(data) {
    var parent_div = $("#apps_container");
    parent_div.html("");
    data.forEach(function(item, index) {
        loadapp(parent_div, item);
    });
    console.log("" + data.length + " apps loaded");
}

/**
* Draw a single app box
*/
function loadapp(parent_div, app_data) {
    var app_id = app_data.name.replace(/[:#\.\$//]/g,"-");
    app_ids[app_data.name] = app_id;
    var html_div_content = app_data.name;
    var versions = app_data.versions;
    var last_version = get_last_version(app_data.versions);
    var icon_url = get_icon_url(app_data.icons)
    html_div_content = "<img class='appimg' src='" + icon_url + "'></img><br/>" + html_div_content;
    if (last_version != null) {
        var url = last_version.url;
        var fsize = last_version.filesize;
        if (fsize != null && fsize > 0) {
            fsize = Math.round(fsize / 1048576);
            html_div_content = html_div_content + " (" + fsize + "Mb)";
        }
        html_div_content = "<a href='" + url + "'>" + html_div_content + "</a>";
    }
    var html_title = "title='" + get_title(app_data.description) + "' ";
    var html_div = "<div id='" + app_id + "' class='float-left appbox' " + html_title + ">" + html_div_content + "</div>";
    parent_div.append(html_div);
}

/**
* Get last version for app
*/
function get_last_version(versions) {
    if (versions === undefined || versions == null) {
        return null;
    }
    var last_version = null;
    versions.forEach(function(item, index) {
        if (item.os == "linux" && (last_version == null || last_version.url < item.url)) {
            last_version = item;
        }
    });
    return last_version
}

/**
* Get full app icon url
*/
function get_icon_url(icons) {
    if (icons != null && icons.length > 0) {
        return "https://gitcdn.xyz/repo/AppImage/appimage.github.io/master/database/" + icons[0];
    } else {
        return "./logo.svg";
    }
}

/**
* Get a suitable app description
*/
function get_title(description) {
    if (description !== undefined && description != null && description != "") {
        return description;
    } else {
        return "No description available.";
    }
}

var search_timeout = null;
var old_search_string = "";

/**
* onkeyup handler for search text box
*/
function search_on_keyup(evt) {
    if (evt.key == "Escape") {
        // reset search
        $("#search_input").val("");
        old_search_string = "";
        return;
    }
    var search_string = $("#search_input").val();
    if (search_string != old_search_string) {
        if (search_timeout != null) {
            clearTimeout(search_timeout);
        }
        search_timeout =  setTimeout(function() {
            search_timeout = null;
            show_apps(search_string);
        }, 500);
    }
    old_search_string = search_string;
}

/**
* Hide / show apps containing 'str'
*/
function show_apps(str) {
    if (str === undefined || str == null || str == "") {
        //show all
        for (var app_name in app_ids) {
            var app_id = app_ids[app_name];
            $('#' + app_id).show();
        }
    } else {
        for (var app_name in app_ids) {
            var app_id = app_ids[app_name];
            // search case-insensitive in appname only
            if(app_name.toLowerCase().indexOf(str.toLowerCase()) >= 0) {
                $('#' + app_id).show();
            } else {
                $('#' + app_id).hide();
            }
        }
    }
}
