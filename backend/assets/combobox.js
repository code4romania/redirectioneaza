export default function () {
  return {
    filter: '',
    show: false,
    selected: null,
    focusedOptionIndex: null,
    options: null,
    initOptions(options) {
      this.options = this.normalizeOptions(options);
    },
    fetchOptions(endpoint) {
      const url = new URL(window.location.origin + endpoint);
      let options = null;
      fetch(url)
        .then(response => response.json())
        .then(data => options = data);
      this.options = this.normalizeOptions(options);
    },
    normalizeString(string) {
      return string.normalize('NFKD').replace(/[^\w\s.-_\/]/g, '').toLowerCase();
    },
    normalizeOptions(options) {
      return options.map(option => {
        const title = option.title ? option.title : option;
        return {
          title: title,
          value: option.value ? option.value : title,
          normalizedTitle: this.normalizeString(title)
        };
      });
    },
    filteredOptions() {
      if (!this.isOpen()) {
        return;
      }
      const searchString = this.filter ? this.normalizeString(this.filter) : '';
      return this.options
        ? this.options.filter(option => {
          return option.normalizedTitle.indexOf(searchString) > -1 || option.title.indexOf(searchString) > -1
        }).map(option => option)
        : {}
    },
    closeOptionsList() {
      this.show = false;
      this.filter = this.selectedOption();
      this.focusedOptionIndex = this.selected ? this.focusedOptionIndex : null;
    },
    openOptionsList() {
      this.show = true;
      this.filter = '';
    },
    toggleOptionsList() {
      if (this.show) {
        this.closeOptionsList();
      } else {
        this.openOptionsList()
      }
    },
    isOpen() {
      return this.show === true
    },
    onOptionClick(index) {
      this.focusedOptionIndex = index;
      this.selectOption();
    },
    selectedOption() {
      return this.selected ? this.selected.title : this.filter;
    },
    selectOption() {
      if (!this.isOpen()) {
        return;
      }
      this.focusedOptionIndex = this.focusedOptionIndex ?? 0;
      const selected = this.filteredOptions()[this.focusedOptionIndex]
      if (this.selected && this.selected === selected) {
        this.selected = null;
        this.filter = '';
      } else {
        this.selected = selected;
        this.filter = this.selectedOption();
      }
      this.closeOptionsList();
    },
    focusPrevOption() {
      if (!this.isOpen()) {
        return;
      }
      const optionsNum = Object.keys(this.filteredOptions()).length - 1;
      if (this.focusedOptionIndex > 0 && this.focusedOptionIndex <= optionsNum) {
        this.focusedOptionIndex--;
      } else if (this.focusedOptionIndex === 0) {
        this.focusedOptionIndex = '';
      }
    },
    focusNextOption() {
      const optionsNum = Object.keys(this.filteredOptions()).length - 1;
      if (!this.isOpen()) {
        this.openOptionsList();
      }
      if (this.focusedOptionIndex == null || this.focusedOptionIndex === optionsNum) {
        this.focusedOptionIndex = 0;
      } else if (this.focusedOptionIndex >= 0 && this.focusedOptionIndex < optionsNum) {
        this.focusedOptionIndex++;
      }
    }
  }
}
