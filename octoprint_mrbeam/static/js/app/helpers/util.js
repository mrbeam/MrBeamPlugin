$(function () {
    /**
     * https://stackoverflow.com/a/7616484
     */

    // Even in slow 3g throttling mode, the font is loaded within 40ms
    const QUICK_TEXT_FONT_LOAD_TIMEOUT = 50; // ms

    String.prototype.hashCode = function () {
        let hash = 0,
            i,
            chr;
        if (this.length === 0) return hash;
        for (i = 0; i < this.length; i++) {
            chr = this.charCodeAt(i);
            hash = (hash << 5) - hash + chr;
            hash |= 0; // Convert to 32bit integer
        }
        return hash;
    };

    loadImagePromise = function (url) {
        return new Promise((resolve, reject) => {
            // do something asynchronous
            var image = new Image();
            image.crossOrigin = "Anonymous"; // allow external links together with server side header Access-Control-Allow-Origin "*"
            image.onload = function () {
                // console.log("### img loaded", image);
                resolve(image);
            };
            image.onerror = function (err) {
                // console.log("###", err, image);
                reject(image, url, err);
            };
            image.src = url;
        });
    };

    generatePNGFromURL = async function (
        url,
        pxPerMM = 1,
        bbox = null,
        whiteBG = false,
        includesQuickText = false
    ) {
        // Load an image and wait for it to be loaded
        const image = await loadImagePromise(url).catch((error) => {
            console.error("Error caught in loadImagePromise:", error);
        });

        // Get the image dimensions
        let x = 0;
        let y = 0;
        let w = image.naturalWidth; // or 'width' if you want a special/scaled size
        let h = image.naturalHeight; // or 'height' if you want a special/scaled size

        // Check if image has dimension
        _checkDimensionsAndThrowError(
            w,
            h,
            `generatePNGFromURL: Image has no dimension!`
        );

        // Check if bbox has dimension
        if (bbox !== null) {
            x = bbox.x;
            y = bbox.y;
            w = bbox.w;
            h = bbox.h;
        }

        // Check if bbox has dimension
        _checkDimensionsAndThrowError(
            w,
            h,
            `generatePNGFromURL: Bbox has no dimension!`
        );

        // Handle and draw image on canvas
        let canvasDrawingOutcome = await _handleAndDrawImageOnCanvas(
            whiteBG,
            image,
            x,
            y,
            w,
            h,
            pxPerMM,
            includesQuickText
        ).catch((error) => {
            console.error(
                "Error caught in _handleAndDrawImageOnCanvas:",
                error
            );
        });

        // Get PNG from canvas
        const png = canvasDrawingOutcome.canvas.toDataURL("image/png");

        // Get analysis from canvas
        const analysis = getCanvasAnalysis(canvasDrawingOutcome.canvas);

        // Remove canvas
        canvasDrawingOutcome.canvas.remove();

        return {
            dataUrl: png,
            bbox: bbox,
            analysis: analysis,
            isFontLoadingIntoCanvasIssueDetected:
                canvasDrawingOutcome.isFontLoadingIntoCanvasIssueDetected,
        };
    };

    let _checkDimensionsAndThrowError = function (w, h, errorMessage) {
        if (w === 0 || h === 0) {
            console.error(errorMessage);
            throw new Error(errorMessage);
        }
    };

    let _handleAndDrawImageOnCanvas = async function (
        whiteBG,
        image,
        x,
        y,
        w,
        h,
        pxPerMM,
        includesQuickText
    ) {
        // Create canvas
        let canvas = document.createElement("canvas");
        canvas.id = "RasterCanvas_generatePNGFromURL";
        canvas.width = w * pxPerMM;
        canvas.height = h * pxPerMM;
        const ctx = canvas.getContext("2d");

        // Draw image on canvas
        let updatedCanvas = _checkWhiteBgAndDrawImage(
            canvas,
            ctx,
            whiteBG,
            image,
            x,
            y,
            w,
            h
        );

        // Check if quickText is included and wait for it to be redrawn
        // The reason behind this is that quickText fonts might not be loaded yet
        // So we wait a bit and redraw the image on the canvas to make sure the font is loaded
        return new Promise((resolve) => {
            if (includesQuickText) {
                setTimeout(() => {
                    // Clear canvas
                    console.info(
                        `Clear canvas: x=${x}, y=${y}, canvas.width=${updatedCanvas.canvas.width}, canvas.height=${updatedCanvas.canvas.height}`
                    );
                    updatedCanvas.ctx.clearRect(
                        x,
                        y,
                        updatedCanvas.canvas.width,
                        updatedCanvas.canvas.height
                    );

                    // Redraw canvas after delay
                    let quickTextUpdatedCanvasAfterDelay =
                        _checkWhiteBgAndDrawImage(
                            updatedCanvas.canvas,
                            updatedCanvas.ctx,
                            whiteBG,
                            image,
                            x,
                            y,
                            w,
                            h
                        );

                    // Check if the font loading into canvas issue is present
                    const isFontLoadingIntoCanvasIssueDetected =
                        _isFontLoadingIntoCanvasIssueDetected(
                            updatedCanvas.canvas,
                            quickTextUpdatedCanvasAfterDelay.canvas
                        );

                    // resolve promise
                    resolve({
                        canvas: quickTextUpdatedCanvasAfterDelay.canvas,
                        isFontLoadingIntoCanvasIssueDetected:
                            isFontLoadingIntoCanvasIssueDetected,
                    });
                }, QUICK_TEXT_FONT_LOAD_TIMEOUT);
            } else {
                const isFontLoadingIntoCanvasIssueDetected = {
                    result: false,
                    payload: null,
                };
                // resolve promise
                resolve({
                    canvas: updatedCanvas.canvas,
                    isFontLoadingIntoCanvasIssueDetected:
                        isFontLoadingIntoCanvasIssueDetected,
                });
            }
        });
    };

    let _checkWhiteBgAndDrawImage = function (
        canvas,
        ctx,
        whiteBG,
        image,
        x,
        y,
        w,
        h
    ) {
        // Draw white background if needed
        if (whiteBG) {
            ctx.fillStyle = "white";
            ctx.fillRect(0, 0, canvas.width, canvas.height);
        }

        // Draw image on canvas
        console.info(`Draw image: x=${x}, y=${y}, w=${w}, h=${h}`);
        ctx.drawImage(image, x, y, w, h, 0, 0, canvas.width, canvas.height);

        // Return canvas
        return { canvas, ctx };
    };

    let _isFontLoadingIntoCanvasIssueDetected = function (
        firstCanvas,
        secondCanvas
    ) {
        // Get PNG data URLs from the canvases
        const dataURL1 = firstCanvas.toDataURL("image/png");
        const dataURL2 = secondCanvas.toDataURL("image/png");

        // Compare the data URLs
        if (dataURL1 !== dataURL2) {
            console.error(
                "Font loading into canvas issue detected! The data URLs are not the same!"
            );
            const payload = {
                drawCanvasResult: dataURL1,
                redrawCanvasResult: dataURL2,
            };
            return {
                result: true,
                payload: payload,
            };
        } else {
            return {
                result: false,
                payload: null,
            };
        }
    };

    getCanvasAnalysis = function (canvas) {
        let hist = new Array(256).fill(0);
        let brightnessChanges = 0;
        let totalBrightnessChange = 0;
        let whitePixelsAtTheOutside = 0;
        let innerWhitePixelRatio = 0;
        let whitePixelRatio = 0;
        try {
            // count ratio of white pixel
            const pixelData = canvas
                .getContext("2d")
                .getImageData(0, 0, canvas.width, canvas.height).data;
            let whitePixelsConsequentInLine = 0;
            let lastYIdx = 0;
            let firstNonWhitePixelOfLineFound = false;
            let lastBrightness = -1;
            for (var p = 0; p < pixelData.length; p += 4) {
                const xIdx = (p / 4) % canvas.width;
                const yIdx = (p / 4 - xIdx) / canvas.width;
                const r = pixelData[p];
                const g = pixelData[p + 1];
                const b = pixelData[p + 2];
                const a = pixelData[p + 3];
                let brightness = Math.round(0.21 * r + 0.72 * g + 0.07 * b); // TODO: bug: rgba(0,0,0,127) should not be black, should be 50% gray
                // blend brightness value on white background
                if (a < 255) {
                    brightness = 255 - Math.round((a / 255) * brightness);
                }
                if (a === 0) brightness = 255; // transparent pixels are treated as white (means ignored)
                hist[brightness]++;
                if (lastBrightness !== brightness) {
                    brightnessChanges++;
                    totalBrightnessChange += Math.abs(
                        lastBrightness - brightness
                    );
                }
                lastBrightness = brightness;

                if (brightness < 255 && !firstNonWhitePixelOfLineFound) {
                    whitePixelsAtTheOutside += whitePixelsConsequentInLine; // left white pixels
                    whitePixelsConsequentInLine = 0;
                    firstNonWhitePixelOfLineFound = true;
                }
                if (yIdx !== lastYIdx) {
                    // line switch
                    whitePixelsAtTheOutside += whitePixelsConsequentInLine; // right white pixels
                    whitePixelsConsequentInLine = 0;
                    firstNonWhitePixelOfLineFound = false;
                    lastYIdx = yIdx;
                }
                if (brightness === 255) {
                    // count all white pixels in a row
                    if (lastBrightness === 255) whitePixelsConsequentInLine++;
                } else {
                    whitePixelsConsequentInLine = 0;
                }
            }
            whitePixelsAtTheOutside += whitePixelsConsequentInLine;
            innerWhitePixelRatio =
                (hist[255] - whitePixelsAtTheOutside) /
                (pixelData.length / 4 - whitePixelsAtTheOutside);
            whitePixelRatio = hist[255] / (pixelData.length / 4);
        } catch (e) {
            console.error(e);
        }
        return {
            whitePixelRatio: whitePixelRatio,
            innerWhitePixelRatio: innerWhitePixelRatio,
            whitePixelsAtTheOutside: whitePixelsAtTheOutside,
            histogram: hist,
            brightnessChanges: brightnessChanges,
            totalBrightnessChange: totalBrightnessChange,
            w: canvas.width,
            h: canvas.height,
        };
    };

    formatDurationHHMMSS = function (durationInSeconds) {
        if (isNaN(durationInSeconds) || durationInSeconds < 0) {
            return "--:--:--";
        }

        const d = getHoursMinutesSeconds(durationInSeconds);
        return d.h + ":" + d.mm + ":" + d.ss;
    };

    getHoursMinutesSeconds = function (durationInSeconds) {
        if (isNaN(durationInSeconds))
            return { h: NaN, m: NaN, s: NaN, hh: "--", mm: "--", ss: "--" };
        const sec_num = parseInt(durationInSeconds, 10); // don't forget the second param
        const hours = Math.floor(sec_num / 3600);
        const minutes = Math.floor((sec_num - hours * 3600) / 60);
        const seconds = sec_num - hours * 3600 - minutes * 60;
        const hh = hours < 10 ? "0" + hours : hours;
        const mm = minutes < 10 ? "0" + minutes : minutes;
        const ss = seconds < 10 ? "0" + seconds : seconds;
        return { h: hours, m: minutes, s: seconds, hh: hh, mm: mm, ss: ss };
    };

    formatFuzzyHHMM = function (durMinMax) {
        if (durMinMax.val === 0) {
            return "0h 0m";
        } else if (durMinMax.val < 60) {
            return "~ 0h 1m";
        } else if (durMinMax.val < 120) {
            return "~ 0h 2m";
        } else {
            const diff = durMinMax.max - durMinMax.min;
            if (diff < 60) {
                const avg = getHoursMinutesSeconds(durMinMax.val);
                return `~ ${avg.h}h ${avg.m}m`;
            } else {
                const min = getHoursMinutesSeconds(durMinMax.min);
                const max = getHoursMinutesSeconds(durMinMax.max);
                return `${min.h}h ${min.m}m - ${max.h}h ${max.m}m `;
            }
        }
    };

    observableInt = function (owner, default_val) {
        if (window.OBSERVER_COUNTER === undefined) window.OBSERVER_COUNTER = 0;
        var shadow_observer = "observableInt_" + window.OBSERVER_COUNTER++;
        owner[shadow_observer] = ko.observable(parseInt(default_val));

        return ko.pureComputed({
            read: function () {
                return owner[shadow_observer]();
            },
            write: function (value) {
                owner[shadow_observer](parseInt(value));
            },
            owner: owner,
        });
    };

    euclideanDistance = function (a, b) {
        return (
            a
                .map((x, i) => Math.abs(x - b[i]) ** 2) // square the difference
                .reduce((sum, now) => sum + now) ** // sum
            (1 / 2)
        ); // sqrt
    };

    throttle = function (func, interval) {
        var lastCall = 0;
        return function () {
            var now = Date.now();
            if (lastCall + interval < now) {
                lastCall = now;
                return func.apply(this, arguments);
            }
        };
    };

    roundDownToNearest10 = function (num) {
        return Math.floor(num / 10) * 10;
    };
    // Get value of element style property
    jQuery.fn.inlineStyle = function (prop) {
        return this.prop("style")[$.camelCase(prop)];
    };

    // Start of Debug Rendering
    debugBase64 = function (base64URL, target = "", data = null) {
        if (Array.isArray(base64URL)) {
            var dbg_links = base64URL.map(
                (url, idx) =>
                    `<a target='_blank' href='${url}' onmouseover=' show_in_popup("${url}"); '>${idx}: Hover | Right click -> Open in new tab</a>`
            ); // debug message, no need to translate
            var dbg_link = dbg_links.join("<br/>");
        } else {
            var dbg_link = `<a target='_blank' href='${base64URL}' onmouseover=' show_in_popup("${base64URL}"); '>Hover | Right click -> Open in new tab</a>`; // debug message, no need to translate
        }
        if (data) {
            dbg_link += "<br/>" + JSON.stringify(data);
        }
        new PNotify({
            title: "render debug output " + target,
            text: dbg_link,
            type: "warn",
            hide: false,
        });
    };

    show_in_popup = function (dataurl) {
        $("#debug_rendering_div").remove();
        $("body").append(
            "<div id='debug_rendering_div' style='position:fixed; top:0; left:0; border:1px solid red; background:center no-repeat; background-size: contain; background-color:aqua; width:50vw; height:50vh; z-index:999999; background-image:url(\"" +
                dataurl +
                "\")' onclick=' this.remove(); '></div>"
        );
    };
    // End of Debug Rendering
});

// Start of Render debugging utilities
(function (console) {
    /**
     * Convenient storing large data objects (json, dataUri, base64 encoded images, ...) from the console.
     *
     * @param {object} data to save (means download)
     * @param {string} filename used for download
     * @returns {undefined}
     */
    console.save = function (data, filename) {
        if (!data) {
            console.error("Console.save: No data");
            return;
        }

        if (!filename) filename = "console.json";

        if (typeof data === "object") {
            data = JSON.stringify(data, undefined, 4);
        }

        var blob = new Blob([data], { type: "text/json" }),
            e = document.createEvent("MouseEvents"),
            a = document.createElement("a");

        a.download = filename;
        a.href = window.URL.createObjectURL(blob);
        a.dataset.downloadurl = ["text/json", a.download, a.href].join(":");
        e.initMouseEvent(
            "click",
            true,
            false,
            window,
            0,
            0,
            0,
            0,
            0,
            false,
            false,
            false,
            false,
            0,
            null
        );
        a.dispatchEvent(e);
    };
})(console);
// End of Render debugging utilities
