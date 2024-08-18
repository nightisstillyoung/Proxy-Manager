import {ApiService} from "./apiService.js";
import {Alert} from "./alerts.js";
import {Formatter} from "./format.js";


export class Navbar {
    /**
     * Setups proxy menu
     * @param outputTextarea {Textarea}
     */
    static setupProxyMenu(outputTextarea) {
        this.$proxiesMenu = $("#proxy-menu");
        this.outputTextarea = outputTextarea;

        // handle user's click
        this.$proxiesMenu.on("click", function(e) {

            // no matter what request we do, we update output proxies
            // if request returns non-empty list
            const $opt = $(e.target);

            // get api url
            const url = $opt.attr("data-api");

            // handle file download (do nothing)
            if ($opt.attr("id").includes("download")) {
                return e;
            }

            ApiService.request(url, '', "GET")
                .then((data) => {
                    if (data.length > 0) {
                        // got proxies, clean textarea
                        this.outputTextarea.clear();

                        // rewrite output data
                        // data = [<proxy obj>,]
                        for (const p of data) {
                            // convert objects from backend and insert them into textarea
                            this.outputTextarea.addLine(Formatter.objToUrl(p));
                        }
                        Alert.success("Done.");
                    } else if (!url.includes("purge")) {  // except 'purge' options we always get proxies from endpoint
                        Alert.warning("There are no proxies in database");
                    } else {
                        Alert.success("Done")
                    }
                });
        }.bind(this));

    }

    /**
     * Setups menu that controls checker
     * @param progressbar {ProgressbarBlock}
     */
    static setupCheckerMenu(progressbar) {
        this.$checkerMenu = $("#checker-menu");

        // In this menu user always start a new check
        this.$checkerMenu.find("#rerun-all-menu, #continue-unchecked-menu").on("click", function(e) {
            ApiService.request($(this).attr("data-api"), '')
                .then((data) => {
                    if (data === null){
                        Alert.warning("There are no proxies in database");
                        return data;
                    }

                    if (data.progress.initial_len === 0) {
                        Alert.error("There are no proxies in database");
                        return data;
                    }
                    // and start progressbar
                    progressbar.start(data.progress.initial_len);
                    Alert.success(`Succeed.`);
                });
        });
    }

    /**
     * Search outputs all results into output textarea
     * @param outputTextarea {Textarea}
     */
    static setupSearch(outputTextarea) {

        $("#search-by-ip").on("click submit", function(e) {
            e.preventDefault();

            // user cannot run in while check is going
            if (localStorage.getItem("progressbar") === "active") {
                Alert.warning("You cannot search during active check.");
                return;
            }

            // get ip from search input
            const searchStr = $("#search-input").val();

            // some validations
            if (searchStr === "") {
                Alert.warning("Search field is empty");
                return;
            }
            if (!Formatter.isValidIP(searchStr)) {
                Alert.error("IP address is invalid");
                return;
            }

            // search it
            ApiService.request("/proxies/search/", {"ip": searchStr}, "GET", "query")
                .then((data) => {
                    if (data.length > 0) {
                        outputTextarea.clear();
                        // rewrite output data
                        // data = [<proxy obj>,]
                        for (const p of data) {
                            outputTextarea.addLine(Formatter.objToUrl(p));
                        }

                        Alert.success("Done.");
                         $("#search-input").val("");
                    }

                    else {
                        Alert.warning("No proxies found.")
                    }

                });

        });
    }
}
