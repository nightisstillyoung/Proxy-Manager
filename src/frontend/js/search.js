import {ApiService} from "./apiService.js";
import {Alert} from "./alerts.js";
import {Textarea} from "./textarea.js";


/**
 * Class that represents all javascript in search page /advanced/search
 */
class App {

    constructor() {
        this.availableProtocols = ["socks4", "socks5", "http", "https"];

        // search results are placed in output textarea
        this.textarea = new Textarea("#search-output-area");

        // textarea that
        this.textareaRow = $("div#textarea-row");

        // shadow overlay that makes background darker when visible
        this.$overlay = $("#overlay");

        // button that copy content from textarea (from textareaRow -> <textarea>)
        this.$outputCopyButton = $("#output-copy-button");
    }

    /**
     * Loads all controls and javascript
     */
    start() {
        // load inputs with type radio
        this.loadFormatControls();

        // handles submit
        this.loadForm();

        // copies all content from 'div#textarea-row textarea'
        this.$outputCopyButton.on("click", () => {
            this.textarea.copyToClipboard().then(r => {
                const oldVal = this.$outputCopyButton.text();
                this.$outputCopyButton.text("Done!");

                setTimeout(() => {
                    this.$outputCopyButton.text(oldVal);
                }, 2000)
            })
        });

        // closes popped textarea
        $("#output-close-button").on("click", function(e) {
            this.$overlay.hide();
            this.textareaRow.addClass("hidden");
        }.bind(this));
    }

    /**
     * Disables/enables custom format input field
     */
    loadFormatControls() {
        $(`input[name="format"]`).on("change", function(e) {
            if ($(e.target).attr("id") === "format-custom-radio") {
                $("#custom-format-string").attr("disabled", false);
            } else {
                $("#custom-format-string").attr("disabled", true);
            }
        });
    }

    /**
     * Makes a request
     */
    fetchProxies() {
        // there is only one form
        let $form = $("form#search-form");

        // base request
        let json_request = {
            "protocols": [],
            "format_string": null,

        };

        // validate custom string field
        if ($form.find(`input#format-custom-radio:checked`).val() && $(`input[name="format-custom"]`).val() === "") {
            Alert.error("Custom format string was not selected.");
            return;
        }

        // add chosen protocols if user selected at least one
        for (const proto of this.availableProtocols) {
            if ($form.find(`input#${proto}:checked`).val()) {
                json_request.protocols.push(proto);
                json_request[proto] = true;
            }
        }

        // if user didn't choose at least one, we set full list
        if (json_request.protocols.length === 0) {
            json_request.protocols = this.availableProtocols;
        }

        // latency
        json_request.latency = parseFloat($form.find(`input[name="latency"]`).val());

        // statuses, chosen by user
        json_request["alive"] = !!$form.find(`input#alive:checked`).val();
        json_request["dead"] = !!$form.find(`input#dead:checked`).val();
        json_request["not_checked"] = !!$form.find(`input#not-checked:checked`).val();

        // limit
        // takes limit from <input type="range">
        json_request.limit = $form.find(`input[name="limit"]`).val() === $form.find(`input[name="limit"]`).attr("max") ?
            -1 : $form.find(`input[name="limit"]`).val();


        // format
        // usually URL, but if user choose custom we also add content from input with his own format string
        json_request.format_type = $form.find(`input[name="format"]:checked`).val();
        if (json_request.format_type === "custom")
            json_request.format_string = $(`input[name="format-custom"]`).val();

        // log it
        console.log(json_request);

        ApiService.request("/proxies/search/advanced", json_request)
            .then(response => {
                if (response.length === 0) {
                    Alert.warning("No proxies found matching your filter.")
                    return;
                }

                // first, clear textarea from previous output
                this.textarea.clear();
                // add proxies which we got from backend
                this.textarea.addLines(response);
                // show textarea in the middle of web page
                this.textareaRow.removeClass("hidden");
                // show shadow background
                this.$overlay.show();

                // log response too
                console.log(response);
            });

    }

    /**
     * loads button in bottom of the page
     * and also handles submit event on main form
     */
    loadForm() {
        $("form#search-form")
            .on("submit", function(e) {
                e.preventDefault();
                this.fetchProxies();
            }.bind(this));

        $("button#submit-form").on("click", function(e) {
            e.preventDefault();
            this.fetchProxies();
        }.bind(this))
    }
}


// run it
$(document).ready(() => {
    const app = new App();
    app.start();
})


