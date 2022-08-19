var assert = chai.assert;

describe("QuickShapeHelper test", function () {
    it("Radio 0 should return empty string", function () {
        var arr = [];

        let circle = QuickShapeHelper.getCircle(0);
        assert.isEmpty(circle);
    });

    it("Radio -1 should return empty string", function () {
        var arr = [];

        let circle = QuickShapeHelper.getCircle(-1);
        console.log(circle);
        assert.isEmpty(circle);
    });
});
