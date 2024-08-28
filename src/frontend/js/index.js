import {Textarea} from "./textarea.js";
import {ApiService} from "./apiService.js";
import {Alert, errors} from "./alerts.js";
import {WebsocketEndpoint} from "./websockets.js";
import {ProgressbarManager} from "./progressbar.js";
import {Navbar} from "./navbar.js";
import {Formatter} from "./format.js";
import {Cookie} from "./cookies.js";


/**
 * Class that represents all javascript in index page
 */
class App {
    constructor() {
        // 3 textarea tags
        this.inputTextarea = new Textarea("#input-area");
        this.outputTextarea = new Textarea("#output-area");
        this.errorTextarea = new Textarea("#error-area");

        // progress bar (active only during check)
        this.progressbar = new ProgressbarManager("#progressbar-active");

        // button under input textarea
        this.$addButton = $("#input-area-button");

        // buttons under output textarea
        this.$outputCopyButton = $("#output-copy-button");
        this.$outputStopButton = $("#output-stop-button");
        this.$outputClearButton = $("#output-clear-button");

        // button under error textarea
        this.$errorClearButton = $("#error-clear-button");

        // websocket controls (under output textarea)
        this.$websocketOn = $("#websocket-on");
        this.$websocketOff = $("#websocket-off");

        /**
         * websocket class
         * @type {null | WebsocketEndpoint}
         */
        this.socket = null;
    }

    /**
     * Loads input textarea and buttons under it
     */
    loadInput() {

        this.$addButton.on("click", () => {

            // parse lines
            const lines = this.inputTextarea.getLines();

            // user clicked Add button without any proxies in the input textarea
            if (lines.length === 0) {
                Alert.error(errors.noInputProxies);
                return;
            }

            // make it readonly while making request
            this.inputTextarea.lock();

            // send them all to our API
            ApiService.request("/proxies/add", lines)
                .then(data => {
                    // incorrect proxies are returned if exist
                    if (data.incorrect_proxies.length > 0) {
                        for (const p of data.incorrect_proxies) {
                            this.errorTextarea.addLine(p);
                        }
                    }
                    // pass it forward
                    return data;
                })
                .then(data => {
                    // finally, clear input textarea
                    this.inputTextarea.clear();
                    return data;
                })
                .then(data => {
                    // user started check when celery was empty
                    if (localStorage.getItem("progressbar") !== "active") {
                        // start progressbar
                        this.progressbar.start(lines.length - data.incorrect_proxies.length);
                    }

                    return data;
                })
                .finally(() => {
                    // make it mutable again
                    this.inputTextarea.release();
                });
        });

    }

    /**
     * Loads clear button under error textarea
     */
    loadError() {
        this.$errorClearButton.on("click", () => {
            this.errorTextarea.clear();
        });
    }

    /**
     * Loads all buttons in the bottom of output textarea
     * (except websocket controls)
     */
    loadOutput() {

        // button that clears celery queue and stops check
        this.$outputStopButton.on("click", () => {
            ApiService.request("/proxies/stop", {})
            .then(() => {
                Alert.success(`<strong>Stopped.</strong> Please wait until remaining tasks are finished.`);
            });
        });

        // copy all content from output textarea to clipboard
        this.$outputCopyButton.on("click", () => {
            this.outputTextarea.copyToClipboard().then(() => {
                const oldVal = this.$outputCopyButton.text();
                this.$outputCopyButton.text("Done!");

                setTimeout(() => {
                    this.$outputCopyButton.text(oldVal);
                }, 2000)
            })
        });

        // clear it
        this.$outputClearButton.on("click", () => {
            this.outputTextarea.clear();
        })
    }

    /**
     * Sets simple websocket's event handlers
     * And load websocket control buttons in the bottom of
     * output textarea
     */
    loadWebsocket() {
        // if user opens page in the first time
        // websocket is set to ON by default
        if (localStorage.getItem("websocket") === null)
            localStorage.setItem("websocket", "on");

        // if websocket settings is set to ON
        if (localStorage.getItem("websocket") === "on") {
            this.$websocketOn.addClass("active");
            this.$websocketOff.removeClass("active");
        } else {
            // change buttons colors if OFF
            this.$websocketOn.removeClass("active");
            this.$websocketOff.addClass("active");
        }

        // create object to manage our connection
        this.socket = new WebsocketEndpoint("/proxies/ws/good");

        // if setting is set to ON, connect user to endpoint
        if (localStorage.getItem("websocket") === "on") {
            this.socket.connect();

            // and await for messages
            this.socket.socket.onmessage = (e) => {
                console.log(e.data);
                this.outputTextarea.addLine(e.data);
            }
        }

        // also set listener on button that enables websocket
        this.$websocketOn.on("click", () => {
            // if websocket is already ON -> do nothing
            if (localStorage.getItem("websocket") === "on")
                return;

            console.log("Websocket on");
            localStorage.setItem("websocket", "on");

            // connect to endpoint
            this.socket.connect();

            // and listen for new messages
            this.socket.get().onmessage = (e) => {
                this.outputTextarea.addLine(e.data);
            }
        });

        // button that disconnects from endpoint
        this.$websocketOff.on("click", () => {
            if (localStorage.getItem("websocket") === "off")
                return;

            console.log("Websocket off");
            localStorage.setItem("websocket", "off");

            if (this.socket !== null && this.socket.isOpen()) {
                this.socket.disconnect();
            }

        });
    }

    /**
     * Loads all js for Index.html
     */
    start() {

        // all links, except download or nav ones, must do nothing
        $("a").on("click", (e) => {
            if ($(e.target).attr("id").includes("download") || $(e.target).attr("id").includes("page"))
                return e;

            e.preventDefault();
        });

        // load all events on input textarea and it's button
        this.loadInput();

        // load error textarea
        this.loadError();

        // load output textarea and it's buttons
        this.loadOutput();

        // connect to websocket endpoint
        this.loadWebsocket();

        // setup navbar
        Navbar.setupProxyMenu(this.outputTextarea);
        Navbar.setupCheckerMenu(this.progressbar);
        Navbar.setupSearch(this.outputTextarea);

        // setup format settings
        Formatter.setup(this.outputTextarea);

        // shows jwt token
        $("#link-get-jwt").on("click", (e) => {
            e.preventDefault();
            const jwt = Cookie.readCookie("auth");

            const $resp = $(`
                <div class="input-group input-group-sm mb-3">
                    <div class="input-group-prepend">
                        <span class="input-group-text" id="inputGroup-sizing-sm">JWT API token</span>
                    </div>
                    <input type="text" value="${jwt}" class="form-control" title="You can use it in your scripts" aria-describedby="inputGroup-sizing-sm">
                </div>
                                
            `)
            Alert.success($resp);
        });

    }

}



// run it
$(document).ready(() => {
    const app = new App();
    app.start();
})


