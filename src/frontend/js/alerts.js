export const errors = {
    noInputProxies: "You didn't put any proxies into input."
}


/**
 * Static class that provides methods to show alerts
 */
export class Alert {
    static $overlay = $("#overlay");

    static error(message) {
        /**
         * Shows error message
         * @param message {string|jQuery|HTMLElement}
         * @type {string|jQuery|HTMLElement}
         */
        const $error = $(`<div class="message alert alert-danger alert-dismissible fade show" id="error" role="alert">
            <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                <span aria-hidden="true">&times;</span>
            </button>
        </div>`);

        this.alert(message, $error);

        return $error;
    }

    static success(message) {
        /**
         * Shows success message
         * @param message {string|jQuery|HTMLElement}
         * @type {string|jQuery|HTMLElement}
         */
        const $success = $(`<div class="message alert alert-success alert-dismissible fade show" id="error" role="alert">
            <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                <span aria-hidden="true">&times;</span>
            </button>
        </div>`);

        this.alert(message, $success);

        return $success;
    }

    static warning(message) {
        /**
         * Shows warn
         * @param message {string|jQuery|HTMLElement}
         * @type {string|jQuery|HTMLElement}
         */
        const $warning = $(`<div class="message alert alert-warning alert-dismissible fade show" id="error" role="alert">
            <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                <span aria-hidden="true">&times;</span>
            </button>
        </div>`);

        this.alert(message, $warning);

        return $warning;
    }



    static alert(message, $elem) {
        /**
         * @param message {string|jQuery|HTMLElement}
         * @param $elem {jQuery|HTMLElement}
         */
        // do not alert if there is another alert active
        if ($(".alert").length !== 0)
            return;

        // wrap around string <p>-tag
        if (typeof message === "string") {
            $elem.prepend(`<p>${message}</p>`);
        } else {
            $elem.prepend(message);  // if message is an element
        }

        // append to DOM
        $("main").append($elem);
        // show 'shadow' overlay
        this.$overlay.show();
        // alert message
        $elem.alert();

        // event on button to close it
        $elem.on("closed.bs.alert", (e) => {
            this.$overlay.hide();
            $(e.target).remove();
        });
    }



}





