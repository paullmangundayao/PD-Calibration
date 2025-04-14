// Wait for window load to add the "loaded" class for animations
window.addEventListener('load', () => {
  document.body.classList.add('loaded');
});

// Progress bar handling
const progressContainer = document.getElementById('progressContainer');
const progressBar = document.getElementById('progressBar');
const progressText = document.getElementById('progressText');

function updateProgressBar(percentage, text) {
  progressContainer.style.display = 'block';
  progressBar.style.width = `${percentage}%`;
  progressText.textContent = text;
}

function resetProgressBar() {
  progressContainer.style.display = 'none';
  progressBar.style.width = '0%';
  progressText.textContent = '';
}

// Activate Initial Sealing Button Listener
document.getElementById('initialSealButton').addEventListener('click', async () => {
  updateProgressBar(10, 'Feeding bubble wrap...');

  try {
    const response = await fetch('/feed-wrap', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ length: 50 })
    });
    const result = await response.json();

    if (!response.ok) throw new Error(result.message || 'Feed failed');
    updateProgressBar(60, 'Feed complete!');
    setTimeout(() => {
      resetProgressBar();
      document.getElementById('sealConfirmModal').style.display = 'block';
    }, 1000);
  } catch (error) {
    alert("Error: " + error.message);
    resetProgressBar();
  }
});

// Confirm button inside modal
document.getElementById('confirmSeal').addEventListener('click', async () => {
  document.getElementById('sealConfirmModal').style.display = 'none';
  updateProgressBar(10, 'Performing sealing...');

  try {
    const response = await fetch('/initial-seal', { method: 'POST' });
    const result = await response.json();

    if (!response.ok) throw new Error(result.message || 'Sealing failed');
    alert(result.message);
    updateProgressBar(100, 'Sealing complete!');
  } catch (error) {
    alert("Error: " + error.message);
  } finally {
    setTimeout(() => resetProgressBar(), 2000);
  }
});

// Toggle the display of the menu
function toggleMenu() {
  const menuContent = document.getElementById("menuContent");
  menuContent.style.display = menuContent.style.display === "flex" ? "none" : "flex";
}

// Toggle tooltips
function toggleTooltip(tooltipId) {
  const tooltip = document.getElementById(tooltipId);
  tooltip.style.display = tooltip.style.display === 'block' ? 'none' : 'block';
}

// Toggle dark mode
function toggleDarkMode() {
  document.body.classList.toggle("dark-mode");
  document.querySelectorAll('.card-light, button').forEach(el => {
    el.style.display = 'none';
    el.offsetHeight; // Trigger reflow
    el.style.display = '';
  });
}

// Show delivery popup
function showDeliveryPopup() {
  const popup = document.createElement('div');
  popup.id = 'deliveryPopup';
  popup.innerHTML = `
    <div class="popup-content">
      <h3>Scanning Complete!</h3>
      <p>What would you like to do next?</p>
      <div class="popup-buttons">
        <button id="deliverButton">Deliver Product</button>
        <button id="recaptureButton">Recapture Dimensions</button>
      </div>
    </div>
  `;
  document.body.appendChild(popup);

  // Delivery button
  document.getElementById('deliverButton').addEventListener('click', async () => {
    try {
      updateProgressBar(30, 'Initiating delivery...');
      const response = await fetch('/deliver-product', { method: 'POST' });
      if (!response.ok) throw new Error('Delivery failed');
      const result = await response.json();
      alert(result.message);

      document.getElementById('clearButton').click();
      popup.remove();
      resetProgressBar();
    } catch (error) {
      alert(error.message);
      popup.remove();
      resetProgressBar();
    }
  });

  // Recapture button
  document.getElementById('recaptureButton').addEventListener('click', () => {
    popup.remove();
    document.getElementById('clearButton').click();
  });
}

// Emergency stop
document.getElementById('emergencyStopButton').addEventListener('click', async () => {
  const confirmStop = confirm("Are you sure you want to trigger the EMERGENCY STOP?");
  if (!confirmStop) return;

  updateProgressBar(50, 'Stopping all hardware...');
  try {
    const response = await fetch('/emergency-stop', { method: 'POST' });
    const result = await response.json();

    if (!response.ok) throw new Error(result.message || 'Emergency stop failed');
    alert(result.message);
  } catch (error) {
    alert("Error: " + error.message);
  } finally {
    resetProgressBar();
  }
});

// Detect dimensions
document.getElementById('detectButton').addEventListener('click', async () => {
  updateProgressBar(10, 'Starting detection...');
  try {
    const response = await fetch('/capture-dimensions');
    if (!response.ok) throw new Error('Failed to capture dimensions. Please check your camera or sensor setup.');

    updateProgressBar(50, 'Processing captured image...');
    const data = await response.json();
    if (data.error) throw new Error(data.error);

    // Captured Image
    document.getElementById('capturedImage').innerHTML = `
      <h2>Captured Image</h2>
      <img src="${data.image_url}" alt="Captured Image" style="width:100%">
    `;

    // Detected Dimensions
    document.getElementById('detectedDimensions').innerHTML = `
      <h2>Detected Dimensions</h2>
      <p>Length: ${data.measured_dimensions.length.toFixed(2)} cm</p>
      <p>Width: ${data.measured_dimensions.width.toFixed(2)} cm</p>
      <p>Height: ${data.measured_dimensions.height.toFixed(2)} cm</p>
    `;

    // Optimal Results
    document.getElementById('resultsContainer').innerHTML = `
      <h2>Optimal Result</h2>
      <p>Optimal Dimensions:</p>
      <ul>
        <li>Length: ${data.optimal_dimensions["Optimal Length"].toFixed(2)} cm</li>
        <li>Width: ${data.optimal_dimensions["Optimal Width"].toFixed(2)} cm</li>
        <li>Height: ${data.optimal_dimensions["Optimal Height"].toFixed(2)} cm</li>
      </ul>
      <p>Bubble Wrap Size:</p>
      <ul>
        <li>Length: ${data.bubble_wrap_size.length.toFixed(2)} cm</li>
        <li>Width: ${data.bubble_wrap_size.width.toFixed(2)} cm</li>
      </ul>
    `;

    updateProgressBar(100, 'Detection and processing complete!');
    setTimeout(() => {
      resetProgressBar();
      showDeliveryPopup();
    }, 5000);
  } catch (error) {
    alert(error.message);
    resetProgressBar();
  }
});

// Clear data from containers
document.getElementById('clearButton').addEventListener('click', () => {
  document.getElementById('capturedImage').innerHTML = '<h2>Captured Image</h2>';
  document.getElementById('detectedDimensions').innerHTML = '<h2>Detected Dimensions</h2>';
  document.getElementById('resultsContainer').innerHTML = '<h2>Optimal Result</h2>';
  console.log('Data cleared from all containers.');
});
