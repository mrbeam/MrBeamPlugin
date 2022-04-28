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

        var goRecursive =
            elem.type !== "defs" && // ignore these tags
            elem.type !== "clipPath" &&
            elem.type !== "metadata" &&
            elem.type !== "desc" &&
            elem.type !== "text" &&
            elem.type !== "rdf:rdf" &&
            elem.type !== "cc:work" &&
            elem.type !== "sodipodi:namedview" &&
            children.length > 0;

        if (goRecursive) {
            for (var i = 0; i < children.length; i++) {
                var child = children[i];
                selection = selection.concat(child.removeUnfilled(fillPaths));
            }
        } else {
            if (
                elem.type === "image" ||
                elem.type === "text" ||
                elem.type === "textPath" //||
                //                elem.type === "#text"
            ) {
                selection.push(elem);
            } else {
                if (fillPaths && elem.is_filled()) {
                    //                    elem.attr("stroke", "none");
                    selection.push(elem);
                } else {
                    if (elem.type !== "#text" && elem.type !== "defs") {
                        elem.remove();
                    }
                }
            }
        }
        return selection;
    };

    Element.prototype.markFilled = function (className, fillPaths) {
        var elem = this;
        var selection = [];
        var children = elem.children();
        if (elem.type === "desc" || elem.type === "style") {
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

    Element.prototype.splitRasterClusters = function (fillAreas) {
        const svg = this;
        let marked = svg.markFilled("toRaster", fillAreas);

        // cluster overlapping
        let clusterCount = 0;
        let clusters = [];
        for (let i = 0; i < marked.length; i++) {
            let rasterEl = marked[i];
            let bbox;
            try {
                bbox = rasterEl.get_total_bbox();
            } catch (error) {
                console.warn(
                    `Getting bounding box for ${rasterEl} failed.`,
                    error
                );
                continue;
            }
            // find overlaps
            let lastOverlap = -1;
            for (var j = 0; j < clusters.length; j++) {
                var cluster = clusters[j];
                if (Snap.path.isBBoxIntersect(cluster.bbox, bbox)) {
                    // TODO refined overlap method
                    if (lastOverlap === -1) {
                        // merge element in cluster (1st overlap)
                        cluster.bbox = Snap.path.merge_bbox(cluster.bbox, bbox);
                        cluster.elements.push(rasterEl);
                        lastOverlap = j;
                    } else {
                        // merge clusters (multiple overlaps)
                        cluster.bbox = Snap.path.merge_bbox(
                            cluster.bbox,
                            clusters[lastOverlap].bbox
                        );
                        cluster.elements = cluster.elements.concat(
                            clusters[lastOverlap].elements
                        );
                        clusters[lastOverlap] = null;
                        lastOverlap = j;
                    }
                }
            }
            clusters = clusters.filter((c) => c !== null);
            if (lastOverlap === -1) {
                // create new cluster
                clusters.push({ bbox: bbox, elements: [rasterEl] });
                clusterCount++;
            }
        }

        for (let c = 0; c < clusters.length; c++) {
            let cluster = clusters[c];
            cluster.elements.forEach((rasterEl) =>
                rasterEl.addClass(`rasterCluster${c}`)
            );
            let tmpSvg = svg.clone();
            tmpSvg.selectAll(`.toRaster:not(.rasterCluster${c})`).remove();
            // tmpSvg.selectAll(`.toRaster:not(.rasterCluster${c})`).forEach((element) => {
            //     let elementToBeRemoved = tmpSvg.select('#' + element.attr('id'));
            //     let elementsToBeExcluded = ["text", "tspan"]
            //     if (elementToBeRemoved && !elementsToBeExcluded.includes(elementToBeRemoved.type)) {
            //         elementToBeRemoved.remove();
            //     }
            // });
            // Fix IDs of filter references, those are not cloned correct (probably because reference is in style="..." definition)
            tmpSvg.fixIds("defs filter[mb\\:id]", "mb:id"); // namespace attribute selectors syntax: [ns\\:attrname]
            // DON'T fix IDs of textPath references, they're cloned correct.
            //tmpSvg.fixIds("defs .quicktext_curve_path", "[mb\\:id]");
            cluster.svg = tmpSvg;
        }
        //console.log("Clusters", clusters);
        return clusters;
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

    /**
     * Removes fill of element. In case element was a filled shape without stroke, element will be removed.
     * @returns {Boolean} if element was removed completely.
     */
    Element.prototype.unfillOrRemove = function () {
        let elem = this;

        // TODO opacity support
        if (
            elem.type !== "circle" &&
            elem.type !== "rect" &&
            elem.type !== "ellipse" &&
            elem.type !== "line" &&
            elem.type !== "polygon" &&
            elem.type !== "polyline" &&
            elem.type !== "path" &&
            elem.type !== "textPath" &&
            elem.type !== "text" &&
            elem.type !== "tspan" &&
            elem.type !== "image"
        ) {
            console.warn(`Element ${elem} is not a native type. Skip.`);
            return false;
        }

        const stroke = elem.attr("stroke");
        if (stroke !== "none") {
            elem.attr({ fill: "none" });
            return false;
        } else {
            elem.remove();
            return true;
        }
    };

    /**
     * Reads a linked image and embeds it with a dataUrl
     * @returns {Promise} Promise with the element or null in case of non-image element.
     */
    Element.prototype.embedImage = function () {
        let elem = this;
        if (elem.type !== "image") {
            console.warn(
                `embedImage only supports <image> elements. Got ${elem}`
            );
            return Promise.resolve(null);
        }

        let url = null;
        if (elem.attr("xlink:href") !== null) {
            url = elem.attr("xlink:href");
        } else if (elem.attr("href") !== null) {
            url = elem.attr("href");
        }
        if (url === null || url.startsWith("data:")) {
            console.info(`embedImage: nothing do to. Url was ${url}`);
            return Promise.resolve(elem);
        }

        let prom = loadImagePromise(url)
            .then(function (image) {
                let canvas = document.createElement("canvas");
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

                const dataUrl = canvas.toDataURL("image/png");
                elem.attr("href", dataUrl);
                canvas.remove();
                return elem;
            })
            .catch(function (error) {
                console.error(
                    `Slicing Error - embedImage: error while loading image: ${error}`
                );
            });
        return prom;
    };

    Element.prototype.renderPNG = function (
        clusterIdx,
        wPT,
        hPT,
        wMM,
        hMM,
        pxPerMM,
        renderBBoxMM = null
    ) {
        var elem = this;
        //console.info("renderPNG paper width", elem.paper.attr('width'), wPT);
        console.debug(
            `renderPNG: SVG ${wPT} * ${hPT} (pt) with viewBox ${wMM} * ${hMM} (mm), rendering @ ${pxPerMM} px/mm, cropping to bbox (mm): ${renderBBoxMM}`
        );

        let bboxFromElem = elem.getBBox();

        let bbox; // attention, this bbox uses viewBox coordinates (mm)
        if (renderBBoxMM === null) {
            // warning: correct result depends upon all resources (img, fonts, ...) have to be fully loaded already.
            bbox = elem.getBBox();
            //console.log(`renderPNG(): fetched render bbox from element: ${bbox}`);
        } else {
            bbox = renderBBoxMM;
            //            console.log(
            //                `renderPNG(): got render bbox from caller: ${bbox}, (elem bbox is ${bboxFromElem})`
            //            );
        }

        // only enlarge on fonts, images not necessary.
        const doEnlargeBBox =
            elem.selectAll("text").filter((e) => {
                const bb = e.getBBox();
                // this filter is required, as every quick text creates an empty text element (for switching between curved and straight text)
                return bb.width > 0 && bb.height > 0;
            }).length > 0;

        // Quick fix: in some browsers the bbox is too tight, so we just add an extra margin to all the sides, making the height and width larger in total
        const enlargement_x = doEnlargeBBox ? 0.4 : 0; // percentage of the width added to each side
        const enlargement_y = doEnlargeBBox ? 0.4 : 0; // percentage of the height added to each side
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

        //        console.debug(
        //            `enlarged renderBBox (in mm): ${bbox.w}*${bbox.h} @ ${bbox.x},${bbox.y}`
        //        );

        // get svg as dataUrl
        var svgDataUri = elem.toDataURL(); // TODO remove comment. OK here

        // init render canvas and attach to page
        var renderCanvas = document.createElement("canvas");
        renderCanvas.id = `renderCanvas_${clusterIdx}`;
        renderCanvas.class = "renderCanvas";
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
        //        renderCanvasContext.fillStyle = "white"; // avoids one backend rendering step (has to be disabled in the backend)
        //        renderCanvasContext.fillRect(
        //            0,
        //            0,
        //            renderCanvas.width,
        //            renderCanvas.height
        //        );

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

        let prom = loadImagePromise(svgDataUri)
            .then(
                function (imgTag) {
                    try {
                        const srcScale = wPT / wMM; // canvas.drawImage refers to <svg> coordinates - not viewBox coordinates.
                        const cx = bbox.x * srcScale;
                        const cy = bbox.y * srcScale;
                        const cw = bbox.w * srcScale;
                        const ch = bbox.h * srcScale;

                        //                        console.debug(
                        //                            `rasterizing: ${cw}*${ch} @ ${cx},${cy} (scale: ${srcScale})`
                        //                        );
                        // drawImage(source, src.x, src.y, src.width, src.height, dest.x, dest.y, dest.width, dest.height);
                        renderCanvasContext.drawImage(
                            imgTag,
                            cx,
                            cy,
                            cw,
                            ch,
                            0,
                            0,
                            renderCanvas.width,
                            renderCanvas.height
                        );
                    } catch (exception) {
                        console.error(
                            "renderCanvasContext.drawImage failed:",
                            exception
                        );
                    }

                    // place fill bitmap into svg
                    const fillBitmap = renderCanvas.toDataURL("image/png");
                    const size = getDataUriSize(fillBitmap);
                    //                    console.debug("renderPNG rendered dataurl has " + size);

                    renderCanvas.remove();
                    return {
                        dataUrl: fillBitmap,
                        size: size,
                        bbox: bbox,
                        clusterIndex: clusterIdx,
                    };
                },
                // after onerror
                function (e) {
                    // var len = svgDataUri ? svgDataUri.length : -1;
                    var len = getDataUriSize(svgDataUri, "B");
                    var msg =
                        "Error during conversion: Loading SVG dataUri into image element failed in renderPNG. (dataUri.length: " +
                        len +
                        ")";
                    console.error(msg, e);
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
                    if (!MRBEAM_DEBUG_RENDERING) {
                        renderCanvas.remove();
                    }
                }
            )
            .catch(function (error) {
                console.error(error);
            });

        return prom;
    };

    Element.prototype.fixIds = function (selector, srcIdAttr) {
        const root = this;
        let elemsToFix = root.selectAll(selector);
        for (let i = 0; i < elemsToFix.length; i++) {
            const e = elemsToFix[i];
            const originalId = e.attr(srcIdAttr);
            if (originalId !== null && originalId !== "") {
                e.attr({ id: originalId });
            }
            //console.log(`fixed Id: ${e.type}#${originalId}`);
        }
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
