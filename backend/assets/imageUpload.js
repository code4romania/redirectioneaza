export default function() {
  return {
    generatePreview(event) {
      const file = event.target.files[0];

      if (!file) {
        return;
      }

      const reader = new FileReader();
      reader.onload = () => (this.$refs.preview.src = reader.result);
      reader.readAsDataURL(file);
    }
  }
}
