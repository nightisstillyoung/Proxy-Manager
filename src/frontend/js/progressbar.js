import {ApiService} from "./apiService.js";


/**
 * Class to control progressbar
 */
export class ProgressbarManager {
    constructor(selector) {
        this.$elem = $(selector);
        this.$progressbar = this.$elem.find('.progress-bar');
        this.$doneDiv = $('#progressbar-done');
        this.intervalId = null;

        if (localStorage.getItem("progressbar") === "active")
            this.continue();
    }

    /**
     * starts progressbar and fetchUpdate() interval
     * @param valueMax - max value when the progressbar will be 100% width
     */
    start(valueMax) {
        if (localStorage.getItem("progressbar") === "active")
            return;

        this.reset();
        this.setValueMax(valueMax);
        this.updateValue(0, valueMax);
        this.show();

        localStorage.setItem("progressbar", "active");
        // start interval
        this.intervalId = setInterval(this.fetchUpdate.bind(this), 4000);

    }

    /**
     * Restarts progressbar if page was reloaded
     */
    continue() {
        // start interval
        this.intervalId = setInterval(this.fetchUpdate.bind(this), 4000);
    }

    /**
     * Shows progressbar and hides 'Done' text
     * Do not use without full understanding
     * Instead of show() use start() or continue()
     */
    show() {
        this.$elem.removeClass("hidden");
        this.$doneDiv.hide();
    }

    /**
     * Hides progressbar, shows 'Done' text
     * Do not use without full understanding
     * Instead of hide() use stop()
     */
    hide() {
        this.$elem.addClass("hidden");
        this.$doneDiv.show();
        localStorage.setItem("progressbar", "hidden");
    }

    /**
     * fetches progressbar update from server
     */
    fetchUpdate() {
        ApiService.request("/proxies/progress", "", "GET")
            .then((response) => {
                this.updateValue(response.progress.value_now, response.progress.current_len);

                // if width === 0 we set it to 0.1% to do not break entire progressbar
                this.updateWidth(
                    response.progress.progressbar_width > 0 ?
                        response.progress.progressbar_width : 0.1
                );

                // update max value in cases if user sends additional proxies when previous ones aren't checked yet
                this.setValueMax(response.progress.initial_len);

                if (response.progress.progressbar_width >= 100) {
                    this.stop();
                }


                return response;
            });



    }

    /**
     * Stops progressbar. Use it instead of hide()
     */
    stop() {
        localStorage.setItem("progressbar", "hidden");
        clearInterval(this.intervalId);
        this.intervalId = null;

        setTimeout(() => {
            if (this.intervalId !== null)
                return;  // if user starts another check during this 1sec pause.

            this.hide();
            this.reset();
            console.log("Progressbar stopped.")
        }, 1000);


    }

    /**
     * Pauses progressbar, but does not hide it
     */
    pause() {
        if (this.intervalId !== null) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    }

    /**
     * Updates text and 'aria-valuenow' on progressbar.
     * In other words, move forward.
     * @param value {string | int} - replaces old value of progress. Greater value - progress positive
     * @param left {string | int} - only cosmetic text: 'value' checked/'left' left
     */
    updateValue(value, left= null) {
        this.$progressbar.attr("aria-valuenow", value);
        if (left === null)
            this.$progressbar.text(`${value} checked`);
        else
            this.$progressbar.text(`${value} checked/${left} left`);
    }

    /**
     * Changes width of progressbar
     * @param width {string | int} percentage of progressbar width
     */
    updateWidth(width) {
        this.$progressbar.width(`${width}%`);
    }

    /**
     * Sets max value of progressbar
     * @param value {string | int} 'aria-valuemax', usually it shows how many proxies was in checked when progressbar started
     */
    setValueMax(value) {
        this.$progressbar.attr("aria-valuemax", value);
    }

    /**
     * Resets progressbar, but does not stop it
     * Use stop() method if you want to stop progressbar
     * @param value
     */
    reset(value = 0) {
        this.$progressbar.attr("aria-valuemin", value);
        this.updateValue("0");
        this.updateWidth("0.1");
    }
}







