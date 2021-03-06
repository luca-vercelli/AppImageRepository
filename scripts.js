var apps = {};
var cur_platform = "linux";
var apps_data = [];

$(document).ready(function() {
    loadapps();
    
    $("#search_input").keyup(search_on_keyup);
    $("#btn_multiselect").click(show_checkboxes);
    $("#btn_dont_generate").click(hide_checkboxes);
    $("#btn_generate").click(function(){
    	generate_script();
    	hide_checkboxes();
    });
    $("#os_select").change(function() {
        cur_platform = $(this).val();
        drawapps();
    });
});

function alert2(text, alert_class="alert-danger") {
    // see https://getbootstrap.com/docs/4.0/components/alerts/
    $("#messages").html("<div class='alert " + alert_class + "' role='alert'>" + text + "</div>");
}

function alert2_dismiss() {
    $("#messages").html();
}

/**
* Draw all app boxes (perform AJAX call)
*/
function loadapps() {
    $("#controls").hide();
    $.ajax({
        url: "https://luca-vercelli.github.io/AppImageRepository/appimages.json",
        success: function(data, textStatus, jqXHR) {
            apps_data = data;
            drawapps();
            $("#search_input").val("");
            $("#controls").show();
        },
        error: function(jqXHR, textStatus, errorThrown ) {
            alert2("Error loading remote data!<br/>Text status: '" + textStatus + "' Error thrown: '" + errorThrown +"'");
        }
    });
}

/**
* Draw all app boxes (after AJAX call)
*/
function drawapps() {
    var parent_div = $("#apps_container");
    parent_div.html("");
    apps_data.forEach(function(item, index) {
        loadapp(parent_div, item);
    });
    console.log("" + apps_data.length + " apps loaded");
}

/**
* Draw a single app box
*/
function loadapp(parent_div, app_data) {
    var app_id = app_data.name.replace(/[:#\.\$//]/g,"-");
    app_data.app_id = app_id;
    apps[app_data.name] = app_data;
    var html_image = "<img class='appimg' src='" + get_icon_url(app_data.icons) + "'></img>";
    var last_version = get_last_version(app_data.versions);
    var html_download_button = "";
    if (last_version != null) {
        var html_download_caption = "Download";
        var url = last_version.url;
        var fsize = last_version.filesize;
        if (fsize != null && fsize > 0) {
            fsize = Math.round(fsize / 1048576);
            html_download_caption = html_download_caption + " (" + fsize + "Mb)";
        }
        html_download_button = "<a class='btn btn-primary' href='" + url + "' role='button' title='Download'>" + html_download_caption + "</a>";
    } else {
        html_download_button = "<a class='btn btn-primary' disabled role='button' title='No versions found'>No download</a>";
    }
    var website_url = get_website_url(app_data.links);
    var html_url_button = "";
    if (website_url != null) {
        html_url_button = "<a class='btn btn-secondary' href='" + website_url + "' target='_blank' role='button' title='Visit author website'>Website</a>";
    } else {
        html_url_button = "<a class='btn btn-secondary' disabled role='button' title='Website unknown'>No website</a>";
    }
    var html_checkbox = "<input type='checkbox' class='float-left d-none appchecked' id='check_" + app_id + "' value='" + app_data.name + "'></input>";
    var html_div_content = html_checkbox + html_image + "<br/>" + app_data.name + "<br/>" + html_download_button + "<br/>" + html_url_button;
    var html_div = "<div id='" + app_id + "' class='float-left appbox' title='" + get_title(app_data.description) + "' >" + html_div_content + "</div>";
    parent_div.append(html_div);
}

/**
* Get last version for app, or null
*/
function get_last_version(versions) {
    if (versions === undefined || versions == null) {
        return null;
    }
    var last_version = null;
    versions.forEach(function(item, index) {
        if (item.os == cur_platform && (last_version == null || last_version.url < item.url)) {
            last_version = item;
        }
    });
    return last_version
}

/**
* Get full app icon url, or a default value
*/
function get_icon_url(icons) {
    if (icons != null && icons.length > 0) {
        return "https://gitcdn.xyz/repo/AppImage/appimage.github.io/master/database/" + icons[0];
    } else {
        return "./logo.svg";
    }
}

/**
* Get full website url, or null
*/
function get_website_url(links) {
    if (links != null && links.length > 0) {
        for (var i in links) {
            var link = links[i];
            if (link.type == "GitHub") {
                return "https://github.com/" + link.url;
            }
        }
    }
    return null;
}

/**
* Get a suitable app description, or a default value
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
        // show all
        for (var app_name in apps) {
            var app_id = apps[app_name].app_id;
            $('#' + app_id).show();
        }
    } else {
    	str = str.toLowerCase();
        for (var app_name in apps) {
            var app_id = apps[app_name].app_id;
            var description = apps[app_name].description || "";
            // search case-insensitive in appname and description
            if(app_name.toLowerCase().indexOf(str) >= 0
            	|| description.toLowerCase().indexOf(str) >= 0) {
                $('#' + app_id).show();
            } else {
                $('#' + app_id).hide();
            }
        }
    }
}

/**
* Show checkboxes
*/
function show_checkboxes() {
    //for (var app_name in apps) {
    //    var app_id = apps[app_name].app_id;
    //    $('#check_' + app_id).removeClass("d-none");
    //}
    $(".appchecked").removeClass("d-none");
    $('#p_generate').removeClass("d-none");
}

/**
* Hide checkboxes
*/
function hide_checkboxes() {
    //for (var app_name in apps) {
    //    var app_id = apps[app_name].app_id;
    //    $('#check_' + app_id).addClass("d-none");
    //}
    $(".appchecked").addClass("d-none");
    $('#p_generate').addClass("d-none");
}

/**
* Generate and download install script
*/
function generate_script() {
    var appnames = $(".appchecked:checked").map(function(){
        return $(this).val();
    }).get();
    var script = "";
    for (var i in appnames) {
        script += "appimage install " + appnames[i] + "\n";
    }
    download("install.sh", script);
}

/**
* Create and download text file.
* @see https://stackoverflow.com/questions/3665115
*/
function download(filename, text) {
  var element = document.createElement('a');
  element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(text));
  element.setAttribute('download', filename);
  element.style.display = 'none';
  document.body.appendChild(element);
  element.click();
  document.body.removeChild(element);
}