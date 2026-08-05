let imageBase64=null;

const fileInput=document.getElementById("file-input");
const preview=document.getElementById("preview");
const analyzeBtn=document.getElementById("analyze-btn");
const resultSection=document.getElementById("result-section");

fileInput.addEventListener("change", function (e){
    console.log("File input changed");
    console.log("Files:", e.target.files);
  



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
function  getConditions(){
    const checkboxes =[
    { id: "diabetes",     label: "Diabetes"     },
    { id: "hypertension", label: "Hypertension" },
    { id: "thyroid",      label: "Thyroid"      },
    { id: "heart",        label: "Heart Disease"},
    { id: "pcos",         label: "PCOS"         },
    { id: "pcod",         label: "PCOD"         }
  ];
   const ticked = [];
  checkboxes.forEach(function(item) {
    const checkbox = document.getElementById(item.id);
    if (checkbox.checked === true) {
      ticked.push(item.label);
    }
  });
  if (ticked.length === 0) { return "None"; }
  return ticked.join(", ");
}
function getProfile() {
  const name            = document.getElementById("name").value;
  const age             = document.getElementById("age").value;
  const gender          = document.getElementById("gender").value;
  const conditions      = getConditions();
  const otherConditions = document.getElementById("other-conditions").value;
  const allergies       = document.getElementById("allergies").value;
  const goals           = document.getElementById("goals").value;

  return {
    name,
    age,
    gender,
    conditions,
    otherConditions,
    allergies,
    goals
  };
}
