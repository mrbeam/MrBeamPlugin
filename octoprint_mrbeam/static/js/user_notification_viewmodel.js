$(function () {

    function UserNotificationViewModel(parameters) {
        let self = this;
        window.mrbeam.viewModels['userNotificationViewModel'] = self;

        /**
         * Add notification tempaltes here
         */
        self._notification_templates = {
            err_leaserheadunit_missing: {
                title: gettext("No laser head unit found"),
                text: gettext("Laser head unit not found. Please make sure that the laser head unit is connected correctly."),
            },
            err_bottom_open: {
                title: gettext("Bottom Plate Error"),
                text: gettext("The bottom plate is not closed correctly. Please make sure that the bottom is correctly mounted as described in the Mr Beam II user manual."),
            },
            err_hwardware_malfunction: {
                title: gettext("Hardware malfunction"),
                text: gettext("A possible hardware malfunction has been detected on this device. "),
            }
        }


        self.onDataUpdaterPluginMessage = function (plugin, data) {
            if (plugin != "mrbeam") {
                return;
            }

            if ('user_notification_system' in data) {
                let nu_notifications = data['user_notification_system']['notifications'] || [];

                for (let i = 0; i < nu_notifications.length; i++) {
                    let pn_obj = self._getPnObj(nu_notifications[i])

                    // find notification in screen
                    let existing_notification = null
                    for (let n = 0; n < PNotify.notices.length; n++) {
                        if (PNotify.notices[n].state != 'closed' &&
                            PNotify.notices[n].options &&
                            PNotify.notices[n].options.id == nu_notifications[i].notification_id) {
                            existing_notification = PNotify.notices[n]
                            break;
                        }
                    }
                    if (existing_notification) {
                        existing_notification.update(pn_obj)
                    } else {
                        new PNotify(pn_obj)
                    }
                }
            }
        };

        self._getPnObj = function (notification_conf) {
            let pn_obj = {
                id: notification_conf.notification_id || 'id_' + Date.now(),
                title: notification_conf.title || "Message",
                text: notification_conf.text || '',
                type: notification_conf.pnotify_type || 'info',
                hide: !(notification_conf.sticky == true),
                delay: (notification_conf.delay || 10) * 1000
            }
            if (notification_conf.notification_id in self._notification_templates) {
                pn_obj.title = self._notification_templates[notification_conf.notification_id].title || pn_obj.title
                pn_obj.text = '<br/ >' + self._notification_templates[notification_conf.notification_id].text || pn_obj.text

                if (notification_conf.knowledgebase_showlink) {
                    pn_obj.text += self._getKnowledgeBaseLink(notification_conf.knowledgebase_url, notification_conf.knowledgebase_params)
                }
                if (notification_conf.err_msg) {
                    pn_obj.text += self._getErrorString(notification_conf.err_msg)
                }
            }
            return pn_obj
        }

        self._getKnowledgeBaseLink = function (kb_url, kb_params) {
            let specific_url = !!kb_url
            kb_url = kb_url || "https://mr-beam.org/support"
            kb_url = kb_url + '?' + $.param(kb_params);
            if (specific_url) {
                return "<br /><br />" +
                    _.sprintf(gettext('For more information check out this %(opening_tag)sKnowledge Base article%(closing_tag)s'),
                        {
                            'opening_tag': '<a href="' + kb_url + '" target="_blank"><strong>',
                            'closing_tag': '</strong></a>',
                            'line_break': '<br />'
                        })
            } else {
                return "<br /><br />" +
                    _.sprintf(gettext('Browse our %(opening_tag)sKnowledge Base%(closing_tag)s'),
                        {
                            'opening_tag': '<a href="' + kb_url + '" target="_blank"><strong>',
                            'closing_tag': '</strong></a>',
                        })
            }
        }

        self._getErrorString = function (err) {
            if (err) {
                return '<br/><br/><strong>' + gettext("Error:") + '</strong><br/>' + err.toString()
            } else {
                return ''
            }

        }

    };

    // view model class, parameters for constructor, container to bind to
    OCTOPRINT_VIEWMODELS.push([
        UserNotificationViewModel,

        // e.g. loginStateViewModel, settingsViewModel, ...
        [/*"settingsViewModel", "wizardAclViewModel", "usersViewModel"*/],

        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        [ /* ... */]
    ]);
});
