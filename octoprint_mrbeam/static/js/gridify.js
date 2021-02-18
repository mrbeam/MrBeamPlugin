//    Gridify - a snapsvg.io plugin to create a grid of an element.
//    Copyright (C) 2015  Teja Philipp <osd@tejaphilipp.de>
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
     * multiplies a group and arranges the copies in a grid with cols x rows
     *
     * @param {integer} cols : as name says, defaults 0.
     * @param {integer} rows : as name says, defaults 0.
     * @param {integer} distX : horizontal distance between grid items, defaults 0.
     * @param {integer} distY : vertical distance between grid items, defaults 0.
     * @returns {undefined}
     */
    Element.prototype.grid = function (cols, rows, distX, distY) {
        var elem = this;
        if (elem.type !== "g") {
            console.info("only supported on groups");
            return;
        }
        var original_group = elem._get_original_group();
        var clone_group = elem._get_clone_group();
        clone_group.clear();

        var grid_elements = original_group.create_grid(
            cols,
            rows,
            distX,
            distY
        );
        for (var i = 0; i < grid_elements.length; i++) {
            var item = grid_elements[i];
            clone_group.append(item);
        }
    };

    Element.prototype._get_clone_group = function () {
        var elem = this;
        var clone_group = elem.select(".gridify_clones");
        if (clone_group) {
            return clone_group;
        } else {
            clone_group = elem.group().addClass("gridify_clones");
            return clone_group;
        }
    };

    Element.prototype._get_original_group = function () {
        var elem = this;
        var orig = elem.select(".gridify_original");
        if (orig) {
            return orig;
        } else {
            var children = elem.children();
            var original_group = elem.group().addClass("gridify_original");
            for (var i = 0; i < children.length; i++) {
                var c = children[i];
                original_group.append(c);
            }
            return original_group;
        }
    };

    Element.prototype.create_grid = function (cols, rows, distX, distY) {
        var elem = this;
        cols = cols || 1;
        rows = rows || 1;
        distX = distX || 0;
        distY = distY || 0;

        var grid_elements = [];

        var bbox = elem.getBBox();
        var dx = bbox.width + distX;
        var dy = bbox.height + distY;
        for (var i = 0; i < cols; i++) {
            for (var j = 0; j < rows; j++) {
                if (i !== 0 || j !== 0) {
                    var str = "t" + dx * i + "," + dy * j;
                    var clone = elem
                        .clone()
                        .removeClass("gridify_original")
                        .addClass("gridify_clone")
                        .transform(str);
                    clone.clean_gc();
                    grid_elements.push(clone);
                }
            }
        }
        return grid_elements;
    };
});
