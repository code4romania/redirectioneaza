

$(function () {
    // code used to show the popup with instructions when click on the url input field
    $(".ngo-copy-url").on("click", function(){
        this.select();
    }).on("input", function(ev){
        ev.preventDefault();
    });
    $('[data-toggle="popover"]').popover({trigger: "focus"});
});