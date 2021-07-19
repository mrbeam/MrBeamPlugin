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

    formatDurationHHMMSS = function (duration) {
        if (isNaN(duration) || duration < 0) {
            return "--:--:--";
        }
        var sec_num = parseInt(duration, 10); // don't forget the second param
        var hours = Math.floor(sec_num / 3600);
        var minutes = Math.floor((sec_num - hours * 3600) / 60);
        var seconds = sec_num - hours * 3600 - minutes * 60;

        if (hours < 10) {
            hours = "0" + hours;
        }
        if (minutes < 10) {
            minutes = "0" + minutes;
        }
        if (seconds < 10) {
            seconds = "0" + seconds;
        }
        return hours + ":" + minutes + ":" + seconds;
    };
});
