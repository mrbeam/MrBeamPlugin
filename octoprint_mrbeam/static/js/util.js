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
                //                console.log("### img loaded", image);
                resolve(image);
            };
            image.onerror = function (err) {
                //                console.log("###", err, image);
                reject(image, url, err);
            };
            image.src = url;
        });
    };

    CanvasUtil = {};
    CanvasUtil.getWhitePixelRatio = function (canvas) {
        // count ratio of white pixel
        const pixelData = canvas
            .getContext("2d")
            .getImageData(0, 0, canvas.width, canvas.height).data;
        let countWhite = 0;
        let countNoneWhite = 0;
        for (var p = 0; p < pixelData.length; p += 4) {
            pixelData[p] === 255 &&
            pixelData[p + 1] === 255 &&
            pixelData[p + 2] === 255 &&
            pixelData[p + 3] === 255
                ? countWhite++
                : countNoneWhite++;
        }
        const ratio = countWhite / (countNoneWhite + countWhite);
        return ratio;
    };

    CanvasUtil.getBoundaries = function (canvas) {
        // get bounds of visible (non transparent) pixel
        const pxArr = canvas
            .getContext("2d")
            .getImageData(0, 0, canvas.width, canvas.height).data;
        let right = 0;
        let left = canvas.width - 1;
        let bottom = 0;
        let top = canvas.height - 1;
        for (var p = 0; p < pxArr.length; p += 4) {
            const x = (p / 4) % canvas.width;
            const y = Math.floor(p / 4 / canvas.width);
            const isVisible = pxArr[p + 3] > 0; // alpha

            if (isVisible) {
                left = Math.min(x, left);
                right = Math.max(x, right);
                top = Math.min(y, top);
                bottom = Math.max(y, bottom);
            }
        }
        const result = {
            px: {
                l: left,
                r: right,
                t: top,
                b: bottom,
                w: right - left,
                h: bottom - top,
            },
            percent: {
                l: left / canvas.width,
                r: right / canvas.width,
                t: top / canvas.height,
                b: bottom / canvas.height,
                w: (right - left) / canvas.width,
                h: (bottom - top) / canvas.height,
            },
        };

        return result;
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
});
