// ==========================================================================
// SARTORIA CUSTOMER INTERACTIVE CLIENT CONTROLLER
// ==========================================================================

document.addEventListener("DOMContentLoaded", () => {
    // 1. Initialize Theme Toggler
    initThemeSystem();

    // 2. Alert Notification Dismissal
    initAlerts();

    // 3. Handle File Upload Previews
    initDragZonePreviews();

    // 4. Onboarding Wizard Form Progress
    initOnboardingSteps();
});

/**
 * Manages premium visual themes (Light / Dark mode toggling)
 */
function initThemeSystem() {
    const themeBtn = document.getElementById("theme-toggle");
    if (!themeBtn) return;

    // Load active theme
    const activeTheme = localStorage.getItem("theme") || "light";
    document.documentElement.setAttribute("data-theme", activeTheme);
    updateThemeIcon(themeBtn, activeTheme);

    themeBtn.addEventListener("click", () => {
        const currentTheme = document.documentElement.getAttribute("data-theme");
        const nextTheme = currentTheme === "dark" ? "light" : "dark";
        
        document.documentElement.setAttribute("data-theme", nextTheme);
        localStorage.setItem("theme", nextTheme);
        updateThemeIcon(themeBtn, nextTheme);
    });
}

function updateThemeIcon(btn, theme) {
    const icon = btn.querySelector("i");
    if (!icon) return;
    
    if (theme === "dark") {
        icon.className = "fa-solid fa-sun";
    } else {
        icon.className = "fa-solid fa-moon";
    }
}

/**
 * Handles soft fading alert banners dismissals
 */
function initAlerts() {
    const alertContainer = document.querySelector(".alert-container");
    if (!alertContainer) return;

    alertContainer.addEventListener("click", (e) => {
        if (e.target.classList.contains("alert-close") || e.target.parentElement.classList.contains("alert-close")) {
            const alert = e.target.closest(".alert");
            if (alert) {
                alert.style.opacity = "0";
                alert.style.transform = "translateY(-10px)";
                alert.style.transition = "all 0.3s ease";
                setTimeout(() => {
                    alert.remove();
                }, 300);
            }
        }
    });

    // Auto dismiss after 5 seconds
    const alerts = alertContainer.querySelectorAll(".alert");
    alerts.forEach((alert) => {
        setTimeout(() => {
            if (alert && alert.parentElement) {
                alert.style.opacity = "0";
                alert.style.transform = "translateY(-10px)";
                alert.style.transition = "all 0.3s ease";
                setTimeout(() => alert.remove(), 300);
            }
        }, 5000);
    });
}

/**
 * Drag and drop upload helper with live previews
 */
function initDragZonePreviews() {
    const dragZone = document.querySelector(".drag-zone");
    const fileInput = document.getElementById("file-upload-input");
    
    if (!dragZone || !fileInput) return;

    // Trigger click on file input
    dragZone.addEventListener("click", () => fileInput.click());

    // Highlight drop zone
    ["dragenter", "dragover"].forEach((eventName) => {
        dragZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dragZone.style.borderColor = "var(--secondary)";
            dragZone.style.background = "rgba(255, 46, 190, 0.04)";
        }, false);
    });

    ["dragleave", "drop"].forEach((eventName) => {
        dragZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dragZone.style.borderColor = "rgba(0, 212, 255, 0.25)";
            dragZone.style.background = "rgba(0, 212, 255, 0.01)";
        }, false);
    });

    // Handle dropped files
    dragZone.addEventListener("drop", (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length) {
            fileInput.files = files;
            showFilePreview(files[0]);
        }
    });

    // Handle selected files
    fileInput.addEventListener("change", function() {
        if (this.files.length) {
            showFilePreview(this.files[0]);
        }
    });
}

function showFilePreview(file) {
    const previewContainer = document.getElementById("preview-box");
    const previewImg = document.getElementById("upload-preview");
    const dragZoneText = document.getElementById("drag-zone-text");
    
    if (!previewContainer || !previewImg) return;

    const reader = new FileReader();
    reader.onload = function(e) {
        previewImg.src = e.target.result;
        previewContainer.style.display = "block";
        if (dragZoneText) {
            dragZoneText.innerText = `File Selected: ${file.name} (Change)`;
        }
    };
    reader.readAsDataURL(file);
}

/**
 * Onboarding Wizard steps toggles
 */
function initOnboardingSteps() {
    const form = document.getElementById("onboarding-form");
    if (!form) return;

    const stepCards = form.querySelectorAll(".onboarding-step-card");
    const nextBtns = form.querySelectorAll(".btn-next-step");
    const prevBtns = form.querySelectorAll(".btn-prev-step");
    const stepDots = document.querySelectorAll(".step-dot");

    let currentStep = 0;

    nextBtns.forEach((btn) => {
        btn.addEventListener("click", () => {
            // Basic inputs check for step 1
            if (currentStep === 0) {
                const ageInput = document.getElementById("age");
                if (ageInput && !ageInput.value) {
                    alert("Please provide your age to complete metrics calibration.");
                    return;
                }
            }
            
            // Move forward
            stepCards[currentStep].style.display = "none";
            stepDots[currentStep].classList.remove("active");
            
            currentStep++;
            
            stepCards[currentStep].style.display = "block";
            stepDots[currentStep].classList.add("active");
        });
    });

    prevBtns.forEach((btn) => {
        btn.addEventListener("click", () => {
            // Move backward
            stepCards[currentStep].style.display = "none";
            stepDots[currentStep].classList.remove("active");
            
            currentStep--;
            
            stepCards[currentStep].style.display = "block";
            stepDots[currentStep].classList.add("active");
        });
    });
}
