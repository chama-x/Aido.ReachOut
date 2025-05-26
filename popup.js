/**
 * Popup script for Google Maps Business Scraper Chrome Extension
 * 
 * This script handles the popup UI interactions, communicates with the
 * background script, and manages the extraction process from the popup.
 */

// Global state
const state = {
  isExtracting: false,
  currentTab: null,
  isGoogleMaps: false,
  results: {
    businesses: [],
    phoneNumbers: 0
  },
  extraction: {
    sessionId: null,
    progress: {
      current: 0,
      total: 0
    }
  }
};

// DOM Elements
const elements = {
  // Form elements
  locationSelect: document.getElementById('location'),
  customLocation: document.getElementById('custom-location'),
  radiusSelect: document.getElementById('radius'),
  queryInput: document.getElementById('query'),
  
  // Action buttons
  extractCurrentBtn: document.getElementById('extract-current-view'),
  searchExtractBtn: document.getElementById('search-and-extract'),
  stopBtn: document.createElement('button'),
  
  // Results elements
  businessCount: document.getElementById('business-count'),
  phoneCount: document.getElementById('phone-count'),
  resultsPreview: document.getElementById('results-preview'),
  
  // Export buttons
  exportCsvBtn: document.getElementById('export-csv'),
  exportJsonBtn: document.getElementById('export-json'),
  copyResultsBtn: document.getElementById('copy-results'),
  
  // Footer elements
  settingsLink: document.getElementById('open-settings'),
  helpLink: document.getElementById('open-help'),
  statusMessage: document.getElementById('status-message'),
  
  // Progress elements
  progressContainer: document.createElement('div'),
  progressBar: document.createElement('div'),
  progressBarInner: document.createElement('div'),
  progressText: document.createElement('div')
};

/**
 * Initialize the popup
 */
function initialize() {
  console.log('Initializing popup');
  
  // Set up event listeners
  setupEventListeners();
  
  // Create and add progress elements
  setupProgressElements();
  
  // Get current tab
  getCurrentTab().then(tab => {
    state.currentTab = tab;
    
    // Check if we're on Google Maps
    checkIfGoogleMaps(tab);
    
    // Load saved settings
    loadSettings();
    
    // Check if extraction is in progress
    checkExtractionStatus();
  });
}

/**
 * Set up event listeners
 */
function setupEventListeners() {
  // Location select change
  elements.locationSelect.addEventListener('change', () => {
    if (elements.locationSelect.value === 'custom') {
      elements.customLocation.style.display = 'block';
    } else {
      elements.customLocation.style.display = 'none';
    }
  });
  
  // Extract from current view button
  elements.extractCurrentBtn.addEventListener('click', () => {
    if (!state.isGoogleMaps) {
      showToast('Please navigate to Google Maps first');
      return;
    }
    
    startExtraction(false);
  });
  
  // Search and extract button
  elements.searchExtractBtn.addEventListener('click', () => {
    startExtraction(true);
  });
  
  // Stop button
  elements.stopBtn.addEventListener('click', stopExtraction);
  
  // Export buttons
  elements.exportCsvBtn.addEventListener('click', () => exportResults('csv'));
  elements.exportJsonBtn.addEventListener('click', () => exportResults('json'));
  elements.copyResultsBtn.addEventListener('click', copyResultsToClipboard);
  
  // Settings link
  elements.settingsLink.addEventListener('click', openSettings);
  
  // Help link
  elements.helpLink.addEventListener('click', openHelp);
}

/**
 * Set up progress elements
 */
function setupProgressElements() {
  // Create stop button
  elements.stopBtn.className = 'btn stop-button';
  elements.stopBtn.textContent = 'Stop Extraction';
  
  // Create progress container
  elements.progressContainer.className = 'progress-container';
  
  // Create progress bar
  elements.progressBar.className = 'progress-bar';
  elements.progressBarInner.className = 'progress-bar-inner';
  elements.progressBar.appendChild(elements.progressBarInner);
  
  // Create progress text
  elements.progressText.className = 'progress-text';
  elements.progressText.textContent = 'Extracting...';
  
  // Add to container
  elements.progressContainer.appendChild(elements.progressBar);
  elements.progressContainer.appendChild(elements.progressText);
  
  // Add to extraction actions section
  const extractionActions = document.querySelector('.extraction-actions');
  extractionActions.appendChild(elements.stopBtn);
  extractionActions.appendChild(elements.progressContainer);
}

/**
 * Get the current tab
 */
async function getCurrentTab() {
  return new Promise((resolve) => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      resolve(tabs[0]);
    });
  });
}

/**
 * Check if the current tab is Google Maps
 */
function checkIfGoogleMaps(tab) {
  const isGoogleMaps = tab.url.includes('google.com/maps') || 
                       tab.url.includes('maps.google.com');
  
  state.isGoogleMaps = isGoogleMaps;
  
  if (!isGoogleMaps) {
    elements.statusMessage.textContent = 'Not on Google Maps';
    elements.extractCurrentBtn.disabled = true;
  } else {
    elements.statusMessage.textContent = 'Ready to extract';
    elements.extractCurrentBtn.disabled = false;
  }
}

/**
 * Load saved settings
 */
function loadSettings() {
  chrome.storage.sync.get(['scraperConfig', 'lastLocation', 'lastRadius', 'lastQuery'], (result) => {
    if (result.lastLocation) {
      // Check if it's in the list
      const option = Array.from(elements.locationSelect.options).find(
        opt => opt.value === result.lastLocation
      );
      
      if (option) {
        elements.locationSelect.value = result.lastLocation;
      } else if (result.lastLocation !== 'custom') {
        // Add it as an option
        const newOption = document.createElement('option');
        newOption.value = result.lastLocation;
        newOption.textContent = result.lastLocation;
        elements.locationSelect.insertBefore(
          newOption, 
          elements.locationSelect.querySelector('option[value="custom"]')
        );
        elements.locationSelect.value = result.lastLocation;
      } else {
        // Custom location
        elements.locationSelect.value = 'custom';
        elements.customLocation.style.display = 'block';
        elements.customLocation.value = result.lastCustomLocation || '';
      }
    }
    
    if (result.lastRadius) {
      elements.radiusSelect.value = result.lastRadius;
    }
    
    if (result.lastQuery) {
      elements.queryInput.value = result.lastQuery;
    }
  });
}

/**
 * Check if extraction is in progress
 */
function checkExtractionStatus() {
  chrome.runtime.sendMessage({ action: 'GET_EXTRACTION_STATUS' }, (response) => {
    if (response && response.isExtracting) {
      state.isExtracting = true;
      state.extraction.sessionId = response.sessionId;
      state.extraction.progress = response.progress;
      
      updateExtractionUI(true);
      updateProgressUI(response.progress.current, response.progress.total);
    }
  });
}

/**
 * Start the extraction process
 */
function startExtraction(withSearch) {
  // Get extraction parameters
  const location = elements.locationSelect.value === 'custom' 
    ? elements.customLocation.value 
    : elements.locationSelect.value;
    
  const radius = parseInt(elements.radiusSelect.value, 10);
  const query = elements.queryInput.value;
  
  // Validate inputs
  if (withSearch && (!location || !query)) {
    showToast('Please enter both location and search query');
    return;
  }
  
  // Save settings
  saveSettings(location, radius, query);
  
  // Update UI
  state.isExtracting = true;
  updateExtractionUI(true);
  
  // Send message to start extraction
  chrome.tabs.sendMessage(state.currentTab.id, {
    action: 'START_EXTRACTION',
    payload: {
      withSearch,
      location,
      radius,
      query
    }
  }, (response) => {
    if (!response || !response.success) {
      showToast(response?.error || 'Failed to start extraction');
      state.isExtracting = false;
      updateExtractionUI(false);
      return;
    }
    
    state.extraction.sessionId = response.sessionId;
    elements.statusMessage.textContent = 'Extraction in progress...';
  });
  
  // Set up progress listener
  setupProgressListener();
}

/**
 * Save settings
 */
function saveSettings(location, radius, query) {
  const settings = {
    lastLocation: location,
    lastRadius: radius,
    lastQuery: query
  };
  
  if (location === 'custom') {
    settings.lastCustomLocation = elements.customLocation.value;
  }
  
  chrome.storage.sync.set(settings);
}

/**
 * Set up progress listener
 */
function setupProgressListener() {
  // Remove any existing listener
  chrome.runtime.onMessage.removeListener(handleProgressUpdate);
  
  // Add listener
  chrome.runtime.onMessage.addListener(handleProgressUpdate);
}

/**
 * Handle progress update message
 */
function handleProgressUpdate(message, sender, sendResponse) {
  if (message.action === 'EXTRACTION_PROGRESS') {
    const { progress, businessesFound, phoneNumbersFound } = message.payload;
    
    // Update progress UI
    updateProgressUI(progress.current, progress.total);
    
    // Update results count
    updateResultsCount(businessesFound, phoneNumbersFound);
  } else if (message.action === 'EXTRACTION_COMPLETE') {
    const { status, businessesFound, phoneNumbersFound, results, error } = message.payload;
    
    // Update state
    state.isExtracting = false;
    state.results.businesses = results || [];
    state.results.phoneNumbers = phoneNumbersFound;
    
    // Update UI
    updateExtractionUI(false);
    updateResultsCount(businessesFound, phoneNumbersFound);
    updateResultsPreview(results);
    
    // Enable export buttons if we have results
    const hasResults = businessesFound > 0;
    elements.exportCsvBtn.disabled = !hasResults;
    elements.exportJsonBtn.disabled = !hasResults;
    elements.copyResultsBtn.disabled = !hasResults;
    
    // Show status message
    if (status === 'completed') {
      elements.statusMessage.textContent = 'Extraction completed';
    } else if (status === 'stopped') {
      elements.statusMessage.textContent = 'Extraction stopped';
    } else if (status === 'error') {
      elements.statusMessage.textContent = `Error: ${error || 'Unknown error'}`;
    }
    
    // Remove progress listener
    chrome.runtime.onMessage.removeListener(handleProgressUpdate);
  }
  
  // Always return false to close the message channel
  return false;
}

/**
 * Update the extraction UI
 */
function updateExtractionUI(isExtracting) {
  const container = document.querySelector('.container');
  
  if (isExtracting) {
    container.classList.add('extracting');
  } else {
    container.classList.remove('extracting');
  }
}

/**
 * Update the progress UI
 */
function updateProgressUI(current, total) {
  const percentage = total > 0 ? Math.min(100, Math.round((current / total) * 100)) : 0;
  
  elements.progressBarInner.style.width = `${percentage}%`;
  elements.progressText.textContent = `Extracting: ${current}/${total} (${percentage}%)`;
}

/**
 * Update the results count
 */
function updateResultsCount(businesses, phones) {
  elements.businessCount.textContent = businesses;
  elements.phoneCount.textContent = phones;
}

/**
 * Update the results preview
 */
function updateResultsPreview(results) {
  if (!results || results.length === 0) {
    elements.resultsPreview.innerHTML = '<p class="no-results">No results yet</p>';
    return;
  }
  
  // Clear previous results
  elements.resultsPreview.innerHTML = '';
  
  // Add up to 5 results as preview
  const previewResults = results.slice(0, 5);
  
  previewResults.forEach(business => {
    const businessElement = document.createElement('div');
    businessElement.className = 'business-item';
    
    const nameElement = document.createElement('div');
    nameElement.className = 'business-name';
    nameElement.textContent = business.name;
    
    businessElement.appendChild(nameElement);
    
    // Add phone numbers
    business.phoneNumbers.forEach(phone => {
      const phoneElement = document.createElement('div');
      phoneElement.className = 'business-phone';
      phoneElement.textContent = phone.number || phone;
      businessElement.appendChild(phoneElement);
    });
    
    elements.resultsPreview.appendChild(businessElement);
  });
  
  // Add message if there are more results
  if (results.length > 5) {
    const moreElement = document.createElement('div');
    moreElement.className = 'more-results';
    moreElement.textContent = `...and ${results.length - 5} more businesses`;
    elements.resultsPreview.appendChild(moreElement);
  }
}

/**
 * Stop the extraction process
 */
function stopExtraction() {
  if (!state.isExtracting) return;
  
  chrome.tabs.sendMessage(state.currentTab.id, {
    action: 'STOP_EXTRACTION'
  });
  
  elements.statusMessage.textContent = 'Stopping extraction...';
}

/**
 * Export results
 */
function exportResults(format) {
  chrome.runtime.sendMessage({
    action: 'EXPORT_RESULTS',
    payload: {
      format,
      sessionId: state.extraction.sessionId
    }
  }, (response) => {
    if (response && response.success) {
      showToast(`Exported as ${format.toUpperCase()}`);
    } else {
      showToast('Export failed');
    }
  });
}

/**
 * Copy results to clipboard
 */
function copyResultsToClipboard() {
  chrome.runtime.sendMessage({
    action: 'GET_RESULTS',
    payload: {
      sessionId: state.extraction.sessionId
    }
  }, (response) => {
    if (response && response.results) {
      // Format results as text
      const text = formatResultsAsText(response.results);
      
      // Copy to clipboard
      navigator.clipboard.writeText(text).then(() => {
        showToast('Results copied to clipboard');
      }).catch(() => {
        showToast('Failed to copy results');
      });
    } else {
      showToast('No results to copy');
    }
  });
}

/**
 * Format results as text
 */
function formatResultsAsText(results) {
  let text = 'Business Name,Phone Number\n';
  
  results.forEach(business => {
    const phones = business.phoneNumbers.map(p => p.number || p).join('; ');
    text += `${business.name},${phones}\n`;
  });
  
  return text;
}

/**
 * Open settings page
 */
function openSettings() {
  chrome.runtime.openOptionsPage();
}

/**
 * Open help page
 */
function openHelp() {
  chrome.tabs.create({
    url: chrome.runtime.getURL('help/help.html')
  });
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

// Initialize the popup
document.addEventListener('DOMContentLoaded', initialize);
