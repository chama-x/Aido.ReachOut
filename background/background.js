/**
 * Background script for Google Maps Business Scraper Chrome Extension
 * 
 * This script runs in the background and coordinates between the popup UI
 * and content script, managing data persistence and extraction sessions.
 */

// Global state
const state = {
  extractionSessions: {},
  currentSession: null,
  isExtracting: false
};

/**
 * Initialize the background script
 */
function initialize() {
  console.log('Google Maps Business Scraper: Background script initialized');
  
  // Set up message listeners
  setupMessageListeners();
}

/**
 * Set up message listeners
 */
function setupMessageListeners() {
  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    console.log('Background script received message:', message);
    
    switch (message.action) {
      case 'EXTRACTION_PROGRESS':
        handleExtractionProgress(message.payload, sender, sendResponse);
        return false;
        
      case 'EXTRACTION_COMPLETE':
        handleExtractionComplete(message.payload, sender, sendResponse);
        return false;
        
      case 'GET_EXTRACTION_STATUS':
        handleGetExtractionStatus(sendResponse);
        return false;
        
      case 'GET_RESULTS':
        handleGetResults(message.payload, sendResponse);
        return true; // Keep the message channel open for async response
        
      case 'EXPORT_RESULTS':
        handleExportResults(message.payload, sendResponse);
        return true; // Keep the message channel open for async response
    }
  });
}

/**
 * Handle extraction progress message
 */
function handleExtractionProgress(payload, sender, sendResponse) {
  const { sessionId, progress, businessesFound, phoneNumbersFound } = payload;
  
  // Update session data
  if (state.extractionSessions[sessionId]) {
    state.extractionSessions[sessionId].progress = progress;
    state.extractionSessions[sessionId].businessesFound = businessesFound;
    state.extractionSessions[sessionId].phoneNumbersFound = phoneNumbersFound;
  }
  
  // Forward progress to popup if open
  chrome.runtime.sendMessage({
    action: 'EXTRACTION_PROGRESS',
    payload
  });
}

/**
 * Handle extraction complete message
 */
function handleExtractionComplete(payload, sender, sendResponse) {
  const { sessionId, status, businessesFound, phoneNumbersFound, results, error } = payload;
  
  // Update session data
  if (state.extractionSessions[sessionId]) {
    state.extractionSessions[sessionId].status = status;
    state.extractionSessions[sessionId].businessesFound = businessesFound;
    state.extractionSessions[sessionId].phoneNumbersFound = phoneNumbersFound;
    state.extractionSessions[sessionId].results = results;
    state.extractionSessions[sessionId].error = error;
    state.extractionSessions[sessionId].completedAt = new Date().toISOString();
  }
  
  // Update global state
  if (state.currentSession === sessionId) {
    state.isExtracting = false;
    state.currentSession = null;
  }
  
  // Forward completion to popup if open
  chrome.runtime.sendMessage({
    action: 'EXTRACTION_COMPLETE',
    payload
  });
}

/**
 * Handle get extraction status message
 */
function handleGetExtractionStatus(sendResponse) {
  if (state.isExtracting && state.currentSession) {
    const session = state.extractionSessions[state.currentSession];
    
    sendResponse({
      isExtracting: true,
      sessionId: state.currentSession,
      progress: session ? session.progress : { current: 0, total: 0 }
    });
  } else {
    sendResponse({
      isExtracting: false
    });
  }
}

/**
 * Handle get results message
 */
function handleGetResults(payload, sendResponse) {
  const { sessionId } = payload;
  
  if (!sessionId) {
    // If no session ID provided, return the most recent session
    const sessions = Object.values(state.extractionSessions)
      .filter(session => session.status === 'completed')
      .sort((a, b) => new Date(b.completedAt) - new Date(a.completedAt));
    
    if (sessions.length > 0) {
      sendResponse({
        success: true,
        results: sessions[0].results
      });
    } else {
      sendResponse({
        success: false,
        error: 'No completed extraction sessions found'
      });
    }
    return;
  }
  
  // Return results for the specified session
  if (state.extractionSessions[sessionId]) {
    sendResponse({
      success: true,
      results: state.extractionSessions[sessionId].results
    });
  } else {
    sendResponse({
      success: false,
      error: 'Session not found'
    });
  }
}

/**
 * Handle export results message
 */
function handleExportResults(payload, sendResponse) {
  const { format, sessionId } = payload;
  
  // Get results
  let results;
  
  if (sessionId && state.extractionSessions[sessionId]) {
    results = state.extractionSessions[sessionId].results;
  } else {
    // If no session ID provided, use the most recent session
    const sessions = Object.values(state.extractionSessions)
      .filter(session => session.status === 'completed')
      .sort((a, b) => new Date(b.completedAt) - new Date(a.completedAt));
    
    if (sessions.length > 0) {
      results = sessions[0].results;
    }
  }
  
  if (!results || results.length === 0) {
    sendResponse({
      success: false,
      error: 'No results to export'
    });
    return;
  }
  
  // Format data
  let data;
  let mimeType;
  let fileExtension;
  
  if (format === 'csv') {
    data = formatAsCSV(results);
    mimeType = 'text/csv';
    fileExtension = 'csv';
  } else {
    data = JSON.stringify(results, null, 2);
    mimeType = 'application/json';
    fileExtension = 'json';
  }
  
  // Generate filename
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-').substring(0, 19);
  const filename = `sri_lanka_businesses_${timestamp}.${fileExtension}`;
  
  // Create blob
  const blob = new Blob([data], { type: mimeType });
  
  // Create download URL
  const url = URL.createObjectURL(blob);
  
  // Download file
  chrome.downloads.download({
    url: url,
    filename: filename,
    saveAs: true
  }, (downloadId) => {
    // Revoke URL after download starts
    URL.revokeObjectURL(url);
    
    if (chrome.runtime.lastError) {
      sendResponse({
        success: false,
        error: chrome.runtime.lastError.message
      });
    } else {
      sendResponse({
        success: true,
        downloadId
      });
    }
  });
}

/**
 * Format results as CSV
 */
function formatAsCSV(results) {
  // Define headers
  const headers = [
    'Business Name',
    'Phone Number',
    'Local Format',
    'Is Mobile',
    'Region',
    'Category',
    'Rating',
    'Reviews Count',
    'Website',
    'Address',
    'Latitude',
    'Longitude'
  ];
  
  // Start with headers
  let csv = headers.join(',') + '\n';
  
  // Add each business
  results.forEach(business => {
    // If business has no phone numbers, add a row with just the business info
    if (!business.phoneNumbers || business.phoneNumbers.length === 0) {
      const row = [
        escapeCsvValue(business.name),
        '',
        '',
        '',
        '',
        escapeCsvValue(business.category || ''),
        business.rating || '',
        business.reviewsCount || '',
        escapeCsvValue(business.website || ''),
        escapeCsvValue(business.address || ''),
        business.location ? business.location.latitude : '',
        business.location ? business.location.longitude : ''
      ];
      
      csv += row.join(',') + '\n';
    } else {
      // Add a row for each phone number
      business.phoneNumbers.forEach(phone => {
        const phoneObj = typeof phone === 'string' ? { number: phone } : phone;
        
        const row = [
          escapeCsvValue(business.name),
          escapeCsvValue(phoneObj.number || ''),
          escapeCsvValue(phoneObj.localFormat || ''),
          phoneObj.isMobile !== undefined ? phoneObj.isMobile : '',
          escapeCsvValue(phoneObj.region || ''),
          escapeCsvValue(business.category || ''),
          business.rating || '',
          business.reviewsCount || '',
          escapeCsvValue(business.website || ''),
          escapeCsvValue(business.address || ''),
          business.location ? business.location.latitude : '',
          business.location ? business.location.longitude : ''
        ];
        
        csv += row.join(',') + '\n';
      });
    }
  });
  
  return csv;
}

/**
 * Escape a value for CSV
 */
function escapeCsvValue(value) {
  if (value === null || value === undefined) {
    return '';
  }
  
  const stringValue = String(value);
  
  // If the value contains a comma, quote, or newline, wrap it in quotes
  if (stringValue.includes(',') || stringValue.includes('"') || stringValue.includes('\n')) {
    // Double up any quotes
    return '"' + stringValue.replace(/"/g, '""') + '"';
  }
  
  return stringValue;
}

// Initialize the background script
initialize();
