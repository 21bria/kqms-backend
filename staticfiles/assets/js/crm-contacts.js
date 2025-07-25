/* Image upload */
let loadFile = function (event) {
  var reader = new FileReader();
  reader.onload = function () {
    var output = document.getElementById("profile-img");
    if (event.target.files[0].type.match("image.*")) {
      output.src = reader.result;
    } else {
      event.target.value = "";
      alert("please select a valid image");
    }
  };
  if(event.target.files[0]){
    reader.readAsDataURL(event.target.files[0]);
}
};

// for profile photo update
let ProfileChange = document.querySelector("#profile-change");
ProfileChange.addEventListener("change", loadFile);

/* multi select with remove button */
const multipleCancelButton = new Choices("#choices-multiple-remove-button1", {
  allowHTML: true,
  removeItemButton: true,
});
const multipleCancelButton1 = new Choices("#choices-multiple-remove-button2", {
  allowHTML: true,
  removeItemButton: true,
});

/* TargetDate Picker */
flatpickr("#targetDate", {
  enableTime: true,
  dateFormat: "Y-m-d H:i",
});

/* For Delete Contact */
let invoicebtn = document.querySelectorAll(".contact-delete");
invoicebtn.forEach((eleBtn) => {
  eleBtn.onclick = () => {
    let invoice = eleBtn.closest(".crm-contact");
    invoice.remove();
  };
});
