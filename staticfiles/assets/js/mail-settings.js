(function () {
  'use strict';

  let loadFile = function (event) {
      var reader = new FileReader();
      reader.onload = function () {
          var output = document.getElementById('profile-img');
          if (event.target.files[0].type.match('image.*')) {
              output.src = reader.result;
          } else {
              event.target.value = '';
              alert('please select a valid image');
          }
      };
      if(event.target.files[0]){
          reader.readAsDataURL(event.target.files[0]);
      }
  };

  // for personal information language
  const multipleCancelButton = new Choices(
      '#language',
      {
          allowHTML: true,
          removeItemButton: true,
      }
  );

  // for mail language
  const multipleCancelButton1 = new Choices(
      '#mail-language',
      {
          allowHTML: true,
          removeItemButton: true,
      }
  );

  // for profile photo update
  let ProfileChange = document.querySelector('#profile-image');
  ProfileChange.addEventListener('change', loadFile);
   /* Start::Choices JS */
   document.addEventListener("DOMContentLoaded", function () {
    var genericExamples = document.querySelectorAll("[data-trigger]");
    for (let i = 0; i < genericExamples.length; ++i) {
    var element = genericExamples[i];
    new Choices(element, {
        allowHTML: true,

        placeholderValue: "This is a placeholder set in the config",
        searchPlaceholderValue: "Search",
    });
    }
});

})();