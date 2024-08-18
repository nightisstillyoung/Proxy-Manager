import {Alert} from "./alerts.js";

/**
 * Static class with convert methods
 */
export class Formatter {

    static proxyExpression = new RegExp(
        '((?<protocol>(socks(4|5|5h))|http(s)?):\\/\\/)?' +
        '((?<username>.+):(?<password>.+)@)?' +
        '(?<ip>\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}):' +
        '(?<port>\\d+)', 'i'
    );

    static ipExpr = /^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$/;

    /**
     * Validates ip
     * @param ip {string}
     * @returns {boolean}
     */
    static isValidIP(ip) {
        return this.ipExpr.test(ip);
    }

    /**
     * Converts string to object
     * @param proxyStr {string}
     * @returns {*|null}
     */
    static strToObj(proxyStr) {
        const match = proxyStr.match(this.proxyExpression);

        // all proxies are already validated, but shit happens
        if (!match) {
            console.log(proxyStr);
            Alert.error(`Something went wrong with proxy: ${proxyStr}`)
            return null;
        }

        // creates object with data from named regex groups
        const { groups } = match;

        // deletes undefined fields
        Object.keys(groups).forEach(key => {
            if (groups[key] === undefined) delete groups[key];
        });

        return groups;
    }


    /**
     * converts {ip, port, username, password, <protocols>} object to string
     * @param obj object with obligatory params ip, port, username, password and one of working protocols
     */
    static objToUrl(obj) {
        let proto;

        // chooses protocol
        if (obj.socks5)
            proto = "socks5";
        else if (obj.socks4)
            proto = "socks4";
        else if (obj.https)
            proto = "https";
        else if (obj.http)
            proto = "http";
        else {
            // if this proxy is not checked
            if (obj.socks5 !== null)
                proto = "socks5";
            else if (obj.socks4 !== null)
                proto = "socks4";
            else if (obj.https !== null)
                proto = "https";
            else if (obj.http !== null)
                proto = "http";
            else
                console.log(obj);

        }

        const credentials = obj.username !== "" ? `${obj.username}:${obj.password}@` : "";

        return `${proto}://${credentials}${obj.ip}:${obj.port}`;
    }

    /**
     * Sets textarea where Formatter should operate
     * @param outputTextarea {Textarea}
     */
    static setup(outputTextarea) {
        $("#to-cr-ip-port").on("click", function(e) {
            // user cannot convert proxies while checking is going on
            if (localStorage.getItem("progressbar") === "active") {
                Alert.warning("You cannot convert format during active check.");
                return;
            }

            // proxies (strings)
            const lines = outputTextarea.getLines();
            if (lines.length === 0) {
                Alert.error("No proxies to convert!");
                return;
            }


            if (!lines[0].includes("://")) {
                // that means user called 'convert from urls' at non-url format
                return;
            }

            // proxies (objects)
            let proxies = [];
            for (const line of lines) {
                proxies.push(Formatter.strToObj(line));
            }

            // filter wrong proxies
            // it is impossible for invalid proxy to exist in output textarea
            // but still, who knows?
            proxies = proxies.filter(item => item !== null);

            outputTextarea.clear();
            for (const proxy of proxies) {
                let p;

                // we use this string as keys in cache in case if user decide to convert them back'
                // to proxy urls.
                if (proxy.username !== undefined) {
                    p = `${proxy.username}:${proxy.password}@${proxy.ip}:${proxy.port}`
                    outputTextarea.addLine(p);
                } else {
                    p = `${proxy.ip}:${proxy.port}`;
                    outputTextarea.addLine(p);
                }

                Cache.saveToCache(p, proxy);

            }




        });

        $("#to-proxy-url").on("click", (e) => {
            // user cannot convert proxies while checking is going on
            if (localStorage.getItem("progressbar") === "active") {
                Alert.warning("You cannot convert format during active check.");
                return;
            }

            // proxies (strings)
            const lines = outputTextarea.getLines();

            if (lines.length === 0) {
                Alert.error("No proxies to convert!");
                return;
            }

            if (lines[0].includes("://")) {
                // that means user called convert on urls
                return;
            }

            outputTextarea.clear();

            // load proxies from cache
            // we load proxies from cache in case they were converted from urls first
            // url -> ip:port -> url (user called to convert them back)
            let proxies = [];
            for (const line of lines) {
                if (Cache.loadFromCache(line) === null)
                    continue;

                const p = Cache.loadFromCache(line);

                let url;
                if (p.username === undefined)
                    url = `${p.protocol}://${p.ip}:${p.port}`;
                else
                    url = `${p.protocol}://${p.username}:${p.password}@${p.ip}:${p.port}`;

                outputTextarea.addLine(url);
            }

            // we do not need it anymore
            Cache.clear();

        });

    }

}



class Cache {
    /**
     * local cache to store proxy data
     * purges when user closes tab
     */

    static saveToCache(key, data) {
        try {
            sessionStorage.setItem(key, JSON.stringify(data));
        } catch (e) {
            console.error("Error saving to cache", e);
        }
    }

    static loadFromCache(key) {
        try {
            const data = sessionStorage.getItem(key);
            return data ? JSON.parse(data) : null;
        } catch (e) {
            console.error("Error loading from cache", e);
            return null;
        }
    }

    static clear() {
        sessionStorage.clear();
    }

}


