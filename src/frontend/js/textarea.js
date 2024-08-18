/**
 * Makes wrapper object on textarea with methods to manage it
 * selector -> <textarea>'s selector
 */
export class Textarea {
    /**
     *
     * @param selector {string} <textarea> selector
     */
    constructor(selector) {
        this.$elem = $(selector);
    }

    /**
     * Returns array of lines from textarea
     * @returns {string[]}
     */
    getLines() {
        let content = this.$elem.val().split("\n");

        return content.filter(item => item !== "")
    }

    /**
     * Inserts multiple lines with \n separator in textarea
     * @param lines lines to insert
     */
    addLines(lines) {
        for (const line of lines) {
            this.addLine(line);
        }
    }

    /**
     *  Inserts one line with \n at the end
     *
     * @param line string to insert
     */
    addLine(line) {
        this.$elem.val(this.$elem.val() + `${line}\n`);
    }

    /**
     * Clears textarea
     */
    clear() {
        this.$elem.val("");
    }

    /**
     * Adds readonly attribute
     */
    lock() {
        this.$elem.attr('readonly', true);
    }

    /**
     * Removes readonly attribute
     */
    release () {
        this.$elem.removeAttr('readonly');
    }

    /**
     * Copy text to clipboard and return it's promise
     * @returns {Promise<void>} returns promise of writeText()
     */
    copyToClipboard() {
        return navigator.clipboard.writeText(this.$elem.val());
    }

    /**
     * Triggers event on textarea
     * @param event {Event | string}
     */
    dispatch(event) {
        this.$elem.trigger(event);
    }

}

