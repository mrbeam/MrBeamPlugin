(function ($) {
    /**
     * Gets the property styling value of an element
     *
     * @param {String} prop
     * @returns {Object} : an array of stroke styling objects
     */
    $.fn.getInlineStyle = function (prop) {
        return this.prop("style")[$.camelCase(prop)];
    };
})(jQuery);
