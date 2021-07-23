$(document).ready(function () {
    let settingsElement = $("#settings_dialog #settings_dialog_menu ul li");
    settingsElement.hover(
        function () {
            $(this).prev().addClass("prev");
        },
        function () {
            $(this).prev().removeClass("prev");
        }
    );
});
