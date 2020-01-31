$(function () {
    /**
     * The url to get all the ngos registered
     * @type {String}
     */
    var api = '/api/ngos';
    var searcEl = $("#search-bar");
    var ngos = [];
    var latinCharMap = {
      'ă': 'a',
      'â': 'a',
      'î': 'i',
      'ș': 's', // comma
      'ț': 't',
      'ş': 's', // cedilla
      'ţ': 't'
    };

    function latinise(str) {
      return str.replace(/[^\u0000-\u007E]/g, function(c) {
        return latinCharMap[c] || c;
      });
    }

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
                onKeyEnterEvent: function () {
                    var selected = searcEl.getSelectedItemData();
                    window.location.href = selected.url;
                },
                match: {
                    enabled: true,
                    method: function (element, phrase) {
                      return latinise(element).search(latinise(phrase)) > -1;
                    }
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
