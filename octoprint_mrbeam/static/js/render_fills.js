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

    Element.prototype.markFilled = function (className, fillPaths) {
        var elem = this;
        var selection = [];
        var children = elem.children();
        if (
            elem.type === "desc" ||
            elem.type === "style" ||
            elem.type === "title"
        ) {
            return [];
        }

        if (children.length > 0 && elem.type !== "text") {
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
            if (elem.is_filled()) {
                if (
                    elem.type === "image" ||
                    elem.type === "text" ||
                    elem.type === "textPath" //||
                ) {
                    elem.addClass(className);
                    selection.push(elem);
                } else {
                    if (fillPaths) {
                        if (elem.is_stroked()) {
                            // duplicate element to separate stroke from fill
                            const unstroked = elem.clone();
                            elem.attr("fill", "none");
                            unstroked.attr("stroke", "none");
                            unstroked.addClass(className);
                            unstroked.clean_gc(); // necessary?
                            selection.push(unstroked);
                        } else {
                            elem.addClass(className);
                            selection.push(elem);
                        }
                    }
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
            const bbox = rasterEl.get_total_bbox();
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
                clusters.push({
                    bbox: bbox,
                    elements: [rasterEl],
                    idx: clusterCount,
                });
                clusterCount++;
            }
        }

        clusters.forEach((cluster) => {
            cluster.elements.forEach((rasterEl) =>
                rasterEl.addClass(`rasterCluster${cluster.idx}`)
            );
        });
        return clusters;
    };

    Element.prototype.is_filled = function () {
        var elem = this;

        if (elem.type === "text") {
            const bb = elem.getBBox();
            if (bb.w === 0 || bb.h === 0) {
                return false;
            }
            const fill = window.getComputedStyle(elem.node)["fill"];
            const opacity = parseFloat(
                window.getComputedStyle(elem.node)["fill-opacity"]
            );
            if (fill === "none" || opacity === 0) {
                return false;
            }
            return true;
        }

        if (elem.type === "image") {
            const bb = elem.getBBox();
            if (bb.w === 0 || bb.h === 0) {
                return false;
            }
            const opacity = parseFloat(
                window.getComputedStyle(elem.node)["opacity"]
            );
            if (opacity === 0) {
                return false;
            }
            return true;
        }

        if (
            elem.type === "circle" ||
            elem.type === "rect" ||
            elem.type === "ellipse" ||
            elem.type === "line" ||
            elem.type === "polygon" ||
            elem.type === "polyline" ||
            elem.type === "path"
        ) {
            const bb = elem.getBBox();
            if (bb.w === 0 || bb.h === 0) {
                return false;
            }
            const opacity = parseFloat(
                window.getComputedStyle(elem.node)["fill-opacity"]
            );
            const fill = window.getComputedStyle(elem.node)["fill"];
            if (fill === "none" || opacity === 0) {
                return false;
            }
            return true;
        }

        return false;
    };

    Element.prototype.is_stroked = function () {
        var elem = this;

        if (
            elem.type === "circle" ||
            elem.type === "rect" ||
            elem.type === "ellipse" ||
            elem.type === "line" ||
            elem.type === "polygon" ||
            elem.type === "polyline" ||
            elem.type === "path"
        ) {
            const opacity = parseFloat(
                window.getComputedStyle(elem.node)["stroke-opacity"]
            );
            const stroke = window.getComputedStyle(elem.node)["stroke"];
            const width = parseFloat(
                window.getComputedStyle(elem.node)["stroke-width"]
            );
            if (
                stroke === "none" ||
                opacity === 0 ||
                isNaN(width) ||
                width <= 0
            ) {
                return false;
            }
            return true;
        }

        return false;
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
        if (url === null) {
            console.info(`embedImage, found empty url: ${url}`);
            return Promise.resolve(elem);
        }
        if (url.startsWith("data:")) {
            console.info(
                `embedImage: nothing do to. Url started with ${url.substr(
                    0,
                    50
                )}`
            );
            return Promise.resolve(elem);
        }

        let prom = url2png(url).then((dataUrl) => {
            elem.attr("href", dataUrl);
            return elem;
        });
        return prom;
    };

    Element.prototype.embedAllImages = async function () {
        const elem = this;
        const allImages = elem.selectAll("image").items;
        if (elem.type === "image") {
            allImages.push(elem);
        }
        console.log(`embedding Images 0/${allImages.length}}`);

        let pAll = await Promise.all(
            allImages.map(async (elem, idx) => {
                const embedded = await elem.embedImage();
                console.log(`embedding Image ${idx + 1}/${allImages.length}}`);
                return embedded;
            })
        );

        return pAll;
    };

    Element.prototype._renderPNG2 = async function (pxPerMM, margin) {
        var elem = this;

        elem.embedAllImages();
        const fontSet = elem.getUsedFonts();
        const fontDeclarations = WorkingAreaHelper.getFontDeclarations(fontSet);

        const wMM = 500; // TODO... should not be here. get from Param?
        const hMM = 390;
        const cropBB = { x: 0, y: 0, x2: wMM, y2: hMM };
        //        let bbox = elem.getBBox();
        let bbox = elem.get_total_bbox();
        let bboxMargin = 0;
        if (margin === null) {
            bboxMargin = fontSet.size > 0 ? 0.8 : 0;
        } else {
            bboxMargin = margin;
        }

        const bboxMM = Snap.path.enlarge_bbox(
            bbox,
            bboxMargin,
            bboxMargin,
            cropBB
        );

        // get svg as dataUrl including namespaces, fonts, more
        const svgDataUrl = elem.toWorkingAreaDataURL(fontDeclarations);
        const fillBitmap = await url2png(svgDataUrl, pxPerMM, bboxMM, true);
        const size = getDataUriSize(fillBitmap);
        const analysis = getCanvasAnalysis(renderCanvas);

        return {
            dataUrl: fillBitmap,
            size: size,
            bbox: bboxMM,
            analysis: analysis,
        };
    };

    /*
     * rasters an snap svg element into a png bitmap.
     * if MRBEAM_DEBUG_RENDERING === true, result will be embedded in the elements paper
     *
     * @param {Number} pxPerMM rastering resolution (default 10)
     * @param {Number} margin will be added around elements bbox. (default null (auto), 0 -> bbox will be rendered. 1 -> 0.5*bbox width will be added left and right)
     *
     * @returns {Object} keys: dataUrl (encoded png), bbox (real size of the rastered png incl. margin)
     */
    Element.prototype.raster = function (pxPerMM = 10, margin = null) {
        const elem = this;
        const bb = elem.getBBox();
        const promise = elem
            ._renderPNG2(pxPerMM, margin)
            .then(function (result) {
                if (MRBEAM_DEBUG_RENDERING) {
                    console.info(
                        "MRBEAM_DEBUG_RENDERING",
                        result.dataUrl,
                        result.bbox
                    );
                    const img = elem.paper.image(
                        result.dataUrl,
                        result.bbox.x,
                        result.bbox.y,
                        result.bbox.w,
                        result.bbox.h
                    );
                    img.attr("opacity", 0.6);
                    img.click(function () {
                        img.remove();
                    });
                }
                return result;
            });
        return promise;
    };

    Element.prototype.trace = async function (callback) {
        const pxPerMM = 20;
        const elem = this;
        const mat = elem.transform().localMatrix;
        const rasterResult = await elem.raster(pxPerMM);
        Potrace.loadImageFromUrl(rasterResult.dataUrl);
        Potrace.process(function () {
            const pathData = Potrace.getSVGPathArray(1 / pxPerMM);
            callback(pathData);
        });
    };

    // TODO use url2png, simplify, check if necessary
    Element.prototype.renderJobTimeEstimationPNG = function (
        wPT,
        hPT,
        wMM,
        hMM
    ) {
        var elem = this;
        console.debug(
            `renderJobTimeEstimationPNG: SVG ${wPT} * ${hPT} (pt) with viewBox ${wMM} * ${hMM} (mm)`
        );

        // get svg as dataUrl
        var svgDataUri = elem.toDataURL(); // TODO fix style="font-family:\"Allerta Stencil\"" quoting bug... needs to be 'Allerta Stencil'
        // TODO fix href and src references. not copied from defs...
        let bbox = elem.getBBox();
        const pxPerMM = 1;

        // init render canvas and attach to page
        const canvas = document.createElement("canvas");
        canvas.id = `renderCanvas_JobTimeEst`;
        canvas.class = "renderCanvas";
        canvas.width = bbox.w * pxPerMM;
        canvas.height = bbox.h * pxPerMM;

        if (MRBEAM_DEBUG_RENDERING) {
            canvas.style =
                "position: fixed; bottom: 0; left: 0; width: 95vw; border: 1px solid red;";
            canvas.addEventListener("click", function () {
                this.remove();
            });
        }
        document.getElementsByTagName("body")[0].appendChild(canvas);
        var renderCanvasContext = canvas.getContext("2d");
        renderCanvasContext.fillStyle = "white"; // avoids one backend rendering step (has to be disabled in the backend)
        renderCanvasContext.fillRect(0, 0, canvas.width, canvas.height);

        let prom = loadImagePromise(svgDataUri)
            .then(
                function (imgTag) {
                    let histogram = {};
                    let whitePxRatio = 0;
                    try {
                        const srcScale = wPT / wMM; // canvas.drawImage refers to <svg> coordinates - not viewBox coordinates.
                        const cx = bbox.x * srcScale;
                        const cy = bbox.y * srcScale;
                        const cw = bbox.w * srcScale;
                        const ch = bbox.h * srcScale;

                        renderCanvasContext.drawImage(
                            imgTag,
                            cx,
                            cy,
                            cw,
                            ch,
                            0,
                            0,
                            canvas.width,
                            canvas.height
                        );
                        const canvasAnalysis = getCanvasAnalysis(canvas);
                        histogram = canvasAnalysis.histogram;
                        whitePxRatio = canvasAnalysis.whitePixelRatio;
                    } catch (exception) {
                        console.error(
                            "renderCanvasContext.drawImage failed:",
                            exception
                        );
                    }

                    if (!MRBEAM_DEBUG_RENDERING) {
                        canvas.remove();
                    }
                    return {
                        bbox: bbox,
                        histogram: histogram,
                        whitePixelRatio: whitePxRatio,
                    };
                },
                // after onerror
                function (e) {
                    // var len = svgDataUri ? svgDataUri.length : -1;
                    var len = getDataUriSize(svgDataUri, "B");
                    var msg =
                        "Error during conversion: Loading SVG dataUri into image element failed. (dataUri.length: " +
                        len +
                        ")";
                    console.error(msg, e);
                    console.debug(
                        "renderJobTimeEstimationPNG ERR: svgDataUri that failed to load: ",
                        svgDataUri
                    );
                    if (!MRBEAM_DEBUG_RENDERING) {
                        canvas.remove();
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
