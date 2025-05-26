# Chrome Extension Architecture for Google Maps Business Scraper

## Overview

This document outlines the architecture and user flows for the Google Maps Business Scraper Chrome extension. The extension will be 100% browser automation based, designed to extract business names and phone numbers from Google Maps with a focus on Sri Lankan businesses.

## Architecture Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Chrome Extension                         │
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐  │
│  │             │    │             │    │                 │  │
│  │  Popup UI   │◄──►│ Background  │◄──►│  Content Script │  │
│  │             │    │   Script    │    │                 │  │
│  └─────────────┘    └─────────────┘    └─────────────────┘  │
│        ▲                   ▲                   ▲            │
│        │                   │                   │            │
│        ▼                   ▼                   ▼            │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐  │
│  │             │    │             │    │                 │  │
│  │ Options UI  │    │   Storage   │    │  DOM Utilities  │  │
│  │             │    │             │    │                 │  │
│  └─────────────┘    └─────────────┘    └─────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1. Content Script

The content script is the core component that interacts directly with Google Maps pages.

**Responsibilities:**
- Detect when user is on Google Maps
- Inject extraction controls into the Google Maps UI
- Perform DOM manipulation to extract business data
- Handle pagination/scrolling to load more results
- Extract business details from business cards and detail pages
- Validate and format phone numbers according to Sri Lankan standards
- Send extracted data to background script

**Technical Implementation:**
- Runs in the context of Google Maps pages
- Uses MutationObserver to detect dynamic content changes
- Implements extraction algorithms for different Google Maps UI states
- Contains Sri Lanka-specific validation logic for phone numbers
- Uses message passing to communicate with background script

### 2. Background Script

The background script serves as the central coordinator for the extension.

**Responsibilities:**
- Manage extension state across browser sessions
- Coordinate between popup UI and content script
- Store and retrieve configuration settings
- Handle data persistence
- Manage extraction sessions
- Process and aggregate extracted data

**Technical Implementation:**
- Persistent background service worker (Manifest V3)
- Implements message handlers for communication
- Uses Chrome Storage API for data persistence
- Maintains extraction state and statistics
- Handles error recovery and session management

### 3. Popup UI

The popup UI provides the main user interface for controlling the extension.

**Responsibilities:**
- Display extraction controls and options
- Show current extraction status and statistics
- Provide search configuration options
- Display extracted data preview
- Offer export functionality
- Provide quick access to common actions

**Technical Implementation:**
- HTML/CSS/JavaScript popup
- Responsive design for various screen sizes
- Uses message passing to communicate with background script
- Implements data visualization for extraction statistics
- Provides export functionality for CSV and JSON formats

### 4. Options UI

The options UI allows for detailed configuration of the extension.

**Responsibilities:**
- Provide advanced configuration settings
- Allow customization of extraction parameters
- Manage saved search templates for Sri Lankan locations
- Configure phone number validation rules
- Set user preferences

**Technical Implementation:**
- HTML/CSS/JavaScript options page
- Form-based configuration interface
- Uses Chrome Storage API for settings persistence
- Implements validation for configuration values
- Provides import/export of configuration settings

### 5. Storage Module

The storage module handles data persistence across browser sessions.

**Responsibilities:**
- Store extraction results
- Save user configurations
- Maintain extraction history
- Store Sri Lankan location data
- Persist extraction templates

**Technical Implementation:**
- Uses Chrome Storage API (sync and local)
- Implements data compression for large datasets
- Handles storage quota management
- Provides data migration for version updates

### 6. DOM Utilities

The DOM utilities module provides helper functions for interacting with the Google Maps DOM.

**Responsibilities:**
- Locate and extract business elements
- Parse business details from various UI components
- Handle different Google Maps UI states
- Provide resilient selectors for UI elements
- Simulate user interactions (scrolling, clicking)

**Technical Implementation:**
- Collection of utility functions for DOM manipulation
- Implements resilient selectors with fallbacks
- Contains parsing logic for different data formats
- Handles internationalization and character encoding

## Data Flow

1. **Initialization Flow:**
   - User installs extension
   - Background script initializes and loads default settings
   - When user navigates to Google Maps, content script is injected
   - Content script registers with background script
   - UI controls are injected into Google Maps

2. **Extraction Flow:**
   - User configures extraction parameters in popup
   - Popup sends configuration to background script
   - Background script initializes extraction session
   - Background script sends extraction command to content script
   - Content script begins extraction process
   - Content script sends extracted data to background script in batches
   - Background script processes and stores data
   - Background script updates popup with progress
   - When extraction completes, background script notifies popup
   - Popup displays results summary and export options

3. **Export Flow:**
   - User selects export format in popup
   - Popup requests data from background script
   - Background script retrieves and formats data
   - Popup generates export file and triggers download
   - Export status is reported to user

## User Flows

### 1. Extract from Current View

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│          │     │          │     │          │     │          │
│  Browse  │────►│  Open    │────►│ Configure│────►│  Start   │
│Google Maps│     │  Popup  │     │ Settings │     │Extraction│
│          │     │          │     │          │     │          │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
                                                        │
                                                        ▼
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│          │     │          │     │          │     │          │
│  Export  │◄────│  Review  │◄────│ Progress │◄────│ Automatic│
│  Results │     │  Results │     │ Indicator│     │Extraction│
│          │     │          │     │          │     │          │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
```

**Steps:**
1. User navigates to Google Maps and searches for businesses
2. User clicks extension icon to open popup
3. User configures extraction settings or uses defaults
4. User clicks "Extract from Current View" button
5. Extension shows progress indicator
6. Content script automatically extracts data from visible results
7. Content script scrolls to load more results if needed
8. When complete, popup shows results summary
9. User reviews results in popup preview
10. User exports data in desired format

### 2. Custom Search and Extract

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│          │     │          │     │          │     │          │
│  Open    │────►│  Enter   │────►│ Configure│────►│  Start   │
│  Popup   │     │  Search  │     │ Settings │     │Extraction│
│          │     │          │     │          │     │          │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
                                                        │
                                                        ▼
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│          │     │          │     │          │     │          │
│  Export  │◄────│  Review  │◄────│ Progress │◄────│ Automatic│
│  Results │     │  Results │     │ Indicator│     │ Search & │
│          │     │          │     │          │     │Extraction│
└──────────┘     └──────────┘     └──────────┘     └──────────┘
```

**Steps:**
1. User clicks extension icon to open popup
2. User enters search query and location (e.g., "restaurants in Colombo")
3. User configures extraction settings
4. User clicks "Search and Extract" button
5. Extension navigates to or updates Google Maps with search query
6. Extension shows progress indicator
7. Content script automatically extracts data from search results
8. Content script scrolls to load more results if needed
9. When complete, popup shows results summary
10. User reviews results in popup preview
11. User exports data in desired format

### 3. Extract Business Details

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│          │     │          │     │          │     │          │
│  Browse  │────►│  View    │────►│  Click   │────►│ Automatic│
│Google Maps│     │ Business │     │Extension│     │Extraction│
│          │     │  Details │     │  Button  │     │          │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
                                                        │
                                                        ▼
┌──────────┐     ┌──────────┐
│          │     │          │
│  Export  │◄────│  Review  │
│  Results │     │  Results │
│          │     │          │
└──────────┘     └──────────┘
```

**Steps:**
1. User navigates to Google Maps and views a business details page
2. User clicks extension button injected into the business details UI
3. Content script automatically extracts detailed business information
4. Popup shows extracted data
5. User exports data in desired format

## UI Design

### Popup UI Layout

```
┌─────────────────────────────────────────┐
│ Google Maps Business Scraper            │
├─────────────────────────────────────────┤
│ ┌─────────────────────────────────────┐ │
│ │ Search Configuration                 │ │
│ │ ┌───────────────┐ ┌───────────────┐ │ │
│ │ │ Location      │ │ Radius (km)   │ │ │
│ │ │ [Colombo    ▼] │ [     5      ▼] │ │ │
│ │ └───────────────┘ └───────────────┘ │ │
│ │ ┌───────────────────────────────┐   │ │
│ │ │ Search Query                   │   │ │
│ │ │ [                          ]   │   │ │
│ │ └───────────────────────────────┘   │ │
│ └─────────────────────────────────────┘ │
│ ┌─────────────────────────────────────┐ │
│ │ Extraction Actions                   │ │
│ │ ┌───────────────┐ ┌───────────────┐ │ │
│ │ │ Extract from  │ │ Search and    │ │ │
│ │ │ Current View  │ │ Extract       │ │ │
│ │ └───────────────┘ └───────────────┘ │ │
│ └─────────────────────────────────────┘ │
│ ┌─────────────────────────────────────┐ │
│ │ Results                              │ │
│ │ Businesses: 0  Phone Numbers: 0      │ │
│ │ ┌───────────────────────────────┐   │ │
│ │ │                               │   │ │
│ │ │       No results yet          │   │ │
│ │ │                               │   │ │
│ │ └───────────────────────────────┘   │ │
│ └─────────────────────────────────────┘ │
│ ┌─────────────────────────────────────┐ │
│ │ Export Options                       │ │
│ │ ┌───────────┐ ┌───────────┐ ┌─────┐ │ │
│ │ │ CSV       │ │ JSON      │ │ Copy│ │ │
│ │ └───────────┘ └───────────┘ └─────┘ │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ [Settings]                   [Help]     │
└─────────────────────────────────────────┘
```

### Options UI Layout

```
┌─────────────────────────────────────────────────────────────┐
│ Google Maps Business Scraper - Settings                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Extraction Settings                                      │ │
│ │ ┌───────────────────────────────────────────────────┐   │ │
│ │ │ Maximum businesses to extract: [100          ]     │   │ │
│ │ │ Scroll delay (ms): [500                     ]     │   │ │
│ │ │ Maximum scroll attempts: [20                ]     │   │ │
│ │ │ Extract business details: [x] Yes  [ ] No         │   │ │
│ │ └───────────────────────────────────────────────────┘   │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Phone Number Validation                                  │ │
│ │ ┌───────────────────────────────────────────────────┐   │ │
│ │ │ Validate Sri Lankan numbers: [x] Yes  [ ] No      │   │ │
│ │ │ Convert to international format: [x] Yes  [ ] No  │   │ │
│ │ │ Include local format: [x] Yes  [ ] No             │   │ │
│ │ │ Identify number type: [x] Yes  [ ] No             │   │ │
│ │ └───────────────────────────────────────────────────┘   │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Sri Lanka Location Templates                             │ │
│ │ ┌───────────────────────────────────────────────────┐   │ │
│ │ │ [Colombo                                      ] [+]│   │ │
│ │ │                                                   │   │ │
│ │ │ Saved Locations:                                  │   │ │
│ │ │ - Colombo (radius: 5km)                      [✓] │   │ │
│ │ │ - Kandy (radius: 3km)                        [✓] │   │ │
│ │ │ - Galle (radius: 2km)                        [✓] │   │ │
│ │ │ - Jaffna (radius: 5km)                       [✓] │   │ │
│ │ └───────────────────────────────────────────────────┘   │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Export Settings                                          │ │
│ │ ┌───────────────────────────────────────────────────┐   │ │
│ │ │ Default export format: ( ) CSV  (•) JSON          │   │ │
│ │ │ Include headers in CSV: [x] Yes  [ ] No           │   │ │
│ │ │ File name template: [sri_lanka_businesses_{date}] │   │ │
│ │ └───────────────────────────────────────────────────┘   │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ [Save Settings]                             [Reset to Default] │
└─────────────────────────────────────────────────────────────┘
```

### Google Maps UI Integration

```
┌─────────────────────────────────────────────────────────────┐
│ Google Maps                                                  │
│ ┌───────────────────────────────────────────────────────┐   │
│ │ Search Box                                            │   │
│ └───────────────────────────────────────────────────────┘   │
│                                                             │
│ ┌─────────────────┐                 ┌───────────────────┐   │
│ │                 │                 │                   │   │
│ │                 │                 │ Business Results  │   │
│ │                 │                 │ ┌───────────────┐ │   │
│ │     Map View    │                 │ │ Business 1    │ │   │
│ │                 │                 │ └───────────────┘ │   │
│ │                 │                 │ ┌───────────────┐ │   │
│ │                 │                 │ │ Business 2    │ │   │
│ │                 │                 │ └───────────────┘ │   │
│ │                 │                 │ ┌───────────────┐ │   │
│ │                 │                 │ │ Business 3    │ │   │
│ └─────────────────┘                 │ └───────────────┘ │   │
│                                     │                   │   │
│                                     └───────────────────┘   │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Scraper Controls (Injected by Extension)                 │ │
│ │ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐   │ │
│ │ │ Extract All   │ │ Progress: 0/0 │ │ Stop          │   │ │
│ │ └───────────────┘ └───────────────┘ └───────────────┘   │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Technical Implementation Details

### 1. Manifest Structure (manifest.json)

```json
{
  "manifest_version": 3,
  "name": "Google Maps Business Scraper for Sri Lanka",
  "version": "1.0.0",
  "description": "Extract business names and phone numbers from Google Maps in Sri Lanka",
  "permissions": [
    "storage",
    "downloads",
    "activeTab"
  ],
  "host_permissions": [
    "https://www.google.com/maps/*",
    "https://maps.google.com/*"
  ],
  "action": {
    "default_popup": "popup/popup.html",
    "default_icon": {
      "16": "icons/icon16.png",
      "48": "icons/icon48.png",
      "128": "icons/icon128.png"
    }
  },
  "background": {
    "service_worker": "background/background.js"
  },
  "content_scripts": [
    {
      "matches": [
        "https://www.google.com/maps/*",
        "https://maps.google.com/*"
      ],
      "js": ["scripts/content.js"],
      "css": ["styles/content.css"]
    }
  ],
  "options_page": "options/options.html",
  "icons": {
    "16": "icons/icon16.png",
    "48": "icons/icon48.png",
    "128": "icons/icon128.png"
  }
}
```

### 2. Message Passing Protocol

The extension components will communicate using a standardized message protocol:

```javascript
// Example message format
{
  action: "ACTION_TYPE",  // e.g., "START_EXTRACTION", "EXTRACTION_PROGRESS", etc.
  payload: {              // Data specific to the action
    // Action-specific data
  },
  requestId: "unique-id", // For tracking request-response pairs
  timestamp: 1621234567890
}
```

Key message types:
- `START_EXTRACTION`: Initiate extraction process
- `STOP_EXTRACTION`: Stop ongoing extraction
- `EXTRACTION_PROGRESS`: Report extraction progress
- `EXTRACTION_COMPLETE`: Signal completion of extraction
- `EXTRACTION_ERROR`: Report extraction error
- `GET_RESULTS`: Request extraction results
- `EXPORT_RESULTS`: Request results export
- `UPDATE_SETTINGS`: Update extension settings

### 3. Data Models

#### Business Entity
```javascript
{
  name: "Business Name",
  phoneNumbers: [
    {
      number: "+94771234567",
      localFormat: "0771234567",
      isMobile: true,
      region: null
    },
    {
      number: "+94112345678",
      localFormat: "0112345678",
      isMobile: false,
      region: "Colombo"
    }
  ],
  address: "123 Main St, Colombo, Sri Lanka",
  category: "Restaurant",
  rating: 4.5,
  reviewsCount: 123,
  website: "https://example.com",
  location: {
    latitude: 6.9271,
    longitude: 79.8612
  },
  extractedAt: "2025-05-26T11:30:00.000Z"
}
```

#### Extraction Session
```javascript
{
  id: "session-123456",
  query: "restaurants in Colombo",
  location: "Colombo",
  radius: 5,
  startTime: "2025-05-26T11:30:00.000Z",
  endTime: "2025-05-26T11:35:00.000Z",
  status: "completed", // "in_progress", "completed", "error", "stopped"
  businessesFound: 45,
  phoneNumbersFound: 52,
  error: null,
  results: [] // Array of Business entities
}
```

## Error Handling Strategy

1. **UI Errors**
   - Display user-friendly error messages
   - Provide retry options where applicable
   - Log detailed errors to console for debugging

2. **Content Script Errors**
   - Implement fallback selectors for DOM elements
   - Handle Google Maps UI changes gracefully
   - Retry failed operations with exponential backoff
   - Report unrecoverable errors to background script

3. **Background Script Errors**
   - Maintain state consistency with transactions
   - Implement recovery mechanisms for interrupted operations
   - Log errors for troubleshooting

4. **Data Validation Errors**
   - Flag invalid or suspicious data
   - Provide validation warnings in UI
   - Allow user override for validation errors

## Performance Considerations

1. **Memory Management**
   - Batch processing of extraction results
   - Efficient DOM traversal to minimize reflows
   - Cleanup of unused resources

2. **CPU Usage**
   - Throttle intensive operations
   - Use requestAnimationFrame for UI updates
   - Implement debouncing for frequent events

3. **Storage Efficiency**
   - Compress large datasets
   - Implement pagination for large result sets
   - Clean up old extraction sessions

## Security and Privacy Considerations

1. **Data Handling**
   - Process all data locally within the browser
   - No transmission of data to external servers
   - Clear documentation of data usage

2. **Permissions**
   - Request minimal permissions required
   - Clearly explain permission usage to users
   - Provide fallback functionality for denied permissions

3. **Code Security**
   - Sanitize all user inputs
   - Implement Content Security Policy
   - Regular security reviews

## Implementation Roadmap

1. **Phase 1: Core Infrastructure**
   - Set up extension scaffolding
   - Implement basic message passing
   - Create storage module

2. **Phase 2: Content Script Development**
   - Implement Google Maps page detection
   - Develop DOM traversal utilities
   - Create business data extraction logic

3. **Phase 3: UI Development**
   - Build popup interface
   - Implement options page
   - Create injected UI controls

4. **Phase 4: Integration and Testing**
   - Connect all components
   - Implement error handling
   - Test on various Google Maps scenarios

5. **Phase 5: Optimization and Polishing**
   - Optimize performance
   - Refine user experience
   - Add final touches and documentation
