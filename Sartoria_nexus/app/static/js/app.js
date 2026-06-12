document.addEventListener("DOMContentLoaded", function () {
    // ==========================================================================
    // 1. DYNAMIC DRAG AND DROP FILE ZONE WITH PREVIEW
    // ==========================================================================
    const dragzone = document.getElementById("upload-dragzone");
    const fileInput = document.getElementById("garment_image") || document.getElementById("business_logo");
    const previewContainer = document.getElementById("file-preview-container");
    const previewImg = document.getElementById("file-preview");
    const dragPrompt = document.getElementById("dragzone-prompt");

    if (dragzone && fileInput) {
        // Highlight dragzone on hover
        ["dragenter", "dragover"].forEach(eventName => {
            dragzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dragzone.classList.add("dragover");
            }, false);
        });

        ["dragleave", "drop"].forEach(eventName => {
            dragzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dragzone.classList.remove("dragover");
            }, false);
        });

        // Handle dropped files
        dragzone.addEventListener("drop", (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files.length > 0) {
                fileInput.files = files;
                handleFilePreview(files[0]);
            }
        });

        // Trigger input on click
        dragzone.addEventListener("click", () => {
            fileInput.click();
        });

        // Handle file select
        fileInput.addEventListener("change", function () {
            if (this.files.length > 0) {
                handleFilePreview(this.files[0]);
            }
        });
    }

    function handleFilePreview(file) {
        if (!file.type.startsWith("image/")) {
            alert("Please select a valid image file (PNG, JPG, WEBP).");
            return;
        }

        const reader = new FileReader();
        reader.onload = function (e) {
            if (previewImg) {
                previewImg.src = e.target.result;
            }
            if (previewContainer) {
                previewContainer.style.display = "block";
            }
            if (dragPrompt) {
                dragPrompt.style.display = "none";
            }
        };
        reader.readAsDataURL(file);
    }

    // ==========================================================================
    // 2. AI IMAGE PIPELINE PROCESS LOADING ANIMATION
    // ==========================================================================
    const uploadForm = document.getElementById("upload-garment-form");
    const loaderOverlay = document.getElementById("ai-loader-overlay");

    if (uploadForm && loaderOverlay) {
        uploadForm.addEventListener("submit", function (e) {
            // Display loading overlay
            loaderOverlay.style.display = "flex";

            // Grab list items
            const steps = document.querySelectorAll(".ai-step-item");
            if (steps.length === 0) return;

            // Sequential timing increments to simulate premium AI classification
            const stepTimings = [0, 1800, 3400, 5000, 6800];
            
            steps.forEach((step, idx) => {
                setTimeout(() => {
                    // Mark previous step done if exists
                    if (idx > 0) {
                        steps[idx - 1].classList.remove("active");
                        steps[idx - 1].querySelector(".dot").style.background = "#00ff66";
                        steps[idx - 1].querySelector(".dot").style.boxShadow = "0 0 10px #00ff66";
                    }
                    // Activate current step
                    step.classList.add("active");
                }, stepTimings[idx]);
            });
        });
    }

    // ==========================================================================
    // 3. CHART.JS seller ANALYTICS RENDER
    // ==========================================================================
    // Global Chart.js styling overrides for glowing sci-fi interface
    if (typeof Chart !== 'undefined') {
        Chart.defaults.color = '#a0a2b3';
        Chart.defaults.font.family = "'Space Grotesk', 'Poppins', sans-serif";
        Chart.defaults.font.size = 12;

        // --- LINE CHART: DAILY TRAFFIC SCANS ---
        const dailyCanvas = document.getElementById("chart-daily-scans");
        if (dailyCanvas) {
            const chartData = JSON.parse(dailyCanvas.getAttribute("data-chart") || "[]");
            const labels = chartData.map(item => item.scan_date);
            const values = chartData.map(item => item.count);

            // Handle empty chart states
            if (labels.length === 0) {
                labels.push("No scan data");
                values.push(0);
            }

            new Chart(dailyCanvas, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Garment Scans',
                        data: values,
                        borderColor: '#5a8fd8',
                        backgroundColor: 'rgba(90, 143, 216, 0.15)',
                        borderWidth: 3,
                        pointBackgroundColor: '#8da4e3',
                        pointBorderColor: '#ffffff',
                        pointHoverRadius: 7,
                        tension: 0.4,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        y: {
                            grid: { color: 'rgba(255, 255, 255, 0.05)' },
                            ticks: { precision: 0 },
                            beginAtZero: true
                        },
                        x: {
                            grid: { display: false }
                        }
                    }
                }
            });
        }

        // --- DOUGHNUT CHART: DEVICE TYPE BREAKDOWN ---
        const deviceCanvas = document.getElementById("chart-devices");
        if (deviceCanvas) {
            const chartData = JSON.parse(deviceCanvas.getAttribute("data-chart") || "{}");
            const labels = Object.keys(chartData);
            const values = Object.values(chartData);

            if (labels.length === 0) {
                labels.push("No data");
                values.push(1);
            }

            new Chart(deviceCanvas, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: values,
                        backgroundColor: [
                            'rgba(90, 143, 216, 0.75)',  // Brand Electric Steel
                            'rgba(29, 56, 100, 0.75)',   // Brand Midnight Navy
                            'rgba(170, 180, 216, 0.75)'  // Brand Periwinkle Silver
                        ],
                        borderColor: '#06060c',
                        borderWidth: 2,
                        hoverOffset: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                color: '#a0a2b3',
                                padding: 15,
                                font: { size: 11 }
                            }
                        }
                    },
                    cutout: '65%'
                }
            });
        }

        // --- BAR CHART: GEOGRAPHIC BREAKDOWN ---
        const countryCanvas = document.getElementById("chart-countries");
        if (countryCanvas) {
            const chartData = JSON.parse(countryCanvas.getAttribute("data-chart") || "{}");
            const labels = Object.keys(chartData);
            const values = Object.values(chartData);

            if (labels.length === 0) {
                labels.push("No data");
                values.push(0);
            }

            new Chart(countryCanvas, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Scans',
                        data: values,
                        backgroundColor: 'rgba(29, 56, 100, 0.75)',
                        borderColor: '#1d3864',
                        borderWidth: 1.5,
                        borderRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        y: {
                            grid: { color: 'rgba(255, 255, 255, 0.05)' },
                            ticks: { precision: 0 },
                            beginAtZero: true
                        },
                        x: {
                            grid: { display: false }
                        }
                    }
                }
            });
        }
    }

    // ==========================================================================
    // 4. ANIMATED AUTO-DISMISS FLASH ALERTS
    // ==========================================================================
    const alerts = document.querySelectorAll(".alert");
    alerts.forEach(alert => {
        const closeBtn = alert.querySelector(".alert-close");
        if (closeBtn) {
            closeBtn.addEventListener("click", () => {
                alert.style.opacity = "0";
                setTimeout(() => alert.remove(), 400);
            });
        }
        
        // Auto dismiss after 8 seconds
        setTimeout(() => {
            if (alert) {
                alert.style.transition = "opacity 0.8s ease";
                alert.style.opacity = "0";
                setTimeout(() => alert.remove(), 800);
            }
        }, 8000);
    });
});
