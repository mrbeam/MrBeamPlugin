const mutationTargetNode = document.body;
const mutationConfig = {
    childList: true,
    attributes: false,
    characterData: false,
    subtree: false,
    attributeOldValue: false,
    characterDataOldValue: false,
};
const mutationCallback = function (mutationsList, observer) {
    for (let mutation of mutationsList) {
        if (mutation.type === "childList") {
            // Todo: should be removed once OctoPrint is updated
            // Backdrop Temporary Solution - start
            let modalElement = $(".modal-scrollable");
            let backDrop = $(".modal-backdrop");
            if (modalElement.length !== 0) {
                modalElement.each(function () {
                    if (
                        !$(this)[0].hasChildNodes() &&
                        modalElement.length === 1
                    ) {
                        setTimeout(() => {
                            if (
                                !$(this)[0].hasChildNodes() &&
                                modalElement.length === 1 &&
                                document.visibilityState === "visible"
                            ) {
                                $("body").removeClass("modal-open");
                                backDrop.remove();
                                $(this).removeClass("modal-scrollable");
                                console.warn(
                                    "mutationCallback: removed incomplete modal after 500ms"
                                );
                            }
                        }, 500);
                    } else if (
                        !$(this)[0].hasChildNodes() &&
                        modalElement.length > 1 &&
                        $(this).next().hasClass("modal-backdrop")
                    ) {
                        $(this).next().remove();
                        $(this)[0].remove();
                    } else if (
                        $(this)[0].hasChildNodes() &&
                        modalElement.length === 1 &&
                        $(this)
                            .find(".modal.hide.fade")
                            .getInlineStyle("display") === "none"
                    ) {
                        setTimeout(() => {
                            if (
                                $(this)
                                    .find(".modal.hide.fade")
                                    .hasClass("modal") &&
                                $(this)
                                    .find(".modal.hide.fade")
                                    .getInlineStyle("display") === "none"
                            ) {
                                document.body.append(
                                    $(this).find(".modal.hide.fade")[0]
                                );
                            }
                        }, 500);
                    }
                });
            } else if (modalElement.length === 0 && backDrop.length !== 0) {
                backDrop.remove();
            }
            // Backdrop Temporary Solution - end

            guidedTourOverride();
        }
    }
};
const observer = new MutationObserver(mutationCallback);
observer.observe(mutationTargetNode, mutationConfig);

// MutationObserver for Hopscotch bubbles to change button classes - start
let mutationAdded = false;
const mutationConfigBubble = {
    childList: true,
    attributes: false,
    characterData: true,
    subtree: false,
    attributeOldValue: false,
    characterDataOldValue: false,
};
const bubbleObserver = new MutationObserver(mutationCallback);

function guidedTourOverride() {
    let hopscotchElement = $(".hopscotch-bubble");
    if (hopscotchElement.length !== 0) {
        const navButtons = hopscotchElement.find(".hopscotch-nav-button");

        navButtons.each(function () {
            const button = $(this);
            button.addClass("btn").removeClass("hopscotch-nav-button");
            if (button.hasClass("hopscotch-next")) {
                button.addClass("btn-primary");
            }
        });

        // only add this observer once
        if (!mutationAdded) {
            const mutationTargetNodeBubble =
                document.getElementsByClassName("hopscotch-bubble")[0];
            bubbleObserver.observe(
                mutationTargetNodeBubble,
                mutationConfigBubble
            );
            mutationAdded = true;
        }
    } else {
        mutationAdded = false;
        bubbleObserver.disconnect();
    }
}
// MutationObserver for Hopscotch bubbles to change button classes - end
