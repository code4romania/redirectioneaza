export default function(options, selectedValue) {

  return {
    selectedOption: "",
    options: [],

    submitOnChange() {
      this.$refs.select.closest("form").submit();
    },

    init() {
      // Convert all option values to strings to ensure consistency
      this.options = options.map(option => ({
        ...option,
        value: String(option.value), // Ensure option values are strings
      }));
      this.options = [...this.options];

      // Convert the selected value to string if not null
      this.selectedOption = selectedValue !== null ? String(selectedValue) : "";
    },
  };
}
