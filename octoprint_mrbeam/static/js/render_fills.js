//    render_fills.js - a snapsvg.io plugin to render the infill of svg files into a bitmap.
//    Copyright (C) 2015  Teja Philipp <osd@tejaphilipp.de>
//
//    based on work by http://davidwalsh.name/convert-canvas-image
//    and http://getcontext.net/read/svg-images-on-a-html5-canvas
//
//    This program is free software: you can redistribute it and/or modify
//    it under the terms of the GNU Affero General Public License as
//    published by the Free Software Foundation, either version 3 of the
//    License, or (at your option) any later version.
//
//    This program is distributed in the hope that it will be useful,
//    but WITHOUT ANY WARRANTY; without even the implied warranty of
//    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//    GNU Affero General Public License for more details.
//
//    You should have received a copy of the GNU Affero General Public License
//    along with this program.  If not, see <http://www.gnu.org/licenses/>.

Snap.plugin(function (Snap, Element, Paper, global) {
    /**
     * @param {boolean} fillPaths true if filledPaths should be rastered
     *
     * @returns {set} set of elements to be rastered.
     */

    Element.prototype.removeUnfilled = function (fillPaths) {
        var elem = this;
        var selection = [];
        var children = elem.children();

        if (children.length > 0) {
            var goRecursive =
                elem.type !== "defs" && // ignore these tags
                elem.type !== "clipPath" &&
                elem.type !== "metadata" &&
                elem.type !== "rdf:rdf" &&
                elem.type !== "cc:work" &&
                elem.type !== "sodipodi:namedview";

            if (goRecursive) {
                for (var i = 0; i < children.length; i++) {
                    var child = children[i];
                    selection = selection.concat(
                        child.removeUnfilled(fillPaths)
                    );
                }
            }
        } else {
            if (
                elem.type === "image" ||
                elem.type === "text" ||
                elem.type === "#text"
            ) {
                selection.push(elem);
            } else {
                if (fillPaths && elem.is_filled()) {
                    //                    elem.attr("stroke", "none");
                    selection.push(elem);
                } else {
                    elem.remove();
                }
            }
        }
        return selection;
    };

    Element.prototype.markFilled = function (className, fillPaths) {
        var elem = this;
        var selection = [];
        var children = elem.children();
        if (elem.type === "desc") {
            return [];
        }

        if (children.length > 0) {
            var goRecursive =
                elem.type !== "defs" && // ignore these tags
                elem.type !== "clipPath" &&
                elem.type !== "metadata" &&
                elem.type !== "rdf:rdf" &&
                elem.type !== "cc:work" &&
                elem.type !== "sodipodi:namedview";

            if (goRecursive) {
                for (var i = 0; i < children.length; i++) {
                    var child = children[i];
                    selection = selection.concat(
                        child.markFilled(className, fillPaths)
                    );
                }
            }
        } else {
            if (
                elem.type === "image" ||
                elem.type === "text" ||
                elem.type === "#text"
            ) {
                if (elem.type === "#text") {
                    let parent = elem.parent();
                    console.log("Parent of #text:", parent);
                    parent.addClass(className);
                    selection.push(parent);
                } else {
                    elem.addClass(className);
                    selection.push(elem);
                }
            } else {
                if (fillPaths && elem.is_filled()) {
                    elem.addClass(className);
                    selection.push(elem);
                }
            }
        }
        return selection;
    };

    Element.prototype.is_filled = function () {
        var elem = this;

        // TODO text support
        // TODO opacity support
        if (
            elem.type !== "circle" &&
            elem.type !== "rect" &&
            elem.type !== "ellipse" &&
            elem.type !== "line" &&
            elem.type !== "polygon" &&
            elem.type !== "polyline" &&
            elem.type !== "path"
        ) {
            return false;
        }

        var fill = elem.attr("fill");
        var opacity = elem.attr("fill-opacity");

        if (fill !== "none") {
            if (opacity === null || opacity > 0) {
                return true;
            }
        }
        return false;
    };

    Element.prototype.embedImage = function () {
        let elem = this;
        if (elem.type !== "image") return;

        let url = null;
        if (elem.attr("xlink:href") !== null) {
            url = elem.attr("xlink:href");
        } else if (elem.attr("href") !== null) {
            url = elem.attr("href");
        }
        if (url === null || url.startsWith("data:")) {
            return;
        }

        let prom = loadImagePromise(url)
            .then(function (image) {
                var canvas = document.createElement("canvas");
                canvas.width = image.naturalWidth; // or 'width' if you want a special/scaled size
                canvas.height = image.naturalHeight; // or 'height' if you want a special/scaled size

                canvas.getContext("2d").drawImage(image, 0, 0);

                const ratio = getWhitePixelRatio(canvas);
                console.log(
                    `embedImage() white pixel ratio: ${(ratio * 100).toFixed(
                        2
                    )}%, total white pixel: ${
                        canvas.width * canvas.height * ratio
                    }, image:${image.src}`
                );

                var dataUrl = canvas.toDataURL("image/png");
                elem.attr("href", dataUrl);
                console.log("in then...", dataUrl);
                canvas.remove();
            })
            .catch(function (error) {
                console.error(
                    `Slicing Error - embedImage: error while loading image: ${error}`
                );
            });
        return prom;
    };

    Element.prototype.embedImage_XXX = function (callback) {
        var elem = this;
        if (elem.type !== "image") return;

        var url = elem.attr("href");
        var image = new Image();

        image.onload = function () {
            var canvas = document.createElement("canvas");
            canvas.width = this.naturalWidth; // or 'width' if you want a special/scaled size
            canvas.height = this.naturalHeight; // or 'height' if you want a special/scaled size

            canvas.getContext("2d").drawImage(this, 0, 0);

            // count ratio of white pixel
            var id = canvas
                .getContext("2d")
                .getImageData(0, 0, canvas.width, canvas.height).data;
            var countWhite = 0;
            var countNoneWhite = 0;
            for (var p = 0; p < id.length; p += 4) {
                id[p] == 255 &&
                id[p + 1] == 255 &&
                id[p + 2] == 255 &&
                id[p + 3] == 255
                    ? countWhite++
                    : countNoneWhite++;
            }
            var ratio = countWhite / (countNoneWhite + countWhite);
            console.log(
                "embedImage() white pixel ratio: " +
                    parseFloat(ratio * 100).toFixed(2) +
                    "%, total white pixel: " +
                    countWhite +
                    ", image:" +
                    this.src
            );

            var dataUrl = canvas.toDataURL("image/png");
            elem.attr("href", dataUrl);
            canvas.remove();
            if (typeof callback === "function") {
                console.log(
                    "embedImage() " +
                        canvas.width +
                        "*" +
                        canvas.height +
                        " px, dataurl: " +
                        getDataUriSize(dataUrl) +
                        ", image: " +
                        this.src
                );
                callback(elem.attr("id"));
            }
        };
        image.onerror = function () {
            console.error(
                "Slicing Error - embedImage: error while loading image: " +
                    this.src
            );
        };

        image.src = url;
    };

    //    Element.prototype.embedImage = function (callback) {
    //        var elem = this;
    //        if (elem.type !== "image") return;
    //
    //        var url = elem.attr("href");
    //        var image = new Image();
    //
    //        image.onload = function () {
    //            var canvas = document.createElement("canvas");
    //            canvas.width = this.naturalWidth; // or 'width' if you want a special/scaled size
    //            canvas.height = this.naturalHeight; // or 'height' if you want a special/scaled size
    //
    //            canvas.getContext("2d").drawImage(this, 0, 0);
    //
    //            // count ratio of white pixel
    //            var id = canvas
    //                .getContext("2d")
    //                .getImageData(0, 0, canvas.width, canvas.height).data;
    //            var countWhite = 0;
    //            var countNoneWhite = 0;
    //            for (var p = 0; p < id.length; p += 4) {
    //                id[p] == 255 &&
    //                id[p + 1] == 255 &&
    //                id[p + 2] == 255 &&
    //                id[p + 3] == 255
    //                    ? countWhite++
    //                    : countNoneWhite++;
    //            }
    //            var ratio = countWhite / (countNoneWhite + countWhite);
    //            console.log(
    //                "embedImage() white pixel ratio: " +
    //                    parseFloat(ratio * 100).toFixed(2) +
    //                    "%, total white pixel: " +
    //                    countWhite +
    //                    ", image:" +
    //                    this.src
    //            );
    //
    //            var dataUrl = canvas.toDataURL("image/png");
    //            elem.attr("href", dataUrl);
    //            canvas.remove();
    //            if (typeof callback === "function") {
    //                console.log(
    //                    "embedImage() " +
    //                        canvas.width +
    //                        "*" +
    //                        canvas.height +
    //                        " px, dataurl: " +
    //                        getDataUriSize(dataUrl) +
    //                        ", image: " +
    //                        this.src
    //                );
    //                callback(elem.attr("id"));
    //            }
    //        };
    //        image.onerror = function () {
    //            console.error(
    //                "Slicing Error - embedImage: error while loading image: " +
    //                    this.src
    //            );
    //        };
    //
    //        image.src = url;
    //    };

    Element.prototype.renderPNG = function (
        wPT,
        hPT,
        wMM,
        hMM,
        pxPerMM,
        renderBBoxMM = null
        //        callback = null
    ) {
        var elem = this;
        //console.info("renderPNG paper width", elem.paper.attr('width'), wPT);
        console.info(
            "renderPNG: SVG " +
                wPT +
                "*" +
                hPT +
                " (pt) with viewBox " +
                wMM +
                "*" +
                hMM +
                " (mm), rendering @ " +
                pxPerMM +
                " px/mm, cropping to bbox (mm): ",
            renderBBoxMM
        );

        let bboxFromElem = elem.getBBox();

        let bbox; // attention, this bbox uses viewBox coordinates (mm)
        if (renderBBoxMM === null) {
            // warning: correct result depends upon all resources (img, fonts, ...) have to be fully loaded already.
            bbox = elem.getBBox();
            console.log(
                "renderPNG(): fetched render bbox from element: ",
                bbox
            );
        } else {
            bbox = renderBBoxMM;
            console.log(
                "renderPNG(): got render bbox from caller: ",
                bbox,
                "(elem bbox is ",
                bboxFromElem,
                ")"
            );
        }

        // Quick fix: in some browsers the bbox is too tight, so we just add an extra 10% to all the sides, making the height and width 20% larger in total
        const enlargement_x = 0.4; // percentage of the width added to each side
        const enlargement_y = 0.4; // percentage of the height added to each side
        const x1 = Math.max(0, bbox.x - bbox.width * enlargement_x);
        const x2 = Math.min(wMM, bbox.x2 + bbox.width * enlargement_x);
        const w = x2 - x1;
        const y1 = Math.max(0, bbox.y - bbox.height * enlargement_y);
        const y2 = Math.min(wMM, bbox.y2 + bbox.height * enlargement_y);
        const h = y2 - y1;
        bbox.x = x1;
        bbox.y = y1;
        bbox.w = w;
        bbox.h = h;

        console.info(
            "enlarged renderBBox (in mm): " +
                bbox.w +
                "*" +
                bbox.h +
                " @ " +
                bbox.x +
                "," +
                bbox.y
        );

        // get svg as dataUrl
        var svgDataUri = elem.toDataURL();

        // init render canvas and attach to page
        var renderCanvas = document.createElement("canvas");
        renderCanvas.id = "renderCanvas";
        renderCanvas.width = bbox.w * pxPerMM;
        renderCanvas.height = bbox.h * pxPerMM;
        if (MRBEAM_DEBUG_RENDERING) {
            renderCanvas.style =
                "position: fixed; bottom: 0; left: 0; width: 95vw; border: 1px solid red;";
            renderCanvas.addEventListener("click", function () {
                this.remove();
            });
        }
        document.getElementsByTagName("body")[0].appendChild(renderCanvas);
        var renderCanvasContext = renderCanvas.getContext("2d");
        renderCanvasContext.fillStyle = "white"; // avoids one backend rendering step (has to be disabled in the backend)
        renderCanvasContext.fillRect(
            0,
            0,
            renderCanvas.width,
            renderCanvas.height
        );

        // TODO "preload" the quicktext fonts - otherwise async loading leads to unpredicted results.
        //        var link = document.createElement('link');
        //        link.rel = 'stylesheet';
        //        link.type = 'text/css';
        //        link.href = 'http://fonts.googleapis.com/css?family=Vast+Shadow';
        //        document.getElementsByTagName('head')[0].appendChild(link);
        //
        //        // Trick from https://stackoverflow.com/questions/2635814/
        //        var image = new Image();
        //        image.src = link.href;
        //        image.onerror = function () {
        //            ctx.font = '50px "Vast Shadow"';
        //            ctx.textBaseline = 'top';
        //            ctx.fillText('Hello!', 20, 10);
        //        };

        var source = new Image();

        // render SVG image to the canvas once it loads.
        let prom = new Promise(function (resolve, reject) {
            source.src = svgDataUri;
            source.onload = resolve();
            source.onerror = reject();
        })
            .then(
                // after onload
                function () {
                    const srcScale = wPT / wMM; // canvas.drawImage refers to <svg> coordinates - not viewBox coordinates.
                    const cx = bbox.x * srcScale;
                    const cy = bbox.y * srcScale;
                    const cw = bbox.w * srcScale;
                    const ch = bbox.h * srcScale;

                    // drawImage(source, src.x, src.y, src.width, src.height, dest.x, dest.y, dest.width, dest.height);
                    console.log(
                        "rasterizing: " +
                            cw +
                            "*" +
                            ch +
                            " @ " +
                            cx +
                            "," +
                            cy +
                            "(scale: " +
                            srcScale +
                            "+)"
                    );
                    renderCanvasContext.drawImage(
                        source,
                        cx,
                        cy,
                        cw,
                        ch,
                        0,
                        0,
                        renderCanvas.width,
                        renderCanvas.height
                    );

                    // place fill bitmap into svg
                    const fillBitmap = renderCanvas.toDataURL("image/png");
                    const size = getDataUriSize(fillBitmap);
                    console.info("renderPNG rendered dataurl has " + size);
                    //            if (typeof callback === "function") {
                    //                callback(fillBitmap, bbox.x, bbox.y, bbox.w, bbox.h);
                    //            }
                    if (!MRBEAM_DEBUG_RENDERING) {
                        renderCanvas.remove();
                    }
                    return { dataUrl: fillBitmap, size: size, bbox: bbox };
                },
                // after onerror
                function () {
                    // var len = svgDataUri ? svgDataUri.length : -1;
                    var len = getDataUriSize(svgDataUri, "B");
                    var msg =
                        "Error during conversion: Loading SVG dataUri into image element failed. (dataUri.length: " +
                        len +
                        ")";
                    console.error(msg, e);
                    console.debug(
                        "renderPNG ERR: original svgStr that failed to load: ",
                        svgStr
                    );
                    console.debug(
                        "renderPNG ERR: svgDataUri that failed to load: ",
                        svgDataUri
                    );
                    new PNotify({
                        title: gettext("Conversion failed"),
                        text: msg,
                        type: "error",
                        hide: false,
                    });
                }
            )
            .catch(function (error) {
                console.error(error);
            });

        return prom;
    };

    function getDataUriSize(datauri, unit) {
        if (!datauri) return -1;
        var bytes = datauri.length;
        switch (unit) {
            case "B":
                return bytes;
            case "kB":
                return Math.floor(bytes / 1024);
            case "MB":
                return Math.floor(bytes / (1024 * 1024));
            default:
                if (bytes < 1024) return bytes + " Byte";
                else if (bytes < 1024 * 1024)
                    return Math.floor(bytes / 1024) + " kByte";
                else return Math.floor(bytes / (1024 * 1024)) + " MByte";
        }
    }
});
