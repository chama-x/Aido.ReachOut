/**
 * Options page script for Google Maps Business Scraper Chrome Extension
 * 
 * This script handles the options page interactions, saves user preferences,
 * and manages the location templates.
 */

// Default settings
const DEFAULT_SETTINGS = {
  maxBusinesses: 100,
  scrollDelay: 500,
  maxScrollAttempts: 20,
  extractDetails: true,
  validateSriLankanNumbers: true,
  convertToInternationalFormat: true,
  includeLocalFormat: true,
  identifyNumberType: true,
  defaultExportFormat: 'json',
  includeHeaders: true,
  filenameTemplate: 'sri_lanka_businesses_{date}',
  savedLocations: [
    { name: 'Colombo', radius: 5 },
    { name: 'Kandy', radius: 3 },
    { name: 'Galle', radius: 2 },
    { name: 'Jaffna', radius: 5 }
  ]
};

// DOM Elements
const elements = {
  // Extraction settings
  maxBusinesses: document.getElementById('max-businesses'),
  scrollDelay: document.getElementById('scroll-delay'),
  maxScrollAttempts: document.getElementById('max-scroll-attempts'),
  extractDetails: document.getElementById('extract-details'),
  
  // Phone number validation
  validateSLNumbers: document.getElementById('validate-sl-numbers'),
  convertInternational: document.getElementById('convert-international'),
  includeLocalFormat: document.getElementById('include-local-format'),
  identifyNumberType: document.getElementById('identify-number-type'),
  
  // Location templates
  newLocation: document.getElementById('new-location'),
  newRadius: document.getElementById('new-radius'),
  addLocationBtn: document.getElementById('add-location'),
  locationsList: document.getElementById('locations-list'),
  
  // Export settings
  formatCsv: document.getElementById('format-csv'),
  formatJson: document.getElementById('format-json'),
  includeHeaders: document.getElementById('include-headers'),
  filenameTemplate: document.getElementById('filename-template'),
  
  // Buttons
  saveSettingsBtn: document.getElementById('save-settings'),
  resetSettingsBtn: document.getElementById('reset-settings'),
  
  // Status
  statusMessage: document.getElementById('status-message')
};

/**
 * Initialize the options page
 */
function initialize() {
  console.log('Initializing options page');
  
  // Load settings
  loadSettings();
  
  // Set up event listeners
  setupEventListeners();
}

/**
 * Set up event listeners
 */
function setupEventListeners() {
  // Add location button
  elements.addLocationBtn.addEventListener('click', addLocation);
  
  // Save settings button
  elements.saveSettingsBtn.addEventListener('click', saveSettings);
  
  // Reset settings button
  elements.resetSettingsBtn.addEventListener('click', resetSettings);
}

/**
 * Load settings from storage
 */
function loadSettings() {
  chrome.storage.sync.get('scraperConfig', (result) => {
    const settings = result.scraperConfig || DEFAULT_SETTINGS;
    
    // Apply settings to form
    applySettings(settings);
  });
}

/**
 * Apply settings to form
 */
function applySettings(settings) {
  // Extraction settings
  elements.maxBusinesses.value = settings.maxBusinesses || DEFAULT_SETTINGS.maxBusinesses;
  elements.scrollDelay.value = settings.scrollDelay || DEFAULT_SETTINGS.scrollDelay;
  elements.maxScrollAttempts.value = settings.maxScrollAttempts || DEFAULT_SETTINGS.maxScrollAttempts;
  elements.extractDetails.checked = settings.extractDetails !== undefined ? settings.extractDetails : DEFAULT_SETTINGS.extractDetails;
  
  // Phone number validation
  elements.validateSLNumbers.checked = settings.validateSriLankanNumbers !== undefined ? settings.validateSriLankanNumbers : DEFAULT_SETTINGS.validateSriLankanNumbers;
  elements.convertInternational.checked = settings.convertToInternationalFormat !== undefined ? settings.convertToInternationalFormat : DEFAULT_SETTINGS.convertToInternationalFormat;
  elements.includeLocalFormat.checked = settings.includeLocalFormat !== undefined ? settings.includeLocalFormat : DEFAULT_SETTINGS.includeLocalFormat;
  elements.identifyNumberType.checked = settings.identifyNumberType !== undefined ? settings.identifyNumberType : DEFAULT_SETTINGS.identifyNumberType;
  
  // Export settings
  if (settings.defaultExportFormat === 'csv') {
    elements.formatCsv.checked = true;
  } else {
    elements.formatJson.checked = true;
  }
  
  elements.includeHeaders.checked = settings.includeHeaders !== undefined ? settings.includeHeaders : DEFAULT_SETTINGS.includeHeaders;
  elements.filenameTemplate.value = settings.filenameTemplate || DEFAULT_SETTINGS.filenameTemplate;
  
  // Location templates
  renderLocationsList(settings.savedLocations || DEFAULT_SETTINGS.savedLocations);
}

/**
 * Render the locations list
 */
function renderLocationsList(locations) {
  // Clear the list
  elements.locationsList.innerHTML = '';
  
  if (locations.length === 0) {
    const emptyMessage = document.createElement('div');
    emptyMessage.className = 'empty-message';
    emptyMessage.textContent = 'No saved locations';
    elements.locationsList.appendChild(emptyMessage);
    return;
  }
  
  // Add each location
  locations.forEach((location, index) => {
    const locationItem = document.createElement('div');
    locationItem.className = 'location-item';
    locationItem.innerHTML = `
      <div class="location-info">
        <div class="location-name">${location.name}</div>
        <div class="location-radius">Radius: ${location.radius} km</div>
      </div>
      <div class="location-actions">
        <button class="delete-location" data-index="${index}">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 6h18"></path>
            <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path>
            <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path>
          </svg>
        </button>
      </div>
    `;
    
    elements.locationsList.appendChild(locationItem);
    
    // Add delete event listener
    locationItem.querySelector('.delete-location').addEventListener('click', () => {
      deleteLocation(index);
    });
  });
}

/**
 * Add a new location
 */
function addLocation() {
  const name = elements.newLocation.value.trim();
  const radius = parseInt(elements.newRadius.value, 10);
  
  if (!name) {
    showToast('Please enter a location name');
    return;
  }
  
  if (isNaN(radius) || radius < 1 || radius > 50) {
    showToast('Radius must be between 1 and 50 km');
    return;
  }
  
  // Get current locations
  chrome.storage.sync.get('scraperConfig', (result) => {
    const settings = result.scraperConfig || DEFAULT_SETTINGS;
    const locations = settings.savedLocations || [];
    
    // Check if location already exists
    const existingIndex = locations.findIndex(loc => loc.name.toLowerCase() === name.toLowerCase());
    if (existingIndex !== -1) {
      // Update existing location
      locations[existingIndex].radius = radius;
      showToast(`Updated location: ${name}`);
    } else {
      // Add new location
      locations.push({ name, radius });
      showToast(`Added location: ${name}`);
    }
    
    // Save and render
    settings.savedLocations = locations;
    chrome.storage.sync.set({ scraperConfig: settings }, () => {
      renderLocationsList(locations);
      
      // Clear inputs
      elements.newLocation.value = '';
      elements.newRadius.value = '5';
    });
  });
}

/**
 * Delete a location
 */
function deleteLocation(index) {
  chrome.storage.sync.get('scraperConfig', (result) => {
    const settings = result.scraperConfig || DEFAULT_SETTINGS;
    const locations = settings.savedLocations || [];
    
    if (index >= 0 && index < locations.length) {
      const deletedName = locations[index].name;
      locations.splice(index, 1);
      
      // Save and render
      settings.savedLocations = locations;
      chrome.storage.sync.set({ scraperConfig: settings }, () => {
        renderLocationsList(locations);
        showToast(`Deleted location: ${deletedName}`);
      });
    }
  });
}

/**
 * Save settings
 */
function saveSettings() {
  // Collect settings from form
  const settings = {
    maxBusinesses: parseInt(elements.maxBusinesses.value, 10),
    scrollDelay: parseInt(elements.scrollDelay.value, 10),
    maxScrollAttempts: parseInt(elements.maxScrollAttempts.value, 10),
    extractDetails: elements.extractDetails.checked,
    validateSriLankanNumbers: elements.validateSLNumbers.checked,
    convertToInternationalFormat: elements.convertInternational.checked,
    includeLocalFormat: elements.includeLocalFormat.checked,
    identifyNumberType: elements.identifyNumberType.checked,
    defaultExportFormat: elements.formatCsv.checked ? 'csv' : 'json',
    includeHeaders: elements.includeHeaders.checked,
    filenameTemplate: elements.filenameTemplate.value
  };
  
  // Validate settings
  if (isNaN(settings.maxBusinesses) || settings.maxBusinesses < 1 || settings.maxBusinesses > 500) {
    showToast('Maximum businesses must be between 1 and 500');
    return;
  }
  
  if (isNaN(settings.scrollDelay) || settings.scrollDelay < 300 || settings.scrollDelay > 2000) {
    showToast('Scroll delay must be between 300 and 2000 ms');
    return;
  }
  
  if (isNaN(settings.maxScrollAttempts) || settings.maxScrollAttempts < 5 || settings.maxScrollAttempts > 50) {
    showToast('Maximum scroll attempts must be between 5 and 50');
    return;
  }
  
  // Get current settings to preserve saved locations
  chrome.storage.sync.get('scraperConfig', (result) => {
    const currentSettings = result.scraperConfig || DEFAULT_SETTINGS;
    
    // Merge with saved locations
    settings.savedLocations = currentSettings.savedLocations || DEFAULT_SETTINGS.savedLocations;
    
    // Save settings
    chrome.storage.sync.set({ scraperConfig: settings }, () => {
      elements.statusMessage.textContent = 'Settings saved!';
      showToast('Settings saved successfully');
      
      // Clear status message after 3 seconds
      setTimeout(() => {
        elements.statusMessage.textContent = '';
      }, 3000);
    });
  });
}

/**
 * Reset settings to default
 */
function resetSettings() {
  if (confirm('Are you sure you want to reset all settings to default?')) {
    // Apply default settings
    applySettings(DEFAULT_SETTINGS);
    
    // Save default settings
    chrome.storage.sync.set({ scraperConfig: DEFAULT_SETTINGS }, () => {
      elements.statusMessage.textContent = 'Settings reset to default!';
      showToast('Settings reset to default');
      
      // Clear status message after 3 seconds
      setTimeout(() => {
        elements.statusMessage.textContent = '';
      }, 3000);
    });
  }
}

/**
 * Show a toast notification
 */
function showToast(message, duration = 3000) {
  // Remove any existing toast
  const existingToast = document.querySelector('.toast');
  if (existingToast) {
    existingToast.remove();
  }
  
  // Create new toast
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.textContent = message;
  
  // Add to document
  document.body.appendChild(toast);
  
  // Show toast
  setTimeout(() => {
    toast.classList.add('show');
  }, 10);
  
  // Hide toast after duration
  setTimeout(() => {
    toast.classList.remove('show');
    
    // Remove from document after animation
    setTimeout(() => {
      toast.remove();
    }, 300);
  }, duration);
}

// Initialize the options page
document.addEventListener('DOMContentLoaded', initialize);
