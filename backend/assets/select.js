export default function (options,selectedValue) {

  return {
    selectedOption: "",
    options: [],

    handleChange() {
      this.$refs.select.closest('form').submit();
    },

    init() {
      // Convert all option values to strings to ensure consistency
      this.options = options.map(option => ({
        ...option,
        value: String(option.value) // Ensure option values are strings
      }));
      this.options = [...this.options];

      // Convert selected value to string if not null
      this.selectedOption = selectedValue !== null ? String(selectedValue) : "";
      console.log('selectedOption: "' + this.selectedOption + '"');
    }
  }
}
