$(function () {
    function UserNotificationViewModel(parameters) {
        let self = this;
        window.mrbeam.viewModels["userNotificationViewModel"] = self;

        /**
         * Add notification tempaltes here
         */
        self._notification_templates = {
            err_leaserheadunit_missing: {
                title: gettext("No laser head unit found"),
                text: gettext(
                    "Laser head unit not found. Please make sure that the laser head unit is connected correctly."
                ),
                type: "error",
                hide: false,
                knowledgebase: {
                    url:
                        "https://support.mr-beam.org/support/solutions/articles/43000557281-system-messages#lhnotfound",
                },
            },
            err_bottom_open: {
                title: gettext("Bottom Plate Error"),
                text: gettext(
                    "The bottom plate is not closed correctly. Please make sure that the bottom is correctly mounted as described in the Mr Beam user manual."
                ),
                type: "error",
                hide: false,
                knowledgebase: {
                    url:
                        "https://support.mr-beam.org/support/solutions/articles/43000557281-system-messages#bottomplate",
                },
            },
            err_hardware_malfunction: {
                title: gettext("Hardware malfunction"),
                text: gettext(
                    "A possible hardware malfunction has been detected on this device. "
                ),
                type: "error",
                hide: false,
                knowledgebase: {
                    url:
                        "https://support.mr-beam.org/support/solutions/articles/43000557281-system-messages#hwmalfunction",
                },
            },
            warn_cam_conn_err: {
                title: gettext("Camera busy"),
                text: gettext(
                    "The camera was stopped recently, it will take a few seconds to restart."
                ),
                type: "info",
                hide: true,
            },
            missing_updateinformation_info: {
                title: gettext("No update information"),
                text: gettext(
                    "No information about available updates could be retrieved, please try again later. Errorcode: E-1000"
                ),
                type: "info",
                hide: false,
            },
            write_error_update_info_file_err: {
                title: gettext("Error during fetching update information"),
                text: gettext(
                    "There was a error during fetching the update information Errorcode: E-1001"
                ),
                type: "error",
                hide: false,
            },
            update_fetching_information_err: {
                title: gettext("Error during fetching update information"),
                text: gettext(
                    "There was a error during fetching the update information, please try again later."
                ),
                type: "error",
                hide: false,
            },
            err_cam_conn_err: {
                title: gettext("Camera Error"),
                text: gettext(
                    "The camera has had a small issue, please restart your Mr Beam if you need to use the camera to continue with your work."
                ),
                type: "error",
                hide: false,
                knowledgebase: {
                    url:
                        "https://support.mr-beam.org/support/solutions/articles/43000557281-system-messages#cameraerror",
                },
            },
            msg_cam_image_analytics_sent: {
                title: gettext("Thank you"),
                text: gettext(
                    "The last image from your camera was submitted to Mr Beam and is going to be uploaded silently in the background."
                ),
                type: "success",
            },
            lens_calibration_done: {
                title: gettext("Lens Calibration Over"),
                text: gettext(
                    "A new lens calibration file has been created and is now being used."
                ),
                type: "success",
                hide: false,
            },
        };

        self.onDataUpdaterPluginMessage = function (plugin, data) {
            if (plugin != "mrbeam") {
                return;
            }

            if ("user_notification_system" in data) {
                let nu_notifications =
                    data["user_notification_system"]["notifications"] || [];

                for (let i = 0; i < nu_notifications.length; i++) {
                    let pn_obj = self._getPnObj(nu_notifications[i]);
                    mrbeam.updatePNotify(pn_obj);
                }
            }
        };

        self._getPnObj = function (notification_conf) {
            let pn_obj = {
                id: notification_conf.notification_id || "id_" + Date.now(),
                title: notification_conf.title || "Message",
                text: notification_conf.text || "",
                type: notification_conf.type || "info",
                hide:
                    notification_conf.hide === undefined
                        ? true
                        : notification_conf.hide,
                delay: notification_conf.delay || 10 * 1000,
            };
            if (
                notification_conf.notification_id in
                self._notification_templates
            ) {
                pn_obj = {
                    ...pn_obj,
                    ...self._notification_templates[
                        notification_conf.notification_id
                    ],
                };
            }

            if ("knowledgebase" in pn_obj) {
                pn_obj.text += self._getKnowledgeBaseLink(pn_obj.knowledgebase);
            }
            if (
                notification_conf.err_msg &&
                notification_conf.err_msg.length > 0
            ) {
                pn_obj.text += self._getErrorString(notification_conf.err_msg);
            }

            return pn_obj;
        };

        self._getKnowledgeBaseLink = function (kb_konf) {
            let specific_url = "url" in kb_konf;
            let kb_url = kb_konf.url || "https://mr-beam.org/support";
            let default_params = {
                utm_medium: "beamos",
                utm_source: "beamos",
                utm_campaign: "notification",
                version: MRBEAM_PLUGIN_VERSION,
                env: MRBEAM_ENV_LOCAL,
            };
            // this merges two objects. If both objects have a property with the same name, then the second object property overwrites the first.
            let kb_params = { ...default_params, ...kb_konf.params };
            kb_url = kb_url + "?" + $.param(kb_params);
            if (specific_url) {
                return (
                    "<br /><br />" +
                    _.sprintf(
                        gettext(
                            "For more information check out this %(opening_tag)sKnowledge Base article%(closing_tag)s"
                        ),
                        {
                            opening_tag:
                                '<a href="' +
                                kb_url +
                                '" target="_blank"><strong>',
                            closing_tag: "</strong></a>",
                            line_break: "<br />",
                        }
                    )
                );
            } else {
                return (
                    "<br /><br />" +
                    _.sprintf(
                        gettext(
                            "Browse our %(opening_tag)sKnowledge Base%(closing_tag)s"
                        ),
                        {
                            opening_tag:
                                '<a href="' +
                                kb_url +
                                '" target="_blank"><strong>',
                            closing_tag: "</strong></a>",
                        }
                    )
                );
            }
        };

        self._getErrorString = function (err) {
            if (err) {
                err = Array.isArray(err) ? err.join(",<br />") : err;
                return (
                    "<br/><br/><strong>" +
                    gettext("Error:") +
                    "</strong><br/>" +
                    err.toString()
                );
            } else {
                return "";
            }
        };
    }

    // view model class, parameters for constructor, container to bind to
    OCTOPRINT_VIEWMODELS.push([
        UserNotificationViewModel,

        // e.g. loginStateViewModel, settingsViewModel, ...
        [
            /*"settingsViewModel", "wizardAclViewModel", "usersViewModel"*/
        ],

        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        [
            /* ... */
        ],
    ]);
});
