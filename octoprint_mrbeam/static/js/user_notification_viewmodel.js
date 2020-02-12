$(function() {

    function UserNotificationViewModel(parameters) {
        var self = this;
        window.mrbeam.viewModels['userNotificationViewModel'] = self;


        self.onDataUpdaterPluginMessage = function(plugin, data) {
            if (plugin != "mrbeam") {
                return;
            }

            if ('user_notification_system' in data) {
                let nu_notifications = data['user_notification_system']['notifications'] || [];


                /**
                 * https://stackoverflow.com/a/25769659/2631798:
                 * Whenever you create a notification set an attribute called name which will be unique for each notification.
                 * Then use PNotify.notices to list all the notices, Then based on an if condition you can remove that
                 * particular notice by calling .remove on it. eg: PNotify.notices[notice_to_be_removed].remove();
                 *
                 * PNotify.notices[1].remove()
                 * PNotify.notices[1].update() looks good as well!!!!
                 */
            }
        };

    };

    // view model class, parameters for constructor, container to bind to
    OCTOPRINT_VIEWMODELS.push([
        UserNotificationViewModel,

        // e.g. loginStateViewModel, settingsViewModel, ...
        [/*"settingsViewModel", "wizardAclViewModel", "usersViewModel"*/],

        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        [ /* ... */ ]
    ]);
});
