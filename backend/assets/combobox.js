export default function (options, currentValue) {
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

        if (!query) {
          this.filteredOptions = this.options;
        } else {
          this.filteredOptions = this.options.filter((option) => {
            return option.normalizedTitle.indexOf(query) > -1 || option.title.indexOf(query) > -1;
          });
        }
      };

      filter();
      this.$watch('query', filter);

      if (currentValue) {
        const selectedOption = this.options.find(option => option.value === currentValue);
        this.setSelectedOption(selectedOption);
      }
    },
    setSelectedOption(option) {
      this.selectedOption = option.value;

      this.$refs.input.value = option.value;
      this.$refs.display.value = option.title;

      this.close();
    },
    select(option) {
      if (!option || !this.isOpen) {
        return;
      }
      this.setSelectedOption(option);

      this.$refs.input.closest('form').submit();
    },

    close() {
      this.isOpen = false;
      this.query = this.selectedOption ? this.selectedOption : null;
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
      if (!string) {
        return '';
      }

      return string.normalize('NFKD').replace(/[^\w\s.-_\/]/g, '').toLowerCase();
    },
  }
}
