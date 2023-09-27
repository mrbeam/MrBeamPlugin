ko.components.register('laser-cutter-mode-switch', {
    viewModel: function(params) {
        let self = this;

        console.log('############# LIKE WIDGET #############');
        // Data: value is either null, 'like', or 'dislike'
        self.selectedMode = 'default';

        // Behaviors
        self.changeMode = function () {
            console.log('########### change mode to ' + self.selectedMode);
        };
    },
    template:
        '<select id="laser_cutter_mode_select" data-test="laser-cutter-mode-select" data-bind="value: selectedMode, event:{ change: changeMode}">\
            <option value="default">{{ _(\'Default\') }}</option>\
            <option value="rotary">{{ _(\'Rotary\') }}</option>\
        </select>'
});
