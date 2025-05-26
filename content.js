/**
 * Content script for Google Maps Business Scraper Chrome Extension
 * 
 * This script is injected into Google Maps pages and handles the extraction
 * of business data, including names and phone numbers, with specific
 * optimizations for Sri Lankan businesses.
 */

// Global state
const state = {
  isExtracting: false,
  extractionSession: null,
  businesses: [],
  progress: {
    current: 0,
    total: 0,
    scrolls: 0
  },
  ui: {
    controlsInjected: false
  },
  config: {
    maxBusinesses: 100,
    scrollDelay: 500,
    maxScrollAttempts: 20,
    extractDetails: true,
    validateSriLankanNumbers: true,
    convertToInternationalFormat: true,
    includeLocalFormat: true,
    identifyNumberType: true
  }
};

// Sri Lankan phone number patterns
const SL_MOBILE_PATTERN = /(?:\+94|0)7[0-2,4-8]\d{7}/;
const SL_LANDLINE_PATTERN = /(?:\+94|0)(?:[1-9][0-9])\d{6}/;
const SL_GENERAL_PATTERN = /(?:\+94|0)\d{9}/;

// Sri Lankan landline area codes with regions
const LANDLINE_REGIONS = {
  '11': 'Colombo',
  '33': 'Gampaha',
  '34': 'Kalutara',
  '81': 'Kandy',
  '66': 'Matale',
  '52': 'Nuwara Eliya',
  '91': 'Galle',
  '41': 'Matara',
  '47': 'Hambantota',
  '21': 'Jaffna/Kilinochchi',
  '23': 'Mannar',
  '24': 'Vavuniya/Mullaitivu',
  '65': 'Batticaloa',
  '63': 'Ampara',
  '26': 'Trincomalee',
  '37': 'Kurunegala',
  '32': 'Puttalam',
  '25': 'Anuradhapura',
  '27': 'Polonnaruwa',
  '55': 'Badulla/Monaragala',
  '45': 'Ratnapura',
  '35': 'Kegalle'
};

/**
 * Initialize the content script
 */
function initialize() {
  console.log('Google Maps Business Scraper: Content script initialized');
  
  // Load configuration from storage
  loadConfiguration().then(() => {
    // Set up message listeners
    setupMessageListeners();
    
    // Check if we're on Google Maps
    if (isGoogleMapsPage()) {
      // Wait for the page to be fully loaded
      waitForGoogleMapsToLoad().then(() => {
        // Inject UI controls
        injectUIControls();
        
        // Set up mutation observer to handle dynamic content
        setupMutationObserver();
      });
    }
  });
}

/**
 * Load configuration from Chrome storage
 */
async function loadConfiguration() {
  return new Promise((resolve) => {
    chrome.storage.sync.get('scraperConfig', (result) => {
      if (result.scraperConfig) {
        state.config = { ...state.config, ...result.scraperConfig };
      }
      resolve();
    });
  });
}

/**
 * Set up message listeners for communication with popup and background script
 */
function setupMessageListeners() {
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    console.log('Content script received message:', message);
    
    switch (message.action) {
      case 'START_EXTRACTION':
        handleStartExtraction(message.payload, sendResponse);
        return true; // Keep the message channel open for async response
        
      case 'STOP_EXTRACTION':
        handleStopExtraction(sendResponse);
        return true;
        
      case 'GET_STATUS':
        sendResponse({
          isExtracting: state.isExtracting,
          progress: state.progress,
          businesses: state.businesses.length
        });
        return false;
        
      case 'CHECK_GOOGLE_MAPS':
        sendResponse({ isGoogleMaps: isGoogleMapsPage() });
        return false;
    }
  });
}

/**
 * Check if the current page is Google Maps
 */
function isGoogleMapsPage() {
  return window.location.href.includes('google.com/maps') || 
         window.location.href.includes('maps.google.com');
}

/**
 * Wait for Google Maps to fully load
 */
function waitForGoogleMapsToLoad() {
  return new Promise((resolve) => {
    // Check if the map is already loaded
    if (document.querySelector('div[role="feed"]') || 
        document.querySelector('div[role="main"]')) {
      resolve();
      return;
    }
    
    // Set up a mutation observer to wait for the map to load
    const observer = new MutationObserver((mutations, obs) => {
      if (document.querySelector('div[role="feed"]') || 
          document.querySelector('div[role="main"]')) {
        obs.disconnect();
        resolve();
      }
    });
    
    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
    
    // Timeout after 10 seconds
    setTimeout(() => {
      observer.disconnect();
      resolve();
    }, 10000);
  });
}

/**
 * Inject UI controls into Google Maps
 */
function injectUIControls() {
  if (state.ui.controlsInjected) return;
  
  // Create control container
  const controlContainer = document.createElement('div');
  controlContainer.id = 'gmbs-controls';
  controlContainer.className = 'gmbs-controls';
  controlContainer.innerHTML = `
    <div class="gmbs-controls-inner">
      <button id="gmbs-extract-btn" class="gmbs-btn gmbs-extract-btn">
        Extract Businesses
      </button>
      <div id="gmbs-progress" class="gmbs-progress" style="display: none;">
        <span id="gmbs-progress-text">Progress: 0/0</span>
        <div class="gmbs-progress-bar">
          <div id="gmbs-progress-bar-inner" class="gmbs-progress-bar-inner" style="width: 0%"></div>
        </div>
      </div>
      <button id="gmbs-stop-btn" class="gmbs-btn gmbs-stop-btn" style="display: none;">
        Stop
      </button>
    </div>
  `;
  
  // Add styles
  const styles = document.createElement('style');
  styles.textContent = `
    .gmbs-controls {
      position: fixed;
      bottom: 20px;
      left: 50%;
      transform: translateX(-50%);
      z-index: 1000;
      background: white;
      border-radius: 8px;
      box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
      padding: 10px 15px;
      display: flex;
      align-items: center;
      font-family: Roboto, Arial, sans-serif;
    }
    
    .gmbs-controls-inner {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    
    .gmbs-btn {
      background: #1a73e8;
      color: white;
      border: none;
      border-radius: 4px;
      padding: 8px 16px;
      font-size: 14px;
      cursor: pointer;
      font-weight: 500;
      transition: background-color 0.2s;
    }
    
    .gmbs-btn:hover {
      background: #1765cc;
    }
    
    .gmbs-stop-btn {
      background: #ea4335;
    }
    
    .gmbs-stop-btn:hover {
      background: #d33426;
    }
    
    .gmbs-progress {
      display: flex;
      flex-direction: column;
      min-width: 150px;
    }
    
    .gmbs-progress-text {
      font-size: 14px;
      margin-bottom: 4px;
    }
    
    .gmbs-progress-bar {
      height: 6px;
      background: #e0e0e0;
      border-radius: 3px;
      overflow: hidden;
    }
    
    .gmbs-progress-bar-inner {
      height: 100%;
      background: #1a73e8;
      transition: width 0.3s;
    }
  `;
  
  // Append to document
  document.body.appendChild(styles);
  document.body.appendChild(controlContainer);
  
  // Add event listeners
  document.getElementById('gmbs-extract-btn').addEventListener('click', () => {
    startExtraction();
  });
  
  document.getElementById('gmbs-stop-btn').addEventListener('click', () => {
    stopExtraction();
  });
  
  state.ui.controlsInjected = true;
  console.log('Google Maps Business Scraper: UI controls injected');
}

/**
 * Set up mutation observer to handle dynamic content changes
 */
function setupMutationObserver() {
  const observer = new MutationObserver((mutations) => {
    // If we're extracting and in the results view, check for new results
    if (state.isExtracting && isResultsView()) {
      // This will be handled by the extraction process
    }
    
    // If we're on a business details page and extraction is active
    if (state.isExtracting && isBusinessDetailsPage() && state.config.extractDetails) {
      // This will be handled by the extraction process
    }
  });
  
  observer.observe(document.body, {
    childList: true,
    subtree: true
  });
}

/**
 * Check if we're in the results view
 */
function isResultsView() {
  return !!document.querySelector('div[role="feed"]');
}

/**
 * Check if we're on a business details page
 */
function isBusinessDetailsPage() {
  // Check for business details panel
  return !!document.querySelector('button[data-item-id="phone"]') || 
         !!document.querySelector('button[jsaction*="pane.rating.category"]');
}

/**
 * Handle start extraction message
 */
function handleStartExtraction(payload, sendResponse) {
  if (state.isExtracting) {
    sendResponse({ success: false, error: 'Extraction already in progress' });
    return;
  }
  
  // Start extraction with the provided parameters
  startExtraction(payload).then((result) => {
    sendResponse({ success: true, sessionId: result.sessionId });
  }).catch((error) => {
    sendResponse({ success: false, error: error.message });
  });
}

/**
 * Handle stop extraction message
 */
function handleStopExtraction(sendResponse) {
  stopExtraction();
  sendResponse({ success: true });
}

/**
 * Start the extraction process
 */
async function startExtraction(params = {}) {
  if (state.isExtracting) {
    throw new Error('Extraction already in progress');
  }
  
  console.log('Starting extraction with params:', params);
  
  // Initialize extraction session
  const sessionId = 'session-' + Date.now();
  state.extractionSession = {
    id: sessionId,
    query: params.query || '',
    location: params.location || '',
    radius: params.radius || 5,
    startTime: new Date().toISOString(),
    endTime: null,
    status: 'in_progress',
    businessesFound: 0,
    phoneNumbersFound: 0,
    error: null
  };
  
  // Reset state
  state.isExtracting = true;
  state.businesses = [];
  state.progress = {
    current: 0,
    total: 0,
    scrolls: 0
  };
  
  // Update UI
  updateExtractionUI(true);
  
  try {
    // If search query and location are provided, perform search
    if (params.query && params.location) {
      await performSearch(params.query, params.location);
    }
    
    // Wait for results to load
    await waitForResults();
    
    // Extract businesses
    await extractBusinesses();
    
    // Complete extraction
    completeExtraction();
    
    return { sessionId };
  } catch (error) {
    failExtraction(error);
    throw error;
  }
}

/**
 * Perform a search on Google Maps
 */
async function performSearch(query, location) {
  console.log(`Performing search: ${query} in ${location}`);
  
  // Get the search box
  const searchBox = document.querySelector('input[name="q"]');
  if (!searchBox) {
    throw new Error('Search box not found');
  }
  
  // Clear and focus the search box
  searchBox.focus();
  searchBox.value = '';
  
  // Type the search query
  await typeWithDelay(searchBox, `${query} in ${location}`);
  
  // Press Enter to search
  searchBox.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true }));
  
  // Wait for search to complete
  return new Promise((resolve) => {
    setTimeout(resolve, 2000);
  });
}

/**
 * Type text with a delay to simulate human typing
 */
async function typeWithDelay(element, text) {
  for (let i = 0; i < text.length; i++) {
    element.value += text[i];
    element.dispatchEvent(new Event('input', { bubbles: true }));
    
    // Random delay between keystrokes
    await new Promise(resolve => setTimeout(resolve, 50 + Math.random() * 100));
  }
}

/**
 * Wait for results to load
 */
async function waitForResults() {
  return new Promise((resolve, reject) => {
    let attempts = 0;
    const maxAttempts = 10;
    
    const checkResults = () => {
      if (isResultsView()) {
        resolve();
        return;
      }
      
      attempts++;
      if (attempts >= maxAttempts) {
        reject(new Error('Results not found after multiple attempts'));
        return;
      }
      
      setTimeout(checkResults, 1000);
    };
    
    checkResults();
  });
}

/**
 * Extract businesses from the results
 */
async function extractBusinesses() {
  if (!isResultsView()) {
    throw new Error('Not in results view');
  }
  
  console.log('Extracting businesses from results');
  
  // Get the results container
  const resultsContainer = document.querySelector('div[role="feed"]');
  if (!resultsContainer) {
    throw new Error('Results container not found');
  }
  
  // Estimate total businesses (this is approximate)
  state.progress.total = Math.min(
    state.config.maxBusinesses,
    estimateTotalBusinesses()
  );
  updateProgressUI();
  
  // Extract visible businesses
  let lastBusinessCount = 0;
  let scrollAttempts = 0;
  
  while (state.isExtracting && 
         state.businesses.length < state.config.maxBusinesses && 
         scrollAttempts < state.config.maxScrollAttempts) {
    
    // Extract visible business items
    await extractVisibleBusinesses();
    
    // Update progress
    updateProgressUI();
    
    // Check if we found new businesses
    if (state.businesses.length === lastBusinessCount) {
      scrollAttempts++;
    } else {
      scrollAttempts = 0;
      lastBusinessCount = state.businesses.length;
    }
    
    // Scroll to load more results
    await scrollResultsContainer();
    
    // Wait for new results to load
    await new Promise(resolve => setTimeout(resolve, state.config.scrollDelay));
  }
  
  console.log(`Extraction complete. Found ${state.businesses.length} businesses.`);
}

/**
 * Estimate the total number of businesses in the results
 */
function estimateTotalBusinesses() {
  // Try to find a count in the results header
  const resultsHeader = document.querySelector('.section-result-header');
  if (resultsHeader) {
    const countText = resultsHeader.textContent;
    const countMatch = countText.match(/(\d+)/);
    if (countMatch) {
      return parseInt(countMatch[1], 10);
    }
  }
  
  // Fallback: estimate based on visible results
  const visibleResults = document.querySelectorAll('div[role="feed"] > div');
  return Math.max(visibleResults.length * 2, 20); // Assume at least twice as many as visible
}

/**
 * Extract visible businesses from the results
 */
async function extractVisibleBusinesses() {
  // Get all business items in the feed
  const businessItems = document.querySelectorAll('div[role="feed"] > div');
  
  for (const item of businessItems) {
    // Skip if we've reached the maximum
    if (state.businesses.length >= state.config.maxBusinesses || !state.isExtracting) {
      break;
    }
    
    // Skip if already processed (check for a marker)
    if (item.dataset.gmbsProcessed === 'true') {
      continue;
    }
    
    // Mark as processed
    item.dataset.gmbsProcessed = 'true';
    
    try {
      // Check if this is a business result
      const nameElement = item.querySelector('h3, .fontHeadlineSmall');
      if (!nameElement) continue;
      
      // Extract basic business info
      const businessName = nameElement.textContent.trim();
      
      // Check if we already have this business
      if (state.businesses.some(b => b.name === businessName)) {
        continue;
      }
      
      console.log(`Extracting business: ${businessName}`);
      
      // Create business object
      const business = {
        name: businessName,
        phoneNumbers: [],
        address: '',
        category: '',
        rating: null,
        reviewsCount: null,
        website: '',
        location: null,
        extractedAt: new Date().toISOString()
      };
      
      // Extract category if available
      const categoryElement = item.querySelector('.fontBodyMedium span:first-child');
      if (categoryElement) {
        business.category = categoryElement.textContent.trim();
      }
      
      // Extract rating if available
      const ratingElement = item.querySelector('span[aria-hidden="true"][role="img"]');
      if (ratingElement) {
        const ratingText = ratingElement.getAttribute('aria-label');
        if (ratingText) {
          const ratingMatch = ratingText.match(/(\d+(\.\d+)?)/);
          if (ratingMatch) {
            business.rating = parseFloa
(Content truncated due to size limit. Use line ranges to read in chunks)