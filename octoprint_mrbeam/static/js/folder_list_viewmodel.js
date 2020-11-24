$(function () {
    function FolderListViewModel(parameters) {
        var self = this;
        window.mrbeam.viewModels["folderListViewModel"] = self;

        self.files = parameters[0];
        //		self.allViewModels = null;

        self.foldersOnlyABCList = ko.dependentObservable(function () {
            //			var filter = function(data) { return data["type"] && data["type"] === "folder"; };
            var sorter = function (a, b) {
                // sorts ascending
                if (a["display"].toLowerCase() < b["display"].toLowerCase())
                    return -1;
                if (a["display"].toLowerCase() > b["display"].toLowerCase())
                    return 1;
                return 0;
            };
            let items = self.files.foldersOnlyList();
            //			let folders = _.filter(items, filter);
            return items.sort(sorter);
        });
        //		self.foldersOnlyList = ko.dependentObservable(function () {
        //			let filter = function (data) { return data["type"] && data["type"] === "folder"; };
        //			let filtered _.filter(self.listHelper.paginatedItems(), filter);
        //        });

        self.onBeforeBinding = function () {
            // forwarders to the files viewmodel
            self.listHelper = self.files.listHelper;
            self.getEntryId = self.files.getEntryId;
            self.templateFor = self.files.templateFor;
            self.updateSelection = self.files.updateSelection;
            self.cancelSelection = self.files.cancelSelection;
            self.changeFolder = self.files.changeFolder;
            self.enableRemove = self.files.enableRemove;
            self.removeFolder = self.files.removeFolder;
            self.hideAndRemoveFolder = self.files.hideAndRemoveFolder;
        };
    }

    // view model class, parameters for constructor, container to bind to
    OCTOPRINT_VIEWMODELS.push([
        FolderListViewModel,

        // e.g. loginStateViewModel, settingsViewModel, ...
        ["filesViewModel"],

        // e.g. #settings_plugin_mrbeam, #tab_plugin_mrbeam, ...
        [document.getElementById("onlyFoldersList")],
    ]);
});
