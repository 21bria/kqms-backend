
(function() {
  window.addEventListener('load', () => {
    // Textarea auto height
    const textareas = [
      '#hs-floating-textarea',
      '#hs-floating-textarea-gray',
      '#hs-floating-textarea-underline',
      '#hs-autoheight-textarea', '#hs-textarea-ex-1',
      '#hs-textarea-ex-2',
    ]

    textareas.forEach((el) => {
      const textarea = document.querySelector(el);

      textareaAutoHeight(textarea, 3);

      textarea.addEventListener('input', () => {
        textareaAutoHeight(textarea, 3);
      });
    });

    function textareaAutoHeight(el, offsetTop = 0) {
      el.style.height = 'auto';
      el.style.height = `${el.scrollHeight + offsetTop}px`;
    }
  })
})()