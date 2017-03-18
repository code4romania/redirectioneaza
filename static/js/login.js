
$(function () {

    var form = $('.form');

    form.submit(function(ev) {
        ev.preventDefault();
        grecaptcha.execute();
    });
    
    window.onSubmit = function(token) {

        $('<input />').attr('type', 'hidden')
            .attr('name', "g-recaptcha-response").attr('value', token)
            .appendTo( form );
        
        form.off('submit').submit();
    };
});