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
			while (v1parts.length < v2parts.length) v1parts.push("0");
			while (v2parts.length < v1parts.length) v2parts.push("0");
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
			}
			else if (v1parts[i] > v2parts[i]) {
				return 1;
			}
			else {
				return -1;
			}
		}

		if (v1parts.length !== v2parts.length) {
			return -1;
		}

		return 0;
	}
	

	static HUMAN_READABLE_IDS_CONSTANTS = 'bcdfghjklmnpqrstvwxz';
	static HUMAN_READABLE_IDS_VOCALS    = 'aeiouy';

	static getHumanReadableId(length){
		length = length || 4;
		let out = [];
		for (let i = 0; i < length/2; i++) {
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
	};
};
