/* This is a jQuery plugin that enables easy handling of elements and their styling */
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
    /**
     * Gets all element styles and their property values for styles including a certain keyword
     *
     * @param {...string} keyword
     * @returns {Object} : an array of styling objects
     */
    $.fn.getAllStylesIncluding = function (keyword) {
        const element = this[0];
        const computedStyles = window.getComputedStyle(element);
        const styles = [];

        for (const style in computedStyles) {
            if (
                computedStyles.hasOwnProperty(style) &&
                style.includes(keyword)
            ) {
                styles.push({ [style]: computedStyles[style] });
            }
        }

        return styles;
    };
    /**
     * Set styling property of an element to a certain value
     *
     * @param {...string} style
     * @param {...*} styleValue
     * @returns {undefined}
     */
    $.fn.setStyleValue = function (style, styleValue) {
        const element = this[0];
        element.style.setProperty(style, styleValue);
    };
    /**
     * Set styling value of an element to default
     *
     * @param {...string} style
     * @returns {undefined}
     */
    $.fn.setDefaultStyleValue = function (style) {
        const element = this[0];
        element.style.setProperty(style, null);
    };
})(jQuery);
