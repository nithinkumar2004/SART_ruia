// ==========================================================================
// PROGRESSIVE WEB APP (PWA) INSTALL CONTROLLER
// ==========================================================================

let deferredInstallPrompt = null;

// Register Service Worker
if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
        navigator.serviceWorker.register("/sw.js")
            .then((registration) => {
                console.log("Sartoria ServiceWorker registered successfully with scope:", registration.scope);
            })
            .catch((err) => {
                console.log("Sartoria ServiceWorker registration failed:", err);
            });
    });
}

// Intercept application installation prompt
window.addEventListener("beforeinstallprompt", (e) => {
    // Prevent default browser display prompt
    e.preventDefault();
    deferredInstallPrompt = e;
    
    // Display custom PWA installation banner popup
    showPWAInstallPopup();
});

function showPWAInstallPopup() {
    const installBanner = document.getElementById("pwa-install-banner");
    if (installBanner) {
        installBanner.style.display = "flex";
        installBanner.style.opacity = "1";
        installBanner.style.transform = "translateY(0)";
    }
}

// Handle Install Click Action
document.addEventListener("DOMContentLoaded", () => {
    const installBtn = document.getElementById("pwa-install-btn");
    const closeBtn = document.getElementById("pwa-close-btn");
    const installBanner = document.getElementById("pwa-install-banner");

    if (installBtn) {
        installBtn.addEventListener("click", async () => {
            if (!deferredInstallPrompt) return;
            
            // Show prompt
            deferredInstallPrompt.prompt();
            
            // Wait for user's decision
            const { outcome } = await deferredInstallPrompt.userChoice;
            console.log(`PWA Installation user outcome: ${outcome}`);
            
            // Reset prompt
            deferredInstallPrompt = null;
            
            // Hide Banner
            if (installBanner) {
                installBanner.style.display = "none";
            }
        });
    }

    if (closeBtn && installBanner) {
        closeBtn.addEventListener("click", () => {
            installBanner.style.opacity = "0";
            installBanner.style.transform = "translateY(20px)";
            setTimeout(() => {
                installBanner.style.display = "none";
            }, 300);
        });
    }
});

// Detect active standalone mode (Installed app status check)
window.addEventListener("appinstalled", (e) => {
    console.log("Sarotoria successfully installed as a Progressive Web App.");
    const installBanner = document.getElementById("pwa-install-banner");
    if (installBanner) {
        installBanner.style.display = "none";
    }
});
