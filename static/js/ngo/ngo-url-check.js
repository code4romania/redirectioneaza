$(function () {

    function checkNgoUrl(){
        if(!ongUrl.val()) {
            return;
        }

        $.ajax({
            url: "{{ check_ngo_url }}" + ongUrl.val(),
            success: function(data) {
                ongUrl.parent().removeClass("has-error");
            },
            error: function(data) {
                // if we find it it's no good
                ongUrl.parent().addClass("has-error");
            }
        });
    };
    function sanitizeInput(value) {
        value = value.trim().toLowerCase();

        value = value.replace(/ț|Ț+/g, "t").replace(/ș|Ș+/g, "s").replace(/î|Î+/g, "i").replace(/ă|Ă+/g, "a").replace(/â|Â+/g, "a");

        // replace all spaces with -, more than one - goes to one, replace any non alpha
        value = value.replace(/\s+/g, "-").replace(/-+/g, "-").replace(/[^-\w]/g, '');

        return value;
    };

    var ongUrl = $("#ong-url");
    $("#ong-nume").on("input propertychange", function(ev){
        var value = sanitizeInput(ev.target.value);

        ongUrl.val(value);
    }).on("blur", checkNgoUrl);

    ongUrl.on("input propertychange", function(ev){
        var value = sanitizeInput(ev.target.value);

        ongUrl.val(value);

        checkNgoUrl();
    });

});