$(function () {
    function UserNotificationViewModel(params) {
        let self = this;
        window.mrbeam.viewModels["userNotificationViewModel"] = self;

        self.freshdeskWidget = params[0];

        openFreshWidget = function (prefilled_description, test) {
            if (prefilled_description) {
                window.FreshworksWidget("prefill", "ticketForm", {
                    subject: prefilled_description,
                });
            }
            self.freshdeskWidget.openWidgetFromError();
        };
        self._getPlaceHolderParameters = function (knowledgebase_url = null) {
            let kb_url =
                knowledgebase_url ||
                gettext("https://support.mr-beam.org/en") + "/support";
            let default_params = {
                utm_medium: "beamos",
                utm_source: "beamos",
                utm_campaign: "notification",
                version: MRBEAM_PLUGIN_VERSION,
                env: MRBEAM_ENV_LOCAL,
            };
            // this merges two objects. If both objects have a property with the same name, then the second object property overwrites the first.
            kb_url = kb_url + "?" + $.param(default_params);

            return {
                opening_tag:
                    '<a href="' + kb_url + '" target="_blank"><strong>',
                closing_tag: "</strong></a>",
                line_break: "<br />",
                opening_tag_support:
                    '<a href="javascript:void(0)" onclick="openFreshWidget(\'##err_code##\', self)"><strong>',
                closing_tag_support: "</strong></a>",
            };
        };

        /**
         * Add notification tempaltes here
         */
        self._notification_templates = {
            err_leaserheadunit_missing: {
                title: gettext("Laserhead unit missing"),
                text: _.sprintf(
                    gettext(
                        "The device is currently not able to start any laser job.\n" +
                            "\n" +
                            "Only disconnect or connect the laserhead unit if device is not powered on!\n" +
                            "\n" +
                            "Please shutdown the device and check the connection to the laserhead following this %(opening_tag)sKnowledgebase article%(closing_tag)s.\n" +
                            "\n" +
                            "If this doesn’t solve the problem, please %(opening_tag_support)sopen a support ticket%(closing_tag_support)s."
                    ),
                    self._getPlaceHolderParameters(
                        gettext("https://support.mr-beam.org/en") +
                            "/support/solutions/articles/43000560435"
                    )
                ),
                type: "error",
                hide: false,
            },
            err_bottom_open: {
                title: gettext("Bottom plate not detected"),
                text: _.sprintf(
                    gettext(
                        "The device is currently not able to start any laser job.\n" +
                            "\n" +
                            "Please make sure that the bottom is correctly mounted as described in the %(opening_tag)sKnowledgebase article%(closing_tag)s.\n" +
                            "\n" +
                            "If this doesn’t solve the problem, please %(opening_tag_support)sopen a support ticket%(closing_tag_support)s."
                    ),
                    self._getPlaceHolderParameters(
                        gettext("https://support.mr-beam.org/en") +
                            "/support/solutions/articles/43000703004"
                    )
                ),
                type: "error",
                hide: false,
            },
            err_hardware_malfunction_i2c: {
                title: gettext("Hardware malfunction"),
                text: _.sprintf(
                    gettext(
                        "The device is currently not able to start any laser job.\n" +
                            "\n" +
                            "Please shutdown the device and check the ribbon cable following the %(opening_tag)sKnowledgebase article%(closing_tag)s.\n" +
                            "\n" +
                            "If this doesn’t solve the problem, please %(opening_tag_support)sopen a support ticket%(closing_tag_support)s."
                    ),
                    self._getPlaceHolderParameters(
                        gettext("https://support.mr-beam.org/en") +
                            "/support/solutions/articles/43000703001"
                    )
                ),
                type: "error",
                hide: false,
            },
            err_unknown_malfunction: {
                title: gettext("Unknown malfunction"),
                text: _.sprintf(
                    gettext(
                        "The device is properly currently not able to start any laser job.\n" +
                            "\n" +
                            "Please %(opening_tag_support)sopen a support ticket%(closing_tag_support)s."
                    ),
                    self._getPlaceHolderParameters()
                ),
                type: "error",
                hide: false,
            },
            err_compressor_malfunction: {
                title: gettext("Compressor malfunction"),
                text: _.sprintf(
                    gettext(
                        "The device is currently not able to start any laser job.\n" +
                            "\n" +
                            "Please check the piping in the working area by following the %(opening_tag)sKnowledgebase article%(closing_tag)s. And restart the device.\n" +
                            "\n" +
                            "If this doesn’t solve the problem, please %(opening_tag_support)sopen a support ticket%(closing_tag_support)s."
                    ),
                    self._getPlaceHolderParameters(
                        gettext("https://support.mr-beam.org/en") +
                            "/support/solutions/articles/43000702996"
                    )
                ),
                type: "error",
                hide: false,
            },
            err_one_button_malfunction: {
                title: gettext("One Button malfunction"),
                text: _.sprintf(
                    gettext(
                        "The device is currently not able to start any laser job.\n" +
                            "\n" +
                            "You can still shut down the device via the Mr Beam Software.\n" +
                            "\n" +
                            "Please %(opening_tag_support)sopen a support ticket%(closing_tag_support)s."
                    ),
                    self._getPlaceHolderParameters()
                ),
                type: "error",
                hide: false,
            },
            err_interlock_malfunction: {
                title: gettext("Interlock malfunction"),
                text: _.sprintf(
                    gettext(
                        "The device is currently not able to start any laser job.\n" +
                            "\n" +
                            "Please check the lid switch following the %(opening_tag)sKnowledgebase article%(closing_tag)s.\n" +
                            "\n" +
                            "If this doesn’t solve the problem, please %(opening_tag_support)sopen a support ticket%(closing_tag_support)s."
                    ),
                    self._getPlaceHolderParameters(
                        gettext("https://support.mr-beam.org/en") +
                            "/support/solutions/articles/43000703002"
                    )
                ),
                type: "error",
                hide: false,
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
                title: gettext("Camera malfunction"),
                text: _.sprintf(
                    gettext(
                        "You can still use the device by aligning manually without camera support. See %(opening_tag)sKnowledgebase article%(closing_tag)s.\n" +
                            "\n" +
                            "Please try to restart the device. \n" +
                            "\n" +
                            "If this doesn’t solve the problem, you may %(opening_tag_support)sopen a support ticket%(closing_tag_support)s."
                    ),
                    self._getPlaceHolderParameters(
                        gettext("https://support.mr-beam.org/en") +
                            "/support/solutions/articles/43000557281"
                    )
                ),
                type: "error",
                hide: false,
            },
            err_job_cancelled_due_to_internal_error: {
                title: gettext("Laser job canceled"),
                text: _.sprintf(
                    gettext(
                        "The job was canceled due to an error - we apologize for any inconvenience.\n" +
                            "\n" +
                            "Please try to restart the device.\n" +
                            "\n" +
                            "If this doesn’t solve the problem, please %(opening_tag_support)sopen a support ticket%(closing_tag_support)s."
                    ),
                    self._getPlaceHolderParameters()
                ),
                type: "error",
                hide: false,
                before_close: (pnotify) => self._dismissNotification(pnotify),
            },
            err_hardware_malfunction_non_i2c: {
                title: gettext("Hardware malfunction"),
                text: _.sprintf(
                    gettext(
                        "The device is currently not able to start any laser job.\n" +
                            "\n" +
                            "Please try to restart the device.\n" +
                            "\n" +
                            "If this doesn’t solve the problem, please %(opening_tag_support)sopen a support ticket%(closing_tag_support)s."
                    ),
                    self._getPlaceHolderParameters()
                ),
                type: "error",
                hide: false,
            },
            err_fan_not_spinning: {
                title: gettext("Hardware malfunction"),
                text: _.sprintf(
                    gettext(
                        "Your Air Filter or single Fan is not spinning properly.\n" +
                            "\n" +
                            "The device is currently not able to start any laser job.\n" +
                            "\n" +
                            "Please %(opening_tag_support)sopen a support ticket%(closing_tag_support)s."
                    ),
                    self._getPlaceHolderParameters()
                ),
                type: "error",
                hide: false,
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

        self._replace_freshdesk_err_code = function (pnotify) {
            pnotify.text = pnotify.text.replace(
                "##err_code##",
                pnotify.err_code
            );
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
                before_close: function (pnotify) {
                    console.log("before_close", pnotify, notification_conf);
                    if (notification_conf.before_close) {
                        notification_conf.before_close(pnotify);
                    }
                },
                before_init: (pnotify) =>
                    self._replace_freshdesk_err_code(pnotify),
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

            // if error code is present show this instead show error message
            if (
                notification_conf.err_code &&
                notification_conf.err_code.length
            ) {
                pn_obj.text += self._getErrorCode(notification_conf.err_code);
                pn_obj.err_code = [notification_conf.err_code];
            } else if (
                notification_conf.err_msg &&
                notification_conf.err_msg.length
            ) {
                pn_obj.text += self._getErrorString(notification_conf.err_msg);
            }

            return pn_obj;
        };

        self._getKnowledgeBaseLink = function (kb_konf) {
            let specific_url = "url" in kb_konf;
            let kb_url =
                kb_konf.url ||
                gettext("https://support.mr-beam.org/en") + "/support/";
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

        self._getErrorCode = function (err) {
            if (err) {
                err = Array.isArray(err) ? err.join(",<br />") : err;
                return (
                    "<br/><br/><strong>" +
                    gettext("Error Code:") +
                    "</strong><br/>" +
                    err.toString()
                );
            } else {
                return "";
            }
        };

        self._dismissNotification = function (pnotify) {
            console.log("before_close", pnotify);
            OctoPrint.simpleApiCommand("mrbeam", "dissmiss_notification", {
                id: pnotify.options.id,
            })
                .done(function (response) {})
                .fail(function () {
                    console.error(
                        "Error while trying to request hardware errors."
                    );
                });
        };
        self._openFreshWidget = function (pnotify) {
            openFreshWidget(pnotify.error_code);
        };
    }

    // view model class, parameters for constructor, container to bind to
    OCTOPRINT_VIEWMODELS.push([
        UserNotificationViewModel,

        // e.g. loginStateViewModel, settingsViewModel, ...
        [
            /*"settingsViewModel", "wizardAclViewModel", "usersViewModel"*/
            "feedbackWidgetViewModel",
        ],

        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        [
            /* ... */
        ],
    ]);
});
