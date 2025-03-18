export default function (options, value) {
  return {
    options: [],
    query: null,
    filteredOptions: [],

    isOpen: false,
    selectedOption: null,

    init() {
      this.options = this.normalizeOptions(options);

      const filter = (query) => {
        query = this.normalizeString(query);

        if (! query) {
          this.filteredOptions = this.options;
        } else {
          this.filteredOptions = this.options.filter((option) => {
            return option.normalizedTitle.indexOf(query) > -1 || option.title.indexOf(query) > -1;
          });
        }
      };

      filter();
      this.$watch('query', filter);
    },

    select(option) {
      this.selectedOption = option.value;
      this.$refs.input.value = option.value;
      this.close();


      this.$refs.input.closest('form').submit();
    },

    close() {
      this.isOpen = false;
      this.query = null;
    },

    normalizeOptions(options) {
      return options.map(option => {
        const title = option?.title || option;
        const value = option?.value || title;

        return {
          title,
          value,
          normalizedTitle: this.normalizeString(title)
        };
      });
    },

    normalizeString(string) {
      if (! string) {
        return '';
      }

      return string.normalize('NFKD').replace(/[^\w\s.-_\/]/g, '').toLowerCase();
    },


////////////////////////////////////////////////////////////////
    // filter: value,
    // show: false,
    // selected: null,
    // focusedOptionIndex: null,
    // // options: null,
    // inputId: null,
    // // submitOnClose: null,

    // init() {

    //   console.log(value);

    //   if (options) {
    //     this.initOptions(options);
    //   } else if (endpoint) {
    //     this.fetchOptions(endpoint);
    //   }
    // },


    // initOptions(options, inputId) {
    //   this.options = this.normalizeOptions(options);
    //   this.inputId = inputId;
    //   // this.initSubmission(submitOnSelect);
    // },
    // fetchOptions(endpoint, inputId) {
    //   const url = new URL(window.location.origin + endpoint);
    //   let options = null;
    //   fetch(url)
    //     .then(response => response.json())
    //     .then(data => options = data);
    //   this.options = this.normalizeOptions(options);
    //   this.inputId = inputId;
    //   // this.initSubmission(submitOnSelect);
    // },
    // // initSubmission(submitOnClose) {
    // //   if (submitOnClose.length > 0) {
    // //     this.submitOnClose = submitOnClose;
    // //   }
    // // },
    // normalizeString(string) {
    //   if (! string) {
    //     return '';
    //   }

    //   return string.normalize('NFKD').replace(/[^\w\s.-_\/]/g, '').toLowerCase();
    // },
    // normalizeOptions(options) {
    //   return options.map(option => {
    //     const title = option.title ? option.title : option;
    //     return {
    //       title: title,
    //       value: option.value ? option.value : title,
    //       normalizedTitle: this.normalizeString(title)
    //     };
    //   });
    // },
    // filteredOptions() {
    //   if (!this.isOpen()) {
    //     return;
    //   }
    //   const searchString = this.filter ? this.normalizeString(this.filter) : '';
    //   return this.options
    //     ? this.options.filter(option => {
    //       return option.normalizedTitle.indexOf(searchString) > -1 || option.title.indexOf(searchString) > -1
    //     }).map(option => option)
    //     : {}
    // },
    // closeOptionsList() {
    //   this.show = false;
    //   this.filter = this.selectedOption();
    //   this.focusedOptionIndex = this.selected ? this.focusedOptionIndex : null;
    //   console.log("AAAAAAAAA");
    //   console.log(this.filter);
    //   if (this.inputId && this.filter) {
    //     document.getElementById(this.inputId).value = this.filter;
    //   }
    //   // if (this.submitOnClose && this.filter) {
    //   //   document.getElementById(this.submitOnClose).submit();
    //   // }
    // },
    // openOptionsList() {
    //   this.show = true;
    //   this.filter = '';
    // },
    // toggleOptionsList() {
    //   if (this.show) {
    //     this.closeOptionsList();
    //   } else {
    //     this.openOptionsList()
    //   }
    // },
    // isOpen() {
    //   return this.show === true
    // },
    // onOptionClick(index) {
    //   this.focusedOptionIndex = index;
    //   this.selectOption();
    // },
    // selectedOption() {
    //   return this.selected ? this.selected.title : this.filter;
    // },
    // selectOption() {
    //   if (!this.isOpen()) {
    //     return;
    //   }
    //   this.focusedOptionIndex = this.focusedOptionIndex ?? 0;
    //   const selected = this.filteredOptions()[this.focusedOptionIndex]
    //   if (this.selected && this.selected === selected) {
    //     this.selected = null;
    //     this.filter = '';
    //   } else {
    //     this.selected = selected;
    //     this.filter = this.selectedOption();
    //   }
    //   this.closeOptionsList();
    // },
    // focusPrevOption() {
    //   if (!this.isOpen()) {
    //     return;
    //   }
    //   const optionsNum = Object.keys(this.filteredOptions()).length - 1;
    //   if (this.focusedOptionIndex > 0 && this.focusedOptionIndex <= optionsNum) {
    //     this.focusedOptionIndex--;
    //   } else if (this.focusedOptionIndex === 0) {
    //     this.focusedOptionIndex = '';
    //   }
    // },
    // focusNextOption() {
    //   const optionsNum = Object.keys(this.filteredOptions()).length - 1;
    //   if (!this.isOpen()) {
    //     this.openOptionsList();
    //   }
    //   if (this.focusedOptionIndex == null || this.focusedOptionIndex === optionsNum) {
    //     this.focusedOptionIndex = 0;
    //   } else if (this.focusedOptionIndex >= 0 && this.focusedOptionIndex < optionsNum) {
    //     this.focusedOptionIndex++;
    //   }
    // }
  }
}
