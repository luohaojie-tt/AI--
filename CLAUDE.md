# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an SNR (Signal-to-Noise Ratio) data visualization tool built with Python/Tkinter that provides professional data analysis and visualization capabilities for SNR configuration data. The tool supports multiple chart types, interactive features, and advanced data filtering/search capabilities.

## Architecture

### Core Modules
- `core/data_manager.py` - Main data management with parsing, validation, and statistical analysis
- `core/visualization.py` - Chart rendering and visualization logic
- `core/config.py` - Application configuration and constants

### Filter/Search System (V2.1 Feature)
- `filters/filter_models.py` - Data structures for filtering criteria and search parameters
- `filters/filter_manager.py` - High-performance data filtering with caching
- `filters/search_manager.py` - Exact and fuzzy search functionality with performance optimization

### UI Components
- `ui/filter_panel.py` - Data filtering UI panel with real-time filtering
- `ui/search_panel.py` - Advanced search UI with history and result visualization
- `snr_visualizer_optimized.py` - Main application with GUI and charting

### Key Features
1. **Multi-chart Visualization**: Line charts, heatmaps, 3D scatter plots, and multi-view displays
2. **Interactive 3D**: Professional 3D point picking and interaction
3. **Data Filtering**: Parameter range filtering and SNR-based filtering with real-time updates
4. **Advanced Search**: Exact and fuzzy search with tolerance matching
5. **Performance Optimization**: Caching, async processing, and memory management
6. **Data Export**: CSV export of filtered/search results and analysis data

## Common Development Tasks

### Running the Application
```bash
python snr_visualizer_optimized.py
```
Or use the batch file:
```bash
run.bat
```

### Dependencies Installation
```bash
pip install -r requirements.txt
```

Key dependencies:
- matplotlib>=3.3.0 (charting)
- pandas>=1.1.0 (data processing)
- numpy>=1.19.0 (numerical operations)
- tkinter (GUI framework)

### Testing
Run specific test files:
```bash
python tests/test_all_features.py
python tests/test_filter_search.py
```

### Code Structure Guidelines
1. Follow the modular architecture with clear separation between core, filters, and UI
2. Use dataclasses for structured data (SNRDataPoint, FilterCriteria, SearchParams)
3. Implement async operations for heavy computations using ThreadPoolExecutor
4. Use caching for performance-critical operations (FilterCache, SearchCache)
5. Follow consistent error handling with detailed user feedback
6. Maintain Chinese language support throughout the UI

### Performance Considerations
1. Large datasets (>1000 points) should use async processing
2. Enable caching for repeated operations
3. Use proper threading to avoid UI freezing
4. Implement proper memory cleanup for 3D visualizations