$(function () {

    $('.description').shorten({
        moreText: 'Arata mai mult',
        lessText: 'Arata mai putin',
        showChars: 200
    });

    var errors = {
        server_error: "Se pare ca am intampinat o eroare pe server. Va rugam incercati din nou.",
        fields_error: "Se pare ca urmatoarele date sunt invalide: "
    }
    var ngoUrl = window.location.href;
    var form = $("#twopercent");

    $('[data-toggle="popover"]').popover({
        trigger: "focus",
        placement: ( $(window).width() > 790 ) ? "right" : "bottom"
    });

    var errorClass = "has-error";
    var invalidFields = {};
    function showError (context) {
        invalidFields[context.id] = true;

        var el = $(context);
        el.parent().addClass(errorClass);
        el.popover({
            content: "Valoarea acestui camp este invalida.",
            title: "",
            placement: ( $(window).width() > 790 ) ? "right" : "bottom",
            trigger: "focus"
        });
    }
    function hideError (context) {
        delete invalidFields[context.id];

        var el = $(context);
        el.parent().removeClass(errorClass);
        el.popover('destroy');
    }

    $("#nume, #prenume, #strada, #bloc, #scara, #etaj, #ap, #localitate").on("blur", function(){
        var val = this.value;
        if(!val) return;

        var regex = /^[\w\s.\-ăîâșțşţ]+$/gi;
        // if we have no match
        if(!val.match(regex)) {
            showError(this);
        } else {
            hideError(this);
        }
    });

    /******************************************************************************/
    /****                            Validare CNP                              ****/
    /******************************************************************************/
    /**
     * Validate CNP ( valid for 1800-2099 )
     *
     * @param string $p_cnp
     * @return boolean
     */
    // copyright https://github.com/cristian-datu/CNP
    function validCNP( p_cnp ) {
        var i=0 , year=0 , hashResult=0 , cnp=[] , hashTable=[2,7,9,1,4,6,3,5,8,2,7,9];
        if( p_cnp.length !== 13 ) { return false; }
        for( i=0 ; i<13 ; i++ ) {
            cnp[i] = parseInt( p_cnp.charAt(i) , 10 );
            if( isNaN( cnp[i] ) ) { return false; }
            if( i < 12 ) { hashResult = hashResult + ( cnp[i] * hashTable[i] ); }
        }
        hashResult = hashResult % 11;
        if( hashResult === 10 ) { hashResult = 1; }
        year = (cnp[1]*10)+cnp[2];
        switch( cnp[0] ) {
            case 1  : case 2 : { year += 1900; } break;
            case 3  : case 4 : { year += 1800; } break;
            case 5  : case 6 : { year += 2000; } break;
            case 7  : case 8 : case 9 : { year += 2000; if( year > ( parseInt( new Date().getYear() , 10 ) - 14 ) ) { year -= 100; } } break;
            default : { return false; }
        }
        if( year < 1800 || year > 2099 ) { return false; }
        return ( cnp[12] === hashResult );
    }

    $("#cnp").on("blur", function(){
        var val = this.value;

        // if the user provided a value make sure it's valid
        if( val && !validCNP(val) ) {
            showError(this);
        } else {
            hideError(this);
        }
    });

    $('#email').on('blur', function() {
        var email = $(this).val().trim();

        var regex = /[\w.-]+@[\w.-]+.\w+/
        if( email && !regex.test(email) ) {
            showError(this);
        } else {
            hideError(this);
        }
    });

    $('#telefon').on('blur', function() {
        var telefon = $(this).val().trim();

        if( telefon && (telefon.length != 10 || telefon.slice(0, 2) !== "07") ) {
            showError(this);
        } else {
            hideError(this);
        }
    });

    var invalidFormAlert = $("#invalid-form-alert");
    var submitFormButton = $("#submit-twopercent-form");

    form.on("submit", function(ev){
        ev.preventDefault();

        $(this).find("input").blur();

        var len = 0;
        for (var o in invalidFields) {
            len++;
        }

        if( len == 0 ) {
            // all ok
            invalidFormAlert.addClass("hidden");
        } else {
            invalidFormAlert.removeClass("hidden");
            return;
        }

        // add ajax field
        $('<input />').attr('type', 'hidden')
            .attr('name', "ajax").attr('value', "true")
            .appendTo(this);


        if( grecaptcha && typeof grecaptcha.execute == "function" ) {
            grecaptcha.execute();
        }

    });

    function forceDownload(href) {
        var anchor = document.createElement('a');
        anchor.href = href;
        anchor.download = 'Formular 2%.pdf';
        document.body.appendChild(anchor);
        anchor.click();
    }

    
    // ######## signature ########

    var canvas = document.getElementById("signature");
    var twpPercWrapper = document.getElementById("twopercent-form-wrapper");
    var signaturePad
    window.addEventListener('resize', resizeCanvas, false);
    function resizeCanvas() {
        canvas.width = twpPercWrapper.clientWidth - 30;
        canvas.height = 150;

        signaturePad = new SignaturePad(canvas, { drawOnly:true, lineTop:200, penWidth: 1, lineWidth: 1 });
    }
    resizeCanvas();
    $('#clear-signature').on('click', function(){
        signaturePad.clear();
    });

    // ----- signature -------

    window.onSubmit = function(token) {

        submitFormButton.removeClass("btn-primary").addClass("btn-success").attr("disabled", true);

        $('<input />').attr('type', 'hidden')
            .attr('name', "g-recaptcha-response").attr('value', token)
            .appendTo(form);


        $.ajax({
            url: ngoUrl,
            type: "POST",
            dataType: "json",
            data: form.serialize(),
            success: function(data) {

                // download the pdf file
                // forceDownload(data.form_url)

                if( data.url ) {
                    // we need a delay between the file download and the redirect
                    // setTimeout(function () {
                        // redirect to the success page
                        window.location = data.url;
                    // }, 1000)
                } else {
                    message = errors["server_error"];
                    submitFormButton.addClass("btn-primary").removeClass("btn-success").attr("disabled", false);
                    invalidFormAlert.removeClass("hidden").find("span").text(message);
                    grecaptcha.reset();
                }
            },
            error: function(data) {

                if( grecaptcha && typeof grecaptcha.reset == "function" ) {
                    grecaptcha.reset()
                }

                var response = data.responseJSON;
                var message = "";
                if(data.status == 500 || response.server) {
                    message = errors["server_error"];
                } else if( response.fields && response.fields.length) {
                    message = errors["fields_error"];

                    for( var field in response.fields ) {
                        message += response.fields + ", ";
                    }
                    message = message.slice(0, -2);
                } else {
                    message = errors["server_error"];
                }

                submitFormButton.addClass("btn-primary").removeClass("btn-success").attr("disabled", false);
                invalidFormAlert.removeClass("hidden").find("span").text(message);
            }
        });
    };

});