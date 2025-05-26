# Google Maps Business Scraper for Sri Lanka

A robust, efficient, and error-resistant web scraper for extracting business names and phone numbers from Google Maps, specifically tailored for Sri Lanka.

## Features

- Extract business names and phone numbers from Google Maps
- Support for various location input formats (city name, coordinates, district)
- Configurable search radius with automatic area subdivision
- Sri Lanka-specific phone number validation and formatting
- Anti-detection measures to ensure reliable operation
- Comprehensive error handling and retry mechanisms
- Multiple output formats (CSV, JSON)
- Command-line interface for easy use

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Install from Source

1. Clone the repository:
   ```
   git clone https://github.com/chama-x/google_maps_scraper.git
   cd google_maps_scraper
   ```

2. Install the package and dependencies:
   ```
   pip install -e .
   ```

3. Install Playwright browsers:
   ```
   playwright install
   ```

## Usage

### Command Line Interface

The scraper can be used directly from the command line:

```bash
python -m src.main "restaurants" --location "Colombo" --radius 5 --output-format csv
```

#### Arguments

- `query`: Search query (required)
- `--location`: Location to search in (city, district, or coordinates)
- `--radius`: Search radius in kilometers
- `--max-results`: Maximum number of results to return
- `--output-format`: Output format (csv or json)
- `--output-dir`: Output directory
- `--config`: Path to configuration file
- `--headless`: Run in headless mode

### Python API

You can also use the scraper as a Python library:

```python
from src.main import GoogleMapsScraper

# Initialize the scraper
scraper = GoogleMapsScraper()

# Search for businesses
results = scraper.search(
    query="hotels",
    location="Kandy",
    radius_km=3.0,
    max_results=50
)

# Save the results
output_path = scraper.save_results(
    results,
    output_format="csv",
    output_dir="./output"
)

print(f"Found {len(results.businesses)} businesses")
print(f"Results saved to {output_path}")
```

## Configuration

The scraper can be configured using a YAML configuration file. Create a file named `user_config.yaml` in the `config` directory to override default settings.

Example configuration:

```yaml
browser:
  headless: true
  stealth_mode: true

location:
  default_radius: 5
  max_radius: 50

output:
  format: csv
  output_dir: ./output

rate_limiting:
  requests_per_minute: 10
```

## Sri Lanka-Specific Features

This scraper is specifically tailored for Sri Lanka with the following features:

1. **Phone Number Validation**: Validates and formats Sri Lankan phone numbers (both mobile and landline)
2. **Location Support**: Built-in support for Sri Lankan cities, districts, and administrative divisions
3. **Language Handling**: Proper handling of Sinhala and Tamil character encoding
4. **Geographic Coverage**: Optimized for both urban and rural areas in Sri Lanka

## Limitations

1. **Google Maps Restrictions**: Google Maps typically limits search results to around 120 businesses per query
2. **Rate Limiting**: Excessive usage may trigger Google's rate limiting or CAPTCHA challenges
3. **Data Availability**: The scraper can only extract information that is publicly available on Google Maps
4. **Terms of Service**: Usage should comply with Google's Terms of Service
5. **Accuracy**: Business data on Google Maps may not always be up-to-date or complete

## Troubleshooting

### Common Issues

1. **No results found**
   - Try a different search query or location
   - Increase the search radius
   - Check if Google Maps is accessible from your network

2. **CAPTCHA challenges**
   - Reduce the rate of requests
   - Try using a different IP address or proxy
   - Wait for some time before trying again

3. **Invalid phone numbers**
   - Some businesses may have incorrectly formatted phone numbers on Google Maps
   - The scraper attempts to validate and correct formats where possible

4. **Browser automation issues**
   - Ensure Playwright is properly installed: `playwright install`
   - Try running in non-headless mode for debugging: `--headless false`

### Logs

Logs are stored in the `logs` directory and can be useful for diagnosing issues.

## Legal and Ethical Considerations

- This tool is intended for legitimate data collection purposes
- Users should comply with Google's Terms of Service
- Respect rate limits and avoid excessive scraping
- Handle extracted data in accordance with privacy regulations

## License

This project is licensed under the MIT License - see the LICENSE file for details.
