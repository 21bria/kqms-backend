(function() {
    "use strict"
    
    // for personal information language
    const multipleCancelButton = new Choices(
        '#language',
        {
            allowHTML: true,
            removeItemButton: true,
        }
    );
    
    // for personal information language
    const multipleCancelButton2 = new Choices(
        '#skills',
        {
            allowHTML: true,
            removeItemButton: true,
        }
    );
    
    // for personal information language
    const multipleCancelButton3 = new Choices(
        '#qualification',
        {
            allowHTML: true,
            removeItemButton: true,
        }
    );
   
     /* Start::Choices JS */
  document.addEventListener("DOMContentLoaded", function () {
    var genericExamples = document.querySelectorAll("[data-trigger]");
    for (let i = 0; i < genericExamples.length; ++i) {
      var element = genericExamples[i];
      new Choices(element, {
        allowHTML: true,

        placeholderValue: "This is a placeholder set in the config",
        searchPlaceholderValue: "Search Crypto Currency",
      });
    }
  });
     
})();