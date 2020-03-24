class WorkingAreaHelper {

	static versionCompare(v1, v2, options) {
		var lexicographical = options && options.lexicographical,
				zeroExtend = options && options.zeroExtend,
				v1parts = v1.split('.'),
				v2parts = v2.split('.');

		function isValidPart(x) {
			return (lexicographical ? /^\d+[A-Za-z]*$/ : /^\d+$/).test(x);
		}

		if (!v1parts.every(isValidPart) || !v2parts.every(isValidPart)) {
			return NaN;
		}

		if (zeroExtend) {
			while (v1parts.length < v2parts.length)
				v1parts.push("0");
			while (v2parts.length < v1parts.length)
				v2parts.push("0");
		}

		if (!lexicographical) {
			v1parts = v1parts.map(Number);
			v2parts = v2parts.map(Number);
		}

		for (var i = 0; i < v1parts.length; ++i) {
			if (v2parts.length === i) {
				return 1;
			}

			if (v1parts[i] === v2parts[i]) {
				continue;
			} else if (v1parts[i] > v2parts[i]) {
				return 1;
			} else {
				return -1;
			}
		}

		if (v1parts.length !== v2parts.length) {
			return -1;
		}

		return 0;
	}

	static getHumanReadableId(length) {
		length = length || 4;
		let out = [];
		for (let i = 0; i < length / 2; i++) {
			const cIdx = Math.floor(Math.random() * this.HUMAN_READABLE_IDS_CONSTANTS.length);
			const vIdx = Math.floor(Math.random() * this.HUMAN_READABLE_IDS_VOCALS.length);
			out.push(this.HUMAN_READABLE_IDS_CONSTANTS.charAt(cIdx));
			out.push(this.HUMAN_READABLE_IDS_VOCALS.charAt(vIdx));
		}
		return  out.join('');
	}

	/**
	 * Workaround of a firefox bug which breaks quotes / brackets.
	 * Solution is pragmatic - just replacing bogus characters after things got wrong.
	 *
	 * @param {type} svgStr
	 * @returns {string} svgStr
	 */
	static fix_svg_string(svgStr) {
		// TODO: look for better solution to solve this Firefox bug problem
		svgStr = svgStr.replace("(\\\"", "(");
		svgStr = svgStr.replace("\\\")", ")");
		return svgStr;
	}

	static getHexColorStr(inputColor) {
		const c = new Color(inputColor);
		return c.getHex();
	}

	/**
	 * Returns with what program and version the given svg file was created. E.g. 'coreldraw'
	 *
	 * @param fragment (result of Snaps .select() .selectAll() .parse(), ...
	 * @returns {object} keys: generator, version
	 */
	static getGeneratorInfo(fragment) {
		var gen = null;
		var version = null;
		var root_attrs;
		if (fragment.select('svg') === null) {
			root_attrs = fragment.node.attributes;
		} else {
			root_attrs = fragment.select('svg').node.attributes;
		}

		// detect BeamOS generated Files by attribute
		// <svg
		//    ...
		//    xmlns:mb="http://www.mr-beam.org"
		//    ...
		//    mb:beamOS_version="0.3.4"
		var beamOS_version = root_attrs['mb:beamOS_version'];
		if (beamOS_version !== undefined) {
			gen = 'beamOS';
			version = version.value;
//				console.log("Generator:", gen, version);
			return {generator: gen, version: version};
		}

		// detect Inkscape by attribute
		// <svg
		//    ...
		//    xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
		//    xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
		//    ...
		//    inkscape:version="0.92.4 (5da689c313, 2019-01-14)"
		//    sodipodi:docname="Mr. Beam Jack of Spades Project Cards Inkscape.svg">
		var inkscape_version = root_attrs['inkscape:version'];
		if (inkscape_version !== undefined) {
			gen = 'inkscape';
			version = inkscape_version.value;
//				console.log("Generator:", gen, version);
			return {generator: gen, version: version};
		}

		// <svg viewBox="0 0 500 500" xmlns="http://www.w3.org/2000/svg" xmlns:bx="https://boxy-svg.com">
		// if (root_attrs['xmlns:bx'] && root_attrs['xmlns:bx'].value.search("boxy-svg.com")>0) {
		//     return { generator: "boxy-svg", version: "unknown" };
		// }

		// detect Illustrator by comment (works with 'save as svg')
		// <!-- Generator: Adobe Illustrator 16.0.0, SVG Export Plug-In . SVG Version: 6.00 Build 0)  -->
		var children = fragment.node.childNodes;
		for (var i = 0; i < children.length; i++) {
			var node = children[i];
			if (node.nodeType === 8) { // check for comment
				if (node.textContent.indexOf('Illustrator') > -1) {
					gen = 'illustrator';
					var matches = node.textContent.match(/\d+\.\d+(\.\d+)*/g);
					version = matches.join('_');
//						console.log("Generator:", gen, version);
					return {generator: gen, version: version};
				}
			}
		}

		// detect Illustrator by data-name (for 'export as svg')
		if (root_attrs && root_attrs['data-name']) {
			gen = 'illustrator';
			version = '?';
//				console.log("Generator:", gen, version);
			return {generator: gen, version: version};
		}

		// detect Corel Draw by comment
		// <!-- Creator: CorelDRAW X5 -->
		var children = fragment.node.childNodes;
		for (var i = 0; i < children.length; i++) {
			var node = children[i];
			if (node.nodeType === 8) { // check for comment
				if (node.textContent.indexOf('CorelDRAW') > -1) {
					gen = 'coreldraw';
					var version = node.textContent.match(/(Creator: CorelDRAW) (\S+)/)[2];
//						console.log("Generator:", gen, version);
					return {generator: gen, version: version};
				}
			}
		}

		// detect Method Draw by comment
		// <!-- Created with Method Draw - http://github.com/duopixel/Method-Draw/ -->
		for (var i = 0; i < children.length; i++) {
			var node = children[i];
			if (node.nodeType === 8) { // check for comment
				if (node.textContent.indexOf('Method Draw') > -1) {
					gen = 'method draw';
//						console.log("Generator:", gen, version);
					return {generator: gen, version: version};
				}
			}
		}


		// detect dxf.js generated svg
		// <!-- Created with dxf.js -->
		for (var i = 0; i < children.length; i++) {
			var node = children[i];
			if (node.nodeType === 8) { // check for comment
				if (node.textContent.indexOf('Created with dxf.js') > -1) {
					gen = 'dxf.js';
					console.log("Generator:", gen, version);
					return {generator: gen, version: version};
				}
			}
		}
//			console.log("Generator:", gen, version);
		return {generator: 'unknown', version: 'unknown'};
	}

	static isBinaryData(str) {
		return /[\x00-\x08\x0E-\x1F]/.test(str);
	}

	static isEmptyFile(fragment) {
	    // https://github.com/mrbeam/MrBeamPlugin/issues/787
	    return fragment.node.querySelectorAll('svg > *').length <= 0
	}
}

WorkingAreaHelper.HUMAN_READABLE_IDS_CONSTANTS = 'bcdfghjklmnpqrstvwxz';
WorkingAreaHelper.HUMAN_READABLE_IDS_VOCALS = 'aeiouy';
