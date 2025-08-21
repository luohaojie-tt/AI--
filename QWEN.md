# SNR_SHOW Project Context for Qwen Code

## Project Overview

This is the SNR_SHOW project - a professional Signal-to-Noise Ratio (SNR) data analysis and visualization tool. The application provides multiple chart types and interactive features to help users deeply analyze SNR data distribution characteristics and correlation relationships.

### Core Features
- Multi-chart visualization (line charts, heatmaps, 3D scatter plots)
- Interactive data filtering and searching
- CSV data import and processing
- Performance-optimized rendering with caching
- Chinese language UI support

### Technology Stack
- **Python 3.x** - Main programming language
- **Tkinter** - GUI framework
- **Matplotlib** - Chart rendering and 3D visualization
- **Plotly/Dash** - Modern web-based visualization components
- **Pandas** - Data processing and analysis
- **NumPy** - Numerical computing

## Project Structure

```
SNR_SHOW/
├── core/                 # Core modules
│   ├── config.py         # Configuration management
│   ├── data_manager.py   # Data management
│   └── visualization.py  # Visualization components
├── filters/              # Filtering and search modules
│   ├── filter_manager.py # Filter manager
│   ├── filter_models.py  # Data models
│   └── search_manager.py # Search manager
├── ui/                   # User interface modules
│   ├── filter_panel.py   # Filter panel UI
│   └── search_panel.py   # Search panel UI
├── tests/                # Test files
│   ├── test_all_features.py
│   ├── test_filter_search.py
│   ├── test_integration.py
│   └── test_search_suggestions.py
├── docs/                 # Documentation
├── data/                 # Data files
├── requirements.txt      # Python dependencies
├── run.bat               # Launch script
└── snr_visualizer_optimized.py  # Main application
```

## Key Modules

### Main Application (snr_visualizer_optimized.py)
- Primary GUI interface with Tkinter
- Chart switching and interaction controls
- 3D scatter plot specialized interaction implementation
- Caching mechanism and performance optimization
- Data loading and management

### Core Modules (core/)
- **config.py** - Theme configuration, chart configuration, UI configuration, global configuration manager
- **data_manager.py** - CSV file reading and parsing, data format validation and cleaning, statistical analysis calculations, data point validation with hexadecimal support
- **visualization.py** - Modern chart components using Plotly/Dash, multiple chart types (line, heatmap, 3D scatter), theme and styling configuration, interactive features implementation

### Filtering & Search System (filters/)
- **filter_models.py** - Data structures (FilterCriteria, SearchParams, FilterStats)
- **filter_manager.py** - Filtering logic implementation, caching mechanism, performance optimization
- **search_manager.py** - Search algorithm implementation, search suggestions functionality, caching mechanism

### User Interface (ui/)
- **filter_panel.py** - Filtering UI components, parameter input controls
- **search_panel.py** - Search UI components, search input controls

### Configuration (core/config.py)
- Theme configuration (colors, styling)
- Chart configuration (sizes, animations)
- UI configuration (layout, fonts, breakpoints)
- Global configuration manager

## Data Format

The application expects CSV files with this format:
```csv
pre,main,post,snr
0xff6a,0x64,0xffce,18.234
0xff6a,0x96,0xffce,19.345
...
```

Where:
- **pre** - Pre-parameter value (supports hex format)
- **main** - Main parameter value (supports hex format)
- **post** - Post-parameter value (supports hex format)
- **snr** - Signal-to-Noise Ratio value

## Development Workflow

### Running the Application
```bash
# Using the batch file (Windows)
run.bat

# Or directly with Python
python snr_visualizer_optimized.py
```

### Installing Dependencies
```bash
pip install -r requirements.txt
```

### Key Requirements
- Python 3.7+
- Matplotlib >= 3.3.0
- Pandas >= 1.1.0
- NumPy >= 1.19.0
- Plotly >= 5.17.0
- Dash >= 2.14.0

## Development Guidelines

### Code Organization
1. **UI Layer** - snr_visualizer_optimized.py handles all user interactions
2. **Business Logic Layer** - Separate modules for data management and visualization
3. **Configuration Layer** - Centralized configuration management in config.py

### Data Flow
1. User loads CSV data through UI
2. DataManager validates and processes the data
3. Visualization module renders charts based on current view
4. Filter/Search modules provide data subset operations
5. Results are displayed in UI with interactive features

### Performance Considerations
- Implements intelligent caching for chart data
- Uses async loading for large datasets
- Optimizes memory management for long-running sessions
- Maintains responsive UI during data processing

## Testing

The project includes several test files:
- test_all_features.py - Comprehensive feature testing
- test_data.csv - Test data file
- test_filter_search.py - Filtering and searching tests
- test_integration.py - Integration tests
- test_search_suggestions.py - Search suggestion tests

Run tests with:
```bash
python test_all_features.py
```

## Common Tasks

### Adding New Chart Types
1. Implement new chart class in visualization.py
2. Add chart switching logic in snr_visualizer_optimized.py
3. Update UI controls for new chart type

### Extending Filter Criteria
1. Modify FilterCriteria dataclass in filter_models.py
2. Update filtering logic in filter_manager.py
3. Adjust UI components in filter_panel.py

### Customizing Themes
1. Modify ThemeConfig in config.py
2. Update get_plotly_theme() method for chart styling
3. Adjust UI configuration in UIConfig class

This documentation provides the necessary context for understanding and working with the SNR_SHOW project. For detailed implementation specifics, refer to the individual module files and the comprehensive README.md.