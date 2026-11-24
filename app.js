let imageBase64=null;

const fileInput=document.getElementById("file-input");
const preview=document.getElementById("preview");
const analyzeBtn=document.getElementById("analyze-btn");
const resultSection=document.getElementById("result-section");

const cameraBtn = document.getElementById("camera-btn");
const galleryBtn = document.getElementById("gallery-btn");
const cameraInput = document.getElementById("camera-input");

cameraBtn.addEventListener("click", function() {
    cameraInput.click();
});

galleryBtn.addEventListener("click", function() {
    fileInput.click();
});

function handleImageSelection(e) {

    const file = e.target.files[0];

    if (!file) return;

    // Check image format
    if (!file.type.startsWith("image/")) {
        alert("Please select a valid image.");
        e.target.value = "";
        return;
    }

    // Check image size (maximum 10 MB)
    if (file.size > 10 * 1024 * 1024) {
        alert("Image size must be less than 10 MB.");
        e.target.value = "";
        return;
    }

    // Display image preview
    preview.src = URL.createObjectURL(file);
    preview.style.display = "block";

    // Disable Analyze until image conversion finishes
    analyzeBtn.disabled = true;

    // Convert image into Base64
    const reader = new FileReader();

    reader.onload = function(ev) {

        imageBase64 = ev.target.result.split(",")[1];

        analyzeBtn.disabled = false;

        console.log("Image ready - Base64 stored");
    };

    reader.onerror = function() {
        alert("Unable to read this image. Please try again.");
        imageBase64 = null;
        analyzeBtn.disabled = true;
    };

    reader.readAsDataURL(file);
}


// Handle camera image
cameraInput.addEventListener("change", handleImageSelection);

// Handle gallery image
fileInput.addEventListener("change", handleImageSelection);


// =====================================
// GET HEALTH CONDITIONS
// =====================================

function getConditions() {

    const checkboxes = [
        { id: "diabetes", label: "Diabetes" },
        { id: "hypertension", label: "Hypertension" },
        { id: "thyroid", label: "Thyroid" },
        { id: "heart", label: "Heart Disease" },
        { id: "pcos", label: "PCOS" },
        { id: "pcod", label: "PCOD" }
    ];

    const ticked = [];

    checkboxes.forEach(function(item) {

        const checkbox = document.getElementById(item.id);

        if (checkbox.checked === true) {
            ticked.push(item.label);
        }

    });

    if (ticked.length === 0) {
        return "None";
    }

    return ticked.join(", ");
}


// =====================================
// GET USER PROFILE
// =====================================

function getProfile() {

    const name = document.getElementById("name").value;
    const age = document.getElementById("age").value;
    const gender = document.getElementById("gender").value;

    const conditions = getConditions();

    const otherConditions = document.getElementById("other-conditions").value;
    const allergies = document.getElementById("allergies").value;
    const goals = document.getElementById("goals").value;

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


// =====================================
// ANALYZE BUTTON
// =====================================

analyzeBtn.addEventListener("click", async function() {

    console.log("Analyze clicked");

    const profile = getProfile();

    console.log("User profile:", profile);

    if (!imageBase64) {
        alert("Please upload or capture a food label image first.");
        return;
    }

    try {

        analyzeBtn.disabled = true;
        analyzeBtn.textContent = "Analyzing...";

        const response = await fetch("http://127.0.0.1:5000/analyze", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                profile: profile,
                image: imageBase64
            })

        });

        const data = await response.json();

        console.log("Analysis result:", data);

        if (!response.ok) {
            throw new Error(data.error || "Analysis failed.");
        }

        alert("Request completed. Check the console for the result.");

    }

    catch(error) {

        console.error("Error:", error);

        alert("Something went wrong: " + error.message);

    }

    finally {

        analyzeBtn.disabled = false;
        analyzeBtn.textContent = "Analyze";

    }

});