$(function () {
    function MessagesViewModel(parameters) {
        let self = this;
        window.mrbeam.viewModels['messagesViewModel'] = self;

        self.settings = parameters[0];
        self.userSettings = parameters[1];
        self.loginState = parameters[2];

        const FIRST_MESSAGE_LOCATION = "/plugin/mrbeam/static/messages/messages.json";
        const MESSAGES_URL = "https://messages.beamos.mr-beam.org/messages.json";

        self.messages = ko.observableArray();
        self.messagesIds = ko.observableArray();
        self.selectedIndex = ko.observable();
        self.hasUnread = ko.observable(false);
        self.lastMessageId = -1;
        self.oldUnreadMessageIds = -1;
        self.notificationsHandled = false;
        self.messagesLoaded = false;

        self.onStartup = function () {
            // Hide Messaging icon
            $("li a#messages_nav_tab").hide();
        }

        self.onUserLoggedIn = function (user) {
            // get user messages details
            if (user?.settings?.mrbeam?.messages) {
                self.lastMessageId = user.settings.mrbeam.messages.lastId;
                self.oldUnreadMessageIds = user.settings.mrbeam.messages.unreadIds;
            }
            // load remote messages
            if (!self.messagesLoaded) {
                self.loadRemoteMessages(MESSAGES_URL);
            }
        };

        self.loadRemoteMessages = function (messageUrl) {
            fetch(messageUrl, {
                method: 'GET'
            }).then(function (response) {
                return response.json();
            }).then(function (json) {
                console.log("Remote Messages loaded: ", json);
                self.saveNewMessages(json);
            }).catch(function (exception) {
                console.log("Remote Messages loading failed! Loading Local Messages");
                self.loadLocalMessages();
            });
        };

        self.saveNewMessages = function (data) {
            // convert object of array into object of an array of objects
            let messages = {};
            for (let i in data.messages) {
                if (data.messages.hasOwnProperty(i)) {
                    messages[i] = data.messages[i];
                }
            }
            let postData = {
                put: messages,
                delete: []
            };
            // save remotely fetched messages
            OctoPrint.simpleApiCommand("mrbeam", "messages", postData)
                .done(function (response) {
                    console.log("Saved Remote Messages loaded: ", response);
                    self.handleMessages(response);
                })
                .fail(function (response) {
                    console.log("Saving Remote Messages failed! Loading Local Messages");
                    self.loadLocalMessages();
                });
        };

        self.loadLocalMessages = function () {
            OctoPrint.simpleApiCommand("mrbeam", "messages", {})
                .done(function (data) {
                    if (Object.keys(data.messages).length === 0 && data.messages.constructor === Object) {
                        // Load First Generic Message
                        console.log("Loading First Message");
                        self.loadRemoteMessages(FIRST_MESSAGE_LOCATION);
                    } else {
                        console.log("Local Messages loaded: ", data.messages);
                        self.handleMessages(data);
                    }
                })
                .fail(function (response) {
                    console.log("Local Messages loading failed!");
                    console.log(response);
                    if (self.loginState.loggedIn()) {
                        // Load First Generic Message
                        console.log("Loading First Message");
                        self.loadRemoteMessages(FIRST_MESSAGE_LOCATION);
                    }
                });
        };

        self.handleMessages = function (data) {
            // convert object into array
            data.messages = Object.values(data.messages);
            if (data && data.messages) {
                let result = [];
                let messageIds = [];
                data.messages.forEach(function (myMessage) {
                    if (self.checkRestriction(myMessage.restrictions)) {
                        let msgObj = {
                            id: myMessage.id,
                            date: myMessage.date,
                            content: null,
                            images: myMessage.content.images || [],
                            notification: null,
                            read: false
                        };
                        let myLocale = LOCALE in myMessage.content ? LOCALE : 'en';
                        // content
                        if (myMessage.content && myMessage.content[myLocale]) {
                            msgObj.content = {
                                title: myMessage.content[myLocale].title,
                                body: myMessage.content[myLocale].body
                            };
                            if (myMessage.content[myLocale].cta) {
                                msgObj.content.cta_url = myMessage.content[myLocale].cta.url;
                                msgObj.content.cta_label = myMessage.content[myLocale].cta.label;
                            }
                        }
                        // notification
                        if (myMessage.notification && myMessage.notification[myLocale]) {
                            if (self.checkRestriction(myMessage.notification.restrictions)) {
                                msgObj.notification = {
                                    sticky: myMessage.notification.sticky,
                                    type: myMessage.notification.type,
                                    title: myMessage.notification[myLocale].title,
                                    body: myMessage.notification[myLocale].body
                                };
                            }
                        }
                        if (self.lastMessageId === -1 ||
                            myMessage.id > self.lastMessageId ||
                            (self.oldUnreadMessageIds != null &&
                                self.getArray(self.oldUnreadMessageIds).includes(myMessage.id))) {
                            messageIds.push(myMessage.id);
                        } else {
                            msgObj.read = true;
                        }
                        result.push(msgObj);
                        self.messagesLoaded = true;
                        $("li a#messages_nav_tab").show();
                    }
                });
                result.sort(function (a, b) {
                    // latest message at the top
                    if (a.id === b.id) {
                        return 0;
                    }
                    return a.id < b.id ? 1 : -1;
                });
                self.messagesIds(messageIds);
                self.messages(result);
                self.showNotifications();
            }
        };

        self.checkRestriction = function (restrictions) {
            if (!restrictions) {
                return true;
            }
            // channel
            if (restrictions.channels && restrictions.channels.length > 0 && restrictions.channels.map(function (x) {
                return x.trim().toUpperCase();
            }).includes(MRBEAM_SW_TIER)) {
                return false;
            }
            // version
            if (
                restrictions.version &&
                restrictions.version.length > 0 &&
                restrictions.version
                    .map(function (x) {
                        return x.trim().toUpperCase();
                    })
                    .includes(MRBEAM_PLUGIN_VERSION)
            ) {
                return false;
            }
            // version_and_newer
            if (
                restrictions.version_and_newer &&
                restrictions.version_and_newer.length > 0 &&
                mrbeam.comparePEP440Versions(
                    MRBEAM_PLUGIN_VERSION,
                    restrictions.version_and_newer,
                    "__ge__"
                )
            ) {
                return false;
            }
            // version_and_older
            if (
                restrictions.version_and_older &&
                restrictions.version_and_older.length > 0 &&
                mrbeam.comparePEP440Versions(
                    MRBEAM_PLUGIN_VERSION,
                    restrictions.version_and_older,
                    "__le__"
                )
            ) {
                return false;
            }
            // ts_after
            if (restrictions.ts_after) {
                if (typeof (restrictions.ts_after) === 'number' &&
                    Date.now() > restrictions.ts_after) {
                    return false;
                } else if (typeof (restrictions.ts_after) === 'string' &&
                    // Date: '2011-10-10T14:48:00'
                    Date.now() > Date.parse(restrictions.ts_after)) {
                    return false;
                }
            }
            // ts_before
            if (restrictions.ts_before) {
                if (typeof (restrictions.ts_before) === 'number' &&
                    Date.now() < restrictions.ts_before) {
                    return false;
                } else if (typeof (restrictions.ts_before) === 'string' &&
                    Date.now() < Date.parse(restrictions.ts_before)) {
                    return false;
                }
            }
            // not_first_run
            if (restrictions.not_first_run && !CONFIG_FIRST_RUN) {
                return false;
            }
            return true;
        };

        self.showNotifications = function () {
            if (!self.notificationsHandled && self.messagesLoaded) {
                var lmid = -1;
                self.messages().forEach(function (myMessage) {
                    lmid = Math.max(lmid, myMessage.id);
                    if (myMessage.notification && myMessage.id > self.lastMessageId) {
                        try {
                            new PNotify({
                                title: myMessage.notification.title || '',
                                text: myMessage.notification.body || '',
                                type: myMessage.notification.type || 'info',
                                hide: false,
                                delay: myMessage.notification.delay || 10 * 1000,
                            });
                        } catch (e) {
                            console.error("Error showing notification for message id " + myMessage.id + ": ", e);
                        }
                    }
                });
                self.notificationsHandled = true;
                self.lastMessageId = lmid > 0 ? lmid : self.lastMessageId;
                self.saveUserSettings();
            } else {
                console.log("showNotifications() skipping");
            }
        };

        self.saveUserSettings = function () {
            // get unread messages Ids
            let unreadIds = self.getArray(self.messagesIds());
            if (unreadIds.length === 0) {
                unreadIds = null;
                self.hasUnread(false);
            } else {
                self.hasUnread(true);
            }
            // save to user settings
            if (self.loginState.currentUser()) {
                var mrbSettings = self.loginState.currentUser().settings.mrbeam;
                mrbSettings.messages = {
                    lastId: self.lastMessageId,
                    unreadIds: unreadIds
                };
                self.userSettings.updateSettings(self.loginState.currentUser().name, {mrbeam: mrbSettings});
            }
        };

        self.onIndexSelected = function (index, data, event) {
            // add message read class
            $(event.currentTarget).parent().addClass("mrb-message-read");
            // update selected index
            this.selectedIndex(index);
            // update user read message data
            let UnreadMessageIds = self.arrayRemove(self.getArray(self.messagesIds()), self.messages()[index].id);
            self.messagesIds(UnreadMessageIds);
            self.saveUserSettings();
        };

        self.selectedIndex.subscribe(function (result) {
            setTimeout(() => {
                let thumbnailWidth = $("#messages .thumbnails").width();
                let imageCount = self.messages()[result].images.length;
                $("#messages .thumbnails  li").width(Math.floor(((thumbnailWidth - 10 * (imageCount - 1)) / imageCount)) - 1);
            }, 100);
        });

        self.selectImage = function (img_url) {
            let imagePreview = $("#design-img-preview");
            imagePreview.css("background-image", "url('" + img_url + "')");
        };

        self.getArray = function (KOObservableArray) {
            let array = [];
            KOObservableArray.forEach(function (id) {
                array.push(id);
            });
            return array;
        };

        self.arrayRemove = function (arr, value) {
            return arr.filter(function (ele) {
                return ele !== value;
            });
        };

    }

    // view model class, parameters for constructor, container to bind to
    OCTOPRINT_VIEWMODELS.push([
        MessagesViewModel,

        // e.g. loginStateViewModel, settingsViewModel, ...
        ["settingsViewModel", "userSettingsViewModel", "loginStateViewModel"],

        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        ["#messages", "#messages_nav_tab", "#messages_burger_menu"]
    ]);
});
