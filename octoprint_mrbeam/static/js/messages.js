/*
 * View model for Mr Beam
 *
 * Author: Andy Werner <andy@mr-beam.org>
 */
/* global OctoPrint, OCTOPRINT_VIEWMODELS */

$(function () {
    function MessagesViewModel(parameters) {
        let self = this;
        window.mrbeam.viewModels['messagesViewModel'] = self;

        const MESSAGES_URL = "/plugin/mrbeam/static/messages/messages.json";
        // const MESSAGES_URL = "https://messages.beamos.mr-beam.org/messages.json";

        self.settings = parameters[0];
        self.userSettings = parameters[1];
        self.loginState = parameters[2];

        self.messages = ko.observableArray();
        self.messagesIds = ko.observableArray();
        self.selectedIndex = ko.observable();
        self.unreadCounter = ko.observable(0);
        self.lastMessageId = -1;
        self.oldUnreadMessageIds = -1;
        self.notificationsHandled = false;
        self.messagesLoaded = false;

        self.onStartupComplete = function () {
            // self.loadRemoteMessages();
        };

        self.onUserLoggedIn = function (user) {
            // self.lastMessageId = user.settings.mrbeam.messages ? user.settings.mrbeam.messages.lastId : 0
            // console.log("ANDYTEST: onUserLoggedIn()  user: ", user);
            if (user.settings.mrbeam.messages) {
                self.lastMessageId = user.settings.mrbeam.messages.lastId;
                self.oldUnreadMessageIds = user.settings.mrbeam.messages.unreadIds;
            }
            // console.log("ANDYTEST: onUserLoggedIn()  lastMessageId: ", self.lastMessageId);
            // self.showNotifications();
            console.log("--------------------> Old unread message Ids: ", self.oldUnreadMessageIds);

            //-------------
            if (!self.messagesLoaded) {
                self.loadRemoteMessages();
            }
            //-------------
        };

        self.saveUserSettings = function () {

            let unreadIds = [];
            self.messagesIds().forEach(function (id) {
                unreadIds.push(id);
            });

            if (unreadIds.length === 0) {
                unreadIds = null;
            }

            if (self.loginState.currentUser()) {
                var mrbSettings = self.loginState.currentUser().settings.mrbeam;
                mrbSettings.messages = {
                    lastId: self.lastMessageId,
                    unreadIds: unreadIds
                };
                self.userSettings.updateSettings(self.loginState.currentUser().name, {mrbeam: mrbSettings});
            }
        };

        self.loadRemoteMessages = function () {
            fetch(MESSAGES_URL, {
                method: 'GET'
            }).then(function (response) {
                return response.json();
            }).then(function (json) {
                console.log("--------------------> Remote Messages loaded: ", json);
                // console.log("--------------------> last remote ID: ", json.messages.sort((a, b) => (a.id > b.id) ? 1 : -1).pop().id);
                // console.log("--------------------> last local ID: ", self.lastMessageId);
                // if(json.messages.sort((a, b) => (a.id > b.id) ? 1 : -1).pop().id > self.lastMessageId){
                //     console.log("--------------------> There are new Messages ==> Save them");
                // self.saveNewMessages(json);
                self.handleMessages(json);
                // }else{
                //     console.log("--------------------> There are no new Messages ==> Load local messages");
                //     self.loadLocalMessages();
                // }
            }).catch(function (exception) {
                console.log("--------------------> Remote Messages loading failed! Loading Local Messages");
                console.log(exception);
                self.loadLocalMessages();
            });
        };

        self.loadLocalMessages = function () {
            OctoPrint.simpleApiCommand("mrbeam", "messages", {})
                .done(function (data) {
                    console.log("--------------------> Local Messages loaded: ", data);
                    self.handleMessages(data);
                })
                .fail(function (response) {
                    console.log("--------------------> Local Messages loading failed!");
                    console.log(response);
                });
        };

        self.saveNewMessages = function (data) {

            // let messages = {};
            // for (let i in data.messages) {
            //     if (data.messages.hasOwnProperty(i)){
            //         messages[i] = data.messages[i];
            //     }
            // }

            let messages = {};
            for (let i in data) {
                if (data.hasOwnProperty(i)) {
                    messages[i] = data[i];
                }
            }

            console.log("--------------------> THIS : ", messages);

            let postData = {
                put: messages,
                delete: []
            };

            OctoPrint.simpleApiCommand("mrbeam", "messages", postData)
                .done(function (response) {
                    console.log("--------------------> Saved Remote Messages loaded: ", response);
                    // self.handleMessages(response);
                })
                .fail(function (response) {
                    console.log("--------------------> Saving Remote Messages failed! Loading Local Messages");
                    // self.loadLocalMessages();
                });
        };

        self.handleMessages = function (data) {

            data.messages = Object.values(data.messages);

            if (data && data.messages) {
                let result = [];
                let messageIds = [];
                data.messages.forEach(function (myMessage) {
                    if (self.checkRestriction(myMessage.restrictions)) {
                        var msgObj = {
                            id: myMessage.id,
                            date: myMessage.date,
                            content: null,
                            images: myMessage.content.images || [],
                            notification: null,
                            read: false
                        };

                        var myLocale = LOCALE in myMessage.content ? LOCALE : 'en';

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
                                    sticky: 30, // TODO
                                    type: 'info', // TODO
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
                        }else{
                            msgObj.read = true;
                        }

                        result.push(msgObj);
                        self.messagesLoaded = true;
                    }
                });

                result.sort(function (a, b) {
                    // latest message at the top
                    if (a.id === b.id) {
                        return 0;
                    }
                    return a.id < b.id ? 1 : -1;
                });

                // if (self.oldUnreadMessageIds === -1) {
                console.log("--------------------> messageIds", messageIds);
                    self.messagesIds(messageIds);
                // }

                self.messages(result);

                // console.log("--------------------> new: ", result);
                self.saveNewMessages(result);

                console.log("--------------------> Show Notifications");

                self.showNotifications();

                //-------------
                // $(".item:first-child").addClass("active");
                // $('.carousel').carousel({
                //     interval: false
                // });
                //-------------

            }
        };

        self.getArray = function (KOObservableArray) {
            let array = [];
            KOObservableArray.forEach(function (id) {
                array.push(id);
            });
            return array;
        };

        self.showNotifications = function () {
            console.log("--------------------> showNotifications() notificationsHandled: " + self.notificationsHandled + ", messagesLoaded: " + self.messagesLoaded);
            if (!self.notificationsHandled && self.messagesLoaded) {
                var lmid = -1;
                self.messages().forEach(function (myMessage) {
                    lmid = Math.max(lmid, myMessage.id);
                    if (myMessage.notification && myMessage.id > self.lastMessageId) {
                        try {
                            new PNotify({
                                // TODO
                                title: myMessage.notification.title || '',
                                text: myMessage.notification.body || '',
                                type: myMessage.notification.type || 'info',
                                hide: false,
                                delay: myMessage.notification.delay || 10 * 1000,
                            });
                        } catch (e) {
                            console.error("Error showing notification for message id " + myMessage.id + ": ", e);
                        }
                        self.unreadCounter(self.unreadCounter() + 1);
                    }
                });
                self.notificationsHandled = true;
                self.lastMessageId = lmid > 0 ? lmid : self.lastMessageId;
                console.log("--------------------> self.lastMessageId: ", self.lastMessageId);
                self.saveUserSettings();
            } else {
                console.log("--------------------> showNotifications() skipping");
            }
        };

        self.checkRestriction = function (restrictions) {
            if (!restrictions) {
                return true;
            }

            // channel
            if (restrictions.channels && restrictions.channels.length > 0 && !restrictions.channels.map(function (x) {
                return x.trim().toUpperCase();
            }).includes(MRBEAM_SW_TIER)) {
                return false;
            }

            // version
            if (restrictions.version && restrictions.version.length > 0 && !restrictions.version.map(function (x) {
                return x.trim().toUpperCase();
            }).includes(BEAMOS_VERSION)) {
                return false;
            }

            // version_and_newer
            if (restrictions.version_and_newer && restrictions.version_and_newer.length > 0 &&
                !window.mrbeam._isVersionOrHigher(BEAMOS_VERSION, restrictions.version_and_newer)) {
                return false;
            }

            // version_and_older
            if (restrictions.version_and_older && restrictions.version_and_older.length > 0 &&
                !window.mrbeam._isVersionOrLower(BEAMOS_VERSION, restrictions.version_and_older)) {
                return false;
            }

            // ts_after
            if (restrictions.ts_after) {
                if (typeof (restrictions.ts_after) === 'number' &&
                    Date.now() / 1000 < restrictions.ts_after) {
                    return false;
                } else if (typeof (restrictions.ts_after) === 'string' &&
                    Date.now() < Date.parse('2011-10-10T14:48:00')) {
                    return false;
                } else {
                    return false;
                }
            }

            // ts_before
            if (restrictions.ts_after) {
                if (typeof (restrictions.ts_after) === 'number' &&
                    Date.now() / 1000 > restrictions.ts_after) {
                    return false;
                } else if (typeof (restrictions.ts_after) === 'string' &&
                    Date.now() > Date.parse('2011-10-10T14:48:00')) {
                    return false;
                } else {
                    return false;
                }
            }

            // not_first_run
            if (restrictions.not_first_run && CONFIG_FIRST_RUN) {
                return false;
            }

            return true;
        };

        // self.onIndexSelected = function (index) {
        self.onIndexSelected = function (index, data, event) {
            // add message read class
            $(event.currentTarget).addClass("mrb-message-read");

            // update selected index
            this.selectedIndex(index);

            // update user read message data
            let UnreadMessageIds = arrayRemove(self.getArray(self.messagesIds()), self.messages()[index].id);
            self.messagesIds(UnreadMessageIds);
            self.saveUserSettings();
        };

        function arrayRemove(arr, value) {
            return arr.filter(function (ele) {
                return ele !== value;
            });
        }

        self.selectedIndex.subscribe(function (result) {
            setTimeout(() => {
                let thumbnailWidth = $("#messages .thumbnails").width();
                let imageCount = self.messages()[result].images.length;
                // $("#messages .thumbnails  li").width(Math.floor(((thumbnailWidth - 20*(imageCount-1))/imageCount))-1);
                $("#messages .thumbnails  li").width(Math.floor(((thumbnailWidth - 10 * (imageCount - 1)) / imageCount)) - 1);
            }, 100);
        });

        self.selectImage = function (img_url) {
            let imagePreview = $("#design-img-preview");
            imagePreview.css("background-image", "url('" + img_url + "')");
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
