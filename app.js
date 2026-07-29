let imagebase64=null;

const fileInput=document.getElementById("file-input");
const preview=document.getElementById("preview");
const analyzeBtn=document.getElementById("analyze-btn");
const resultSection=document.getElementById("result-section");

fileInput.addEventListener("chnage", function (e){
    const file=e.target.files[0];
    if(!file) return;

    preview.src = URL.createObjectURL(file);
    preview.style.display = "block";

     const reader = new FileReader();

  reader.onload = function(ev) {
    imageBase64 = ev.target.result.split(",")[1];
    analyzeBtn.disabled = false;
    console.log("Image ready — base64 stored");
  };

  reader.readAsDataURL(file);
});




