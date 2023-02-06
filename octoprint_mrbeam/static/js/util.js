$(function () {
    /**
     * https://stackoverflow.com/a/7616484
     */
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

    url2png = async function (url, pxPerMM = 1, bbox = null, whiteBG = false) {
        let prom = loadImagePromise(url).then(function (image) {
            let x = 0;
            let y = 0;
            let w = image.naturalWidth; // or 'width' if you want a special/scaled size
            let h = image.naturalHeight; // or 'height' if you want a special/scaled size
            if (w === 0 || h === 0) {
                const msg = `url2png: Image has no dimension!`;
                console.error(msg, image);
                throw new Error(msg);
            }
            if (bbox !== null) {
                x = bbox.x;
                y = bbox.y;
                w = bbox.w;
                h = bbox.h;
            }
            if (w === 0 || h === 0) {
                const msg = `url2png: Source bbox has no dimension!`;
                console.error(msg, image);
                throw new Error(msg);
            }
            let canvas = document.createElement("canvas");
            canvas.id = "RasterCanvas_url2png";
            canvas.width = w * pxPerMM;
            canvas.height = h * pxPerMM;
            const ctx = canvas.getContext("2d");
            if (whiteBG) {
                ctx.fillStyle = "white";
                ctx.fillRect(0, 0, canvas.width, canvas.height);
            }

            console.info(`c.drawImage ${x}, ${y}, ${w}, ${h}`);

            ctx.drawImage(image, x, y, w, h, 0, 0, canvas.width, canvas.height);
            const png = canvas.toDataURL("image/png");
            const analysis = getCanvasAnalysis(canvas);
            canvas.remove();
            return { dataUrl: png, bbox: bbox, analysis: analysis };
        });
        //            .catch(function (error) {
        //                console.error(`url2png: error loading image: ${error}`);
        //            });
        return prom;
    };

    getCanvasAnalysis = function (canvas) {
        // count ratio of white pixel
        const pixelData = canvas
            .getContext("2d")
            .getImageData(0, 0, canvas.width, canvas.height).data;
        let hist = new Array(256).fill(0);
        let brightnessChanges = 0;
        let totalBrightnessChange = 0;
        let whitePixelsAtTheOutside = 0;
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
                totalBrightnessChange += Math.abs(lastBrightness - brightness);
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
        const innerWhitePixelRatio =
            (hist[255] - whitePixelsAtTheOutside) /
            (pixelData.length / 4 - whitePixelsAtTheOutside);
        const whitePixelRatio = hist[255] / (pixelData.length / 4);
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
    }
});
