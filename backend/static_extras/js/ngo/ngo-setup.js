$(function () {
    var uploadLogo = $("#upload-logo");
    var displayLogo = $("#display-logo");

    var aws_api_url = '/api/ngo/upload-url/';
    var photoLogoClass = "fa-picture-o";
    var loadingLogoClass = "fa-spinner fa-pulse";

    var errors = {
        server: "Se pare ca a aparut o problema. Va rugam reincarcati pagina si incercati din nou!"
    }

    var requestAttempts = 0;
    uploadLogo.find("#ong-logo").on("change", function(ev){
        var file = ev.target.files[0];
        function errorCallback(){
            // TODO: remove this in the future
            alert(errors.server);
            return;
            
            requestAttempts++;
            if(requestAttempts<4) {
                uploadLogo.find("#ong-logo").change();
            } else {
                alert(errors.server);
            }
        }

        if( file ) {
            uploadLogo.find("."  + photoLogoClass).removeClass(photoLogoClass).addClass(loadingLogoClass);

            // request upload key
            // $.ajax({
            //     url: aws_api_url + "?file_name="+file.name + "&file_type="+file.type,
            //     dataType: "json",
            //     success: function(data) {
                    // console.log(data);
                    var formData = new FormData();
                    formData.append("files", file);

                    // upload
                    $.ajax({
                        url: aws_api_url,
                        method: "post",
                        data: formData,
                        processData: false,
                        contentType: false,
                        success: function(data) {
                            if( data.file_urls && data.file_urls.length == 1 ) {
                                
                                var url = data.file_urls[0];

                                uploadLogo.addClass("hidden").find("input").val("");
                                displayLogo.find("img").attr("src", url);
                                displayLogo.find("#ong-logo-url").val(url);
                                displayLogo.removeClass("hidden");
                            } else {
                                errorCallback();
                            }
                        },
                        error: errorCallback
                    });

            //     },
            //     error: errorCallback
            // });
        }
    });

    $("#delete-ngo-logo").on("click", function(){
        uploadLogo.find(".fa").removeClass(loadingLogoClass).addClass(photoLogoClass);
        uploadLogo.removeClass("hidden");
        // hide the disaply logo and reset the logo url
        displayLogo.addClass("hidden").find("#ong-logo-url").val("");

    });

    // var ongCif = $("#ong-cif");
    // ongCif.on("blur", function(){
    //     if(!ongCif.val()) return;
    //     $.ajax({
    //         url: "http://openapi.ro/api/validate/cif/" + ongCif.val() + ".json",
    //         dataType: "jsonp",
    //         success: function(data) {
    //             if(data.valid) {
    //                 ongCif.parent().removeClass("has-error");
    //             } else {
    //                 ongCif.parent().addClass("has-error");
    //             }
    //         }
    //     });
    // });

    // var ongCont = $("#ong-cont");
    // ongCont.on("blur", function(){
    //     if(!ongCont.val()) return;
    //     $.ajax({
    //         url: "http://openapi.ro/api/validate/iban/" + ongCont.val() + ".json",
    //         dataType: "jsonp",
    //         success: function(data) {
    //             if(data.valid) {
    //                 ongCont.parent().removeClass("has-error");
    //             } else {
    //                 ongCont.parent().addClass("has-error");
    //             }
    //         }
    //     });
    // });
});
