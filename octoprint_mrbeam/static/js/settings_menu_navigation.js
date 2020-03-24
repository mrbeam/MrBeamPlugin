$(document).ready(function () {
    let settingsElement = $("#settings_dialog #settings_dialog_menu ul li");
    // let settingsActiveElement = $("#settings_dialog #settings_dialog_menu ul li.active");
    settingsElement.hover(
        function () {
            $(this).prev().addClass("prev");
        },
        function () {
                $(this).prev().removeClass("prev");
        });
});
