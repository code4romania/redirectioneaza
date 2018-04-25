$(function () {
    /**
     * The url to get all the ngos registered
     * @type {String}
     */
    var api = '/api/ngos';
    var searcEl = $("#search-bar");
    var ngos = [];

    function setupEasyAutocomplete() {
        var options = {
            data: ngos,
            getValue: "name",
            template: {
                type: "iconLeft",
                fields: {
                    iconSrc: "logo"
                }
            },
            list: {
                onClickEvent: function () {
                    var selected = searcEl.getSelectedItemData();
                    window.location.href = selected.url;
                },
                match: {
                    enabled: true
                }
            }
        };

        searcEl.easyAutocomplete(options);
    }

    $.get(api).done(function (response) {
        ngos = response;
        setupEasyAutocomplete()
    })

    // var doit;
    // window.onresize = function(){
    //   clearTimeout(doit);
    //   doit = setTimeout(setupEasyAutocomplete, 100);
    // };

})