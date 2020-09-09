/*
 * View model for Mr Beam
 *
 * Author: Andy Werner <andy@mr-beam.org>
 */
/* global OctoPrint, OCTOPRINT_VIEWMODELS */

$(function () {
	function MessagesViewModel(parameters) {
		var self = this;
		window.mrbeam.viewModels['messagesViewModel'] = self;

		// MESSAGES_URL = "/plugin/mrbeam/static/messages/messages.json";
		MESSAGES_URL = "https://messages.beamos.mr-beam.org/messages.json";

		self.settings = parameters[0];
		self.userSettings = parameters[1];
		self.loginState = parameters[2];

		self.messages = ko.observableArray();
		// self.localMessages = ko.observable({});
		// self.remoteMessages = ko.observable({});
		self.unreadCounter = ko.observable(0);
		// self.currentUser = ko.observable(null)
		self.lastMessageId = -1;
		self.notificationsHandled = false;
		self.messagesLoaded = false;


		self.onStartupComplete = function () {
			// self.loadMessageData();
            // self.loadLocalMessages();
            self.loadRemoteMessages();
			// self.test()
		};

		self.onUserLoggedIn = function (user) {
			// self.lastMessageId = user.settings.mrbeam.messages ? user.settings.mrbeam.messages.lastId : 0
			console.log("ANDYTEST: onUserLoggedIn()  user: ", user);
			if (user.settings.mrbeam.messages) {
				self.lastMessageId = user.settings.mrbeam.messages.lastId;
			}
			console.log("ANDYTEST: onUserLoggedIn()  lastMessageId: ", self.lastMessageId);
			self.showNotifications();
		};

		self.saveUserSettings = function () {
			if (self.loginState.currentUser()) {
				var mrbSettings = self.loginState.currentUser().settings.mrbeam;
				mrbSettings.messages = {
					lastId: self.lastMessageId
				};
				self.userSettings.updateSettings(self.loginState.currentUser().name, {mrbeam: mrbSettings});
			}
		};

		// self.loadMessageData = function () {
			// $.ajax({
			// 	type: "GET",
			// 	async: true,
            //     contentType: "application/json",
            //     dataType: 'json',
			// 	url: MESSAGES_URL,
			// 	// url: MESSAGES_URL + Date.now(),
			// 	// url: "/plugin/mrbeam/static/messages/messages.json?ts=" + Date.now(),
			// })
			// .done(function (data) {
			// 	console.log("Messages loaded: ", data);
			// 	self.handleMessages(data)
			// })
			// .fail(function () {
			// 	console.log("Messages loading failed!");
			// });

           // self.loadLocalMessages();

		// };

		self.loadLocalMessages = function () {
            OctoPrint.simpleApiCommand("mrbeam", "messages", {})
            .done(function (data) {
                console.log("Local Messages loaded: ", data);
                // self.localMessages(data);
                // self.loadRemoteMessages();
                self.handleMessages(data);
            })
            .fail(function (response) {
                console.log("Local Messages loading failed!");
                console.log(response);
            });
        };

		self.loadRemoteMessages = function () {
		     fetch(MESSAGES_URL, {
                method: 'GET'
            }).then(function (response) {
                return response.json();
            }).then(function (json) {
                console.log("Remote Messages loaded: ", json);
				self.saveNewMessages(json);
            }).catch(function (exception) {
                console.log("Remote Messages loading failed! Loading Local Messages");
                console.log(exception);
                self.loadLocalMessages();
            });
        };

		self.saveNewMessages = function (data) {

		    let messages = {};
		    for (let i in data.messages) {
		        if (data.messages.hasOwnProperty(i)){
                    messages[i] = data.messages[i];
                }
            }

		    let postData = {
                        // put: data.messages,
                        put: messages,
                        delete: []
                    };
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

		self.handleMessages = function (data) {

            data.messages =  Object.values(data.messages);

			if (data && data.messages) {
				var result = [];
				data.messages.forEach(function (myMessage) {
					if (self.checkRestriction(myMessage.restrictions)) {
						var msgObj = {
							id: myMessage.id,
							date: myMessage.date,
							content: null,
							images: myMessage.content.images || [],
							notification: null,
						};

						var myLocale = LOCALE in myMessage.content ? LOCALE : 'en';

						// content
						if (myMessage.content && myMessage.content[myLocale]) {
							msgObj.content = {
								title: myMessage.content[myLocale].title,
								body: myMessage.content[myLocale].body
							};
							if(myMessage.content[myLocale].cta){
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

				self.messages(result);
				self.showNotifications();
			}
		};

		self.showNotifications = function () {
			console.log("ANDYTEST showNotifications() notificationsHandled: " + self.notificationsHandled + ", messagesLoaded: " + self.messagesLoaded);
			if (!self.notificationsHandled && self.messagesLoaded) {
				var lmid = -1;
				self.messages().forEach(function (myMessage) {
					if (myMessage.notification && myMessage.id > self.lastMessageId) {
						lmid = Math.max(lmid, myMessage.id);
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
				self.saveUserSettings();
			} else {
				console.log("ANDYTEST showNotifications() skipping");
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
                if (typeof(restrictions.ts_after) === 'number' &&
                    Date.now()/1000 > restrictions.ts_after){
                    return false;
                } else if (typeof(restrictions.ts_after) === 'string' &&
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

		self.fold_all_messages = function () {
			$('#message_list .message').removeClass('unfold');
		};

		self.unfold_message = function (data, event) {
			if (!event.currentTarget.classList.contains('unfold')) {
				self.fold_all_messages();
				event.currentTarget.classList.add('unfold');
				let scrollPos = $(event.currentTarget).offset().top - 150; // TODO magic number
				$('#message_list').animate({
					scrollTop: scrollPos
				}, 500);
			}
		};

		self.img_clicked = function (data, event) {
			let el = event.currentTarget.closest('.message').querySelector('.message_pic');
			el.style.opacity = 0;
			setTimeout(function(){
				el.style.backgroundImage = 'url('+data+')';
				el.style.opacity = 1;
			}, 200); // has to be the same duration as in the css transition: opacity of .message_pic
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
