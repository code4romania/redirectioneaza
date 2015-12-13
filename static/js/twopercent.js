$(function () {

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

        var regex = /^[\w\s.-]+$/gi;
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
    
    var invalidFormAlert = $("#invalid-form-alert");
    var submitFormButton = $("#submit-twopercent-form");
    var secondStep = $("#second-step-container");
    var secondStepSubmitButton = $("#second-step-submit-button");

    $("#twopercent").on("submit", function(ev){
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

        submitFormButton.removeClass("btn-primary").addClass("btn-success").attr("disabled", true);
        activateSecondStepForm();
        secondStep.removeClass("hidden");
        
        // scroll to bottom
        $("html, body").animate({ scrollTop: $(document).height() - 550 }, 3000);

        $.ajax({
            url: "{{ ngo.key.id() }}/doilasuta",
            type: "POST",
            dataType: "json",
            data: $(this).serialize(),
            success: function(data) {
                // enable the button
                secondStepSubmitButton.attr("disabled", false);
            },
            error: function(data) {
                if( grecaptcha && typeof grecaptcha.reset == "function" ) {
                    grecaptcha.reset()
                }

                var response = data.responseJSON;
                var message = "";
                if(data.status == 500 || response.server) {
                    message = "{{ server_error }}";
                } else if( response.fields && response.fields.length) {
                    message = "{{ fields_error }}";

                    for( var field in response.fields ) {
                        message += response.fields + ", ";
                    }
                    message = message.slice(0, -2);
                } else {
                    message = "{{ server_error }}";
                }

                submitFormButton.addClass("btn-primary").removeClass("btn-success").attr("disabled", false);
                invalidFormAlert.removeClass("hidden").find("span").text(message);
                secondStep.addClass("hidden");
            }
        });
    });


    function activateSecondStepForm() {
        
        secondStepSubmitButton.attr("disabled", true);
        $("#second-step-form").on("submit", function(ev){
            ev.preventDefault();

            var email = $(this).find("#email").val().trim();
            var telefon = $(this).find("#telefon").val().trim();

            // if both email and tel are empty, return
            if(!email && !telefon) {
                invalidFormAlert.removeClass("hidden").find("span").text("Te rugam sa completezi cu o adresa de email sau un numar de telefon.");
                return;
            }

            // validation
            var regex = /[\w.-]+@[\w.-]+.\w+/
            if( email && !regex.test(email) ) {
                invalidFormAlert.removeClass("hidden").find("span").text("Te rugam sa introduci o adresa de email valida.");
                return;
            }

            if( telefon && (telefon.length != 10 || telefon.slice(0, 2) !== "07") ) {
                invalidFormAlert.removeClass("hidden").find("span").text("Te rugam sa introduci un numar de telefon mobil valid.");
                return;
            }

            invalidFormAlert.addClass("hidden");
            secondStepSubmitButton.attr("disabled", true);

            // add ajax field
            $('<input />').attr('type', 'hidden')
                .attr('name', "ajax").attr('value', "true")
                .appendTo(this);

            $.ajax({
                url: "{{ ngo.key.id() }}/doilasuta/pas-2",
                type: "POST",
                dataType: "json",
                data: $(this).serialize(),
                success: function(data) {
                    // redirect to
                    window.location = data.url;
                },
                error: function(data) {
                    if(data.response == 500) {
                        var message = "{{ server_error }}";

                    } else {

                        var message = data.responseJSON.message;
                    }

                    secondStepSubmitButton.attr("disabled", false);
                    invalidFormAlert.removeClass("hidden").find("span").text(message);
                }
            });
        });
    }
});