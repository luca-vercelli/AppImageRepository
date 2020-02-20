$(document).ready(function() {
    $.ajax({
        url: "https://luca-vercelli.github.io/AppImageRepository/appimages.json",
        success: function(data, textStatus, jqXHR) {
            loadapps(data); 
        },
        error: function(jqXHR, textStatus, errorThrown ) {
            alert2("Error loading remote data!<br/>Text status: '" + textStatus + "' Error thrown: '" + errorThrown +"'");
        }
    });
});

var app_names = [];

function alert2(text, alert_class="alert-danger") {
    // see https://getbootstrap.com/docs/4.0/components/alerts/#dismissing
    $("#messages").html("<div class='alert " + alert_class + "' role='alert'>" + text + "</div>");
}

function loadapps(data) {
    var parent_div = $("#apps_container");
    data.forEach(function(item, index) {
        console.log(item);
        loadapp(parent_div, item);
    });
    console.log("" + data.length + " apps loaded");
}

function loadapp(parent_div, app_data) {
    app_names.push(app_data.name);
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
    var html_div = "<div id='div_app_" + app_data.name + "' class='float-left appbox' " + html_title + ">" + html_div_content + "</div>";
    parent_div.append(html_div);
}

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

function get_icon_url(icons) {
    if (icons != null && icons.length > 0) {
        return "https://gitcdn.xyz/repo/AppImage/appimage.github.io/master/database/" + icons[0];
    } else {
        return "./logo.svg";
    }
}

function get_title(description) {
    if (description !== undefined && description != null && description != "") {
        return description;
    } else {
        return "No description available.";
    }
}

function search(s) {
    app_names.forEach(function(appname, index) {
        var box = $('#div_app_' + appname);
        if(appname != null && appname.indexOf(s) >= 0) {
            box.style.visibility = "visible";
        } else {
            box.style.visibility = "hidden";
        }
    });
}
