$(function () {
    var uploadLogo = $("#upload-logo");
    var displayLogo = $("#display-logo");

    var aws_api_url = "{{ ngo_upload_url }}";
    var photoLogoClass = "fa-picture-o";
    var loadingLogoClass = "fa-spinner fa-pulse";

    var errors = 0;
    uploadLogo.find("#ong-logo").on("change", function(ev){
        var file = ev.target.files[0];
        function errorCallback(){
            // TODO: remove this in the future
            alert("Se pare ca a aparut o problema. Va rugam reincarcati pagina si incercati din nou!")
            return;
            
            errors++;
            if(errors<4) {
                uploadLogo.find("#ong-logo").change();
            } else {
                alert("Se pare ca a aparut o problema. Va rugam reincarcati pagina si incercati din nou!")
            }
        }

        if( file ) {
            uploadLogo.find("."  + photoLogoClass).removeClass(photoLogoClass).addClass(loadingLogoClass);

            // request upload key
            $.ajax({
                url: aws_api_url + "?file_name="+file.name + "&file_type="+file.type,
                dataType: "json",
                success: function(data) {
                    console.log(data);
                    // return

                    // upload to s3
                    $.ajax({
                        url: data.signed_request,
                        method: "PUT",
                        data: file,
                        processData: false,
                        contentType: false,
                        headers: {
                            'x-amz-acl': 'public-read',
                            'Content-Type': file.type
                        },
                        success: function() {
                            uploadLogo.addClass("hidden").find("input").val("");
                            displayLogo.find("img").attr("src", data.url);
                            displayLogo.find("#ong-logo-url").val(data.url);
                            displayLogo.removeClass("hidden");
                        },
                        error: errorCallback
                    });

                },
                error: errorCallback
            });
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
