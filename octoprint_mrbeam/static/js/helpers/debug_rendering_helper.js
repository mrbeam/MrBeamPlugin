/*
 * helper for easy render debugging.
 *
 * Author: Teja
 * License: AGPLv3
 */

function debugBase64(base64URL, target = "", data = null) {
    if (Array.isArray(base64URL)) {
        var dbg_links = base64URL.map(
            (url, idx) =>
                `<a target='_blank' href='${url}' onmouseover=' show_in_popup("${url}"); '>${idx}: Hover | Right click -> Open in new tab</a>`
        ); // debug message, no need to translate
        var dbg_link = dbg_links.join("<br/>");
    } else {
        var dbg_link = `<a target='_blank' href='${base64URL}' onmouseover=' show_in_popup("${base64URL}"); '>Hover | Right click -> Open in new tab</a>`; // debug message, no need to translate
    }
    if (data) {
        dbg_link += "<br/>" + JSON.stringify(data);
    }
    new PNotify({
        title: "render debug output " + target,
        text: dbg_link,
        type: "warn",
        hide: false,
    });
}

function show_in_popup(dataurl) {
    $("#debug_rendering_div").remove();
    $("body").append(
        "<div id='debug_rendering_div' style='position:fixed; top:0; left:0; border:1px solid red; background:center no-repeat; background-size: contain; background-color:aqua; width:50vw; height:50vh; z-index:999999; background-image:url(\"" +
            dataurl +
            "\")' onclick=' this.remove(); '></div>"
    );
}

(function (console) {
    /**
     * Convenient storing large data objects (json, dataUri, base64 encoded images, ...) from the console.
     *
     * @param {object} data to save (means download)
     * @param {string} filename used for download
     * @returns {undefined}
     */
    console.save = function (data, filename) {
        if (!data) {
            console.error("Console.save: No data");
            return;
        }

        if (!filename) filename = "console.json";

        if (typeof data === "object") {
            data = JSON.stringify(data, undefined, 4);
        }

        var blob = new Blob([data], { type: "text/json" }),
            e = document.createEvent("MouseEvents"),
            a = document.createElement("a");

        a.download = filename;
        a.href = window.URL.createObjectURL(blob);
        a.dataset.downloadurl = ["text/json", a.download, a.href].join(":");
        e.initMouseEvent(
            "click",
            true,
            false,
            window,
            0,
            0,
            0,
            0,
            0,
            false,
            false,
            false,
            false,
            0,
            null
        );
        a.dispatchEvent(e);
    };
})(console);
// End Render debugging utilities
