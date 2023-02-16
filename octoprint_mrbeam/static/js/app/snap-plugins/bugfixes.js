Snap.plugin(function (Snap, Element, Paper, global) {
    var elproto = Element.prototype;

    /** Original Function
     *
     * @returns {String}
     * @bug: escaping of quotes " in attributes fails
     * @bug: resulting svg is lacking referenced elements from <defs> and namespace declarations
    proto.toDataURL = function () {
        if (window && window.btoa) {
            return "data:image/svg+xml;base64," + btoa(unescape(encodeURIComponent(this)));
        }
    };
    */
    elproto.toDataURLfixed = function (additionalNamespaces = "") {
        if (window && window.btoa) {
            const cnt = this.outerSVG().replaceAll('\\"', "'"); // <text style="font-family: \"Allerta Stencil\"; "> => <text style="font-family: 'Allerta Stencil'; ">
            var bb = this.getBBox(),
                svg = Snap.format(
                    '<svg version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" ' +
                        additionalNamespaces +
                        ' width="{width}" height="{height}" viewBox="{x} {y} {width} {height}">{contents}</svg>',
                    {
                        x: +bb.x.toFixed(3),
                        y: +bb.y.toFixed(3),
                        width: +bb.width.toFixed(3),
                        height: +bb.height.toFixed(3),
                        contents: cnt,
                    }
                );
            return (
                "data:image/svg+xml;base64," +
                btoa(unescape(encodeURIComponent(svg)))
            );
        }
    };
});
