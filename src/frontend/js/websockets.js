/**
 *
 * @param relativeUrl {string} relative url to backend endpoint
 * @returns {WebSocket} websocket connection object
 */
const createWebsocketConn = (relativeUrl) => {
    const loc = window.location;

    let newUri;
    if (loc.protocol === "https:") {
        newUri = "wss:";
    } else {
        newUri = "ws:";
    }

    newUri += "//" + loc.host;
    newUri += relativeUrl;
    return new WebSocket(newUri);
}

/**
 * Wrapper around websocket
 * Permits to restart connection without creating new objects in final code
 */
export class WebsocketEndpoint {
    /**
     *
     * @param url {string} relative ws url
     */
    constructor(url) {
        this.url = url;
        this.socket = null;
    }

    /**
     * Is websocket connection is open now
     * @returns {boolean}
     */
    isOpen() {
        return (this.socket !== null && this.socket.readyState === WebSocket.OPEN);
    }


    /**
     * Creates and returns socket. If socket is already open, just returns it
     * @returns {WebSocket}
     */
    connect() {
        if (this.socket !== null && this.socket.readyState === WebSocket.OPEN) {
            return this;
        }

        this.socket = createWebsocketConn(this.url);

        this.socket.onopen = e => {
            console.log("Opened socket connection");
        }

        this.socket.onclose = e => {
            console.log("Closed socket connection");
            this.socket = null;
        }

        this.socket.onerror = e => {
            console.error(e);
        }

        return this;
    }

    disconnect() {
        if (this.socket !== null && this.socket.readyState === WebSocket.OPEN) {
            this.socket.close();
        }

        this.socket = null;
    }

    get() {
        return this.socket ? this.socket : null;
    }
}
