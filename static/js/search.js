$(function () {
    /**
     * The url to get all the ngos registered
     * @type {String}
     */
    var api = '/api/ngos';
    var searcEl = $("#search-bar");
    var allNgos = [];
    var filteredNgos = [];
    var latinCharMap = {
      'ă': 'a',
      'â': 'a',
      'î': 'i',
      'ș': 's', // comma
      'ț': 't',
      'ş': 's', // cedilla
      'ţ': 't'
    };

    const selectElement = $('#search-ong-judet-select')
    const searchButton = $('#search-button')
    const resultWrapper = $('#search-result-wrapper')
    const defaultLogo = 'https://storage.googleapis.com/redirectioneaza/logo_bw.png'
    const maxDescLength = 125;

    function generateSelectOptions(localNgos){

        function createCountyOption(county, label){
            selectElement
            .append(`<option value="${county}">${label}</option>`)
        }

        var counties = localNgos.reduce(function(acc, ngo) {

            acc['judete'] = acc['judete'] || []
            acc['sectoare'] = acc['sectoare'] || []
            // check if it's sector
            if(!isNaN(ngo.active_region)){
               
                acc['sectoare'] = acc['sectoare'].includes(ngo.active_region) || ngo.active_region === null ? acc['sectoare'] : [...acc['sectoare'], ngo.active_region]

            }else{
                if(ngo.active_region === "RO"){
                    // remove RO.
                    acc['judete'] = acc['judete']
                }else{
                    acc['judete'] = acc['judete'].includes(ngo.active_region) ? acc['judete'] : [...acc['judete'], ngo.active_region]
                }
            }
            return acc

        }, {})

        var judete = counties['judete'];
        var sectoare = counties['sectoare']

        sectoare = sectoare.sort(function(a, b) {
            return a - b;
        })
       
        judete = judete.sort(function(a, b) {

            if(a < b)
                return -1
            if(a > b)
                return 1
            return 0;

        })
     
        createCountyOption("none", "Zona de activitate")
        createCountyOption("RO", "Toată țara")
        selectElement.append(`
            <optgroup label="Bucuresti">
                ${sectoare.map(function(sector){
                    return `<option value="${sector}">Sector ${sector}</option>`
                }).join('')}
            </optgroup>
        `)
        judete.forEach((county) => createCountyOption(county, county))
        active_regions = [...judete, ...sectoare, "RO", "none"]
        
    }
    
    
    function latinise(str) {
      return str.replace(/[^\u0000-\u007E]/g, function(c) {
        return latinCharMap[c] || c;
      });
    }

    function setupEasyAutocomplete(givenNgos) {
        var options = {
            data: givenNgos,
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

    function getShortenDescription(desc){
        if(desc.length > maxDescLength){
            var shortenedStr = desc.substr(0, maxDescLength)
            shortenedStr = shortenedStr.substr(0, Math.min(shortenedStr.length, shortenedStr.lastIndexOf(" ")))

            return `${shortenedStr} ...`
        }else{
            return desc
        }
    }

    $.get(api).done(function (response) {
        allNgos = response;
        filteredNgos = allNgos
        generateSelectOptions(allNgos)
        setupEasyAutocomplete(filteredNgos)
    })

    selectElement.on("change", function(){

        const value = String(this.value)
        if(value === "none"){
            setupEasyAutocomplete(allNgos)
            filteredNgos = allNgos
        }else{
            filteredNgos = allNgos.filter((ngo) => ngo.active_region === value)
            setupEasyAutocomplete(filteredNgos)
        }
        
    })

    function generateNgosOnSearch() {
        const searchValue = searcEl.val().toLocaleLowerCase()
        const selectedCounty = selectElement.val()
        const latinisedSearch = latinise(searchValue)

        if(selectedCounty === 'none' && !searchValue) {
            window.location.href = "/asociatii"
            return;
        }

        const countyAndSearchItem = filteredNgos.filter(function(ngo){
            const latinisedName = latinise(ngo.name).toLocaleLowerCase();
            return latinisedName.search(latinisedSearch) > -1;
        })

        resultWrapper.html('')

        const hasValue = countyAndSearchItem.length > 0
        resultWrapper.css('border-bottom', "1px solid lightgrey");
        if(hasValue){
            countyAndSearchItem.map(function(ngo){
                resultWrapper.append(`
                <div class="col-xs-12 col-sm-4 col-md-3">
                    <div class="ong-panel panel panel-default">
                        <a href="${ngo.url}">
                            <div class="ong-logo">
                                <img src="${ngo.logo ? ngo.logo : defaultLogo}" class="img-responsive center-block" alt="${ngo.name}-logo" />
                            </div>
                            <div class="panel-heading">${ngo.name}</div>
                        </a>
                    <div class="panel-body">
                        ${getShortenDescription(ngo.description)}
                    </div>
                    </div>
                </div>
                `)
            }).join('')
        }else{
            resultWrapper.append(`
                <p>Nu s-a găsit niciun rezultat.</p>
            `)
        }
    }

    searchButton.on("click", function(){
        generateNgosOnSearch()
    })
    
    $('#search-bar').on("keydown", function (event) {
        if (event.which === 13) {
            generateNgosOnSearch()
        }
    }); 
    // var doit;
    // window.onresize = function(){
    //   clearTimeout(doit);
    //   doit = setTimeout(setupEasyAutocomplete, 100);
    // };

})

// $('#serch-ong-judet-option').text("Change it")