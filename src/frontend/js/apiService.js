import {Alert} from "./alerts.js";


/**
 * Provides easy interface between website api and other classes
 */
export class ApiService {
    /**
     * returns Promise wrapped around ajax request
     * @param url relative url
     * @param data object
     * @param method HTTP Method
     * @param dataType json/query
     * @returns {Promise<object>}
     */
    static request(url, data = "", method = "POST", dataType = "json") {
        return new Promise((resolve, reject) => {
            let preparedRequest = {
                url: url,
                type: method,
                dataType: 'json',
                success: function(response) {
                    if (response.status < 0) {
                        console.log(response.details);

                        ApiService.handleError(response);

                        //reject(response);
                        return;
                    }
                    /*
                     {"status": 0, "data" <data>}
                     {"status": -1, "details": <traceback>}
                     */
                    resolve(response.data);
                },
                error: function(xhr, status, error) {
                    console.log(`Status: ${status} | ${error}`);

                    Alert.error("Something went wrong...");

                    //reject(error);
                }
            }

            if (data !== "") {
                preparedRequest.contentType = dataType === "json" ? "application/json" : "application/x-www-form-urlencoded";
                preparedRequest.data = dataType === "json" ? JSON.stringify(data) : $.param(data);
            }

            $.ajax(preparedRequest);
    });
    }

    static handleError(err) {
        /**
         * err - response from server or in-code error
         */
        if (err.details !== undefined) {
            Alert.error(err.details);
        } else {
            Alert.error("Something went wrong...");
            console.log(err);
        }
    }
}





