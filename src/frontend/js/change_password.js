import {ApiService} from "./apiService.js";
import {Alert} from "./alerts.js";



$(document).ready(() => {
    $("form").on("submit", (e) => {
        e.preventDefault();

        if ($("#new-password").val() !== $("#new-password-confirm").val()) {
            Alert.warning("Passwords do not match");
            return;
        }

        if (!$("#old-password").val()) {
            Alert.warning("You must enter your current password");
            return;
        }



        ApiService.request("/jwt/change-password", 
            {
                "password": $("#old-password").val(),
                "new_password": $("#new-password").val()
            },
            "PATCH"
        ).then((data) => {
            Alert.success("Successfuly changed your password, please log in again with a new one").on("closed.bs.alert", () => {
                setTimeout(() => {
                    window.location = "/login";
                }, 100);
            });
            
        });
    });




});
