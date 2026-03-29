# CSV Column Editor

A Python desktop application that provides a graphical interface for manipulating, adding, and editing columns in CSV files with different types of operations.

## Features

- **Load CSV files** - Open and view CSV data with a tree-based interface
- **Add columns** using different logic types:
  - **Python code** - Use expressions with existing column variables (e.g., `col1 + col2 * 2`)
  - **Shell commands** - Execute commands with placeholders for column values (e.g., `echo "Hello {name}"`)
  - **Static values** - Apply a fixed value across all rows
- **Edit columns** - Modify column logic via right-click context menu
- **Delete columns** - Remove columns and their associated logic
- **Save configurations** - Save column operations as JSON for later reuse
- **Load configurations** - Load previously saved column configurations

## Requirements

- Python 3.7+
- pandas>=1.5.0
- tk>=8.6.0 (Tkinter)

## Installation

### Using pip:

```bash
pip install -r requirements.txt
```

### Manual installation:

```bash
pip install pandas
# Tkinter is usually included with Python, but on Linux you may need:
# sudo apt-get install python3-tk
```

## Usage

### Running the Application

1. Make sure you have installed the required dependencies:

```bash
pip install -r requirements.txt
```

2. Run the application:

```bash
python csv_operator.py
```

### Basic Workflow

1. **Open a CSV file** using the "Open CSV" button
2. **Add a new column** using the "Add Column" button
3. **Select column type** (Python, Command, or Value)
4. **Enter column name** and logic/expression
5. **Click "Apply / Update"** to create the column
6. **Save results** if needed using the "Save CSV" button
7. **Save configuration** using the "Save Config" button to reuse your column operations

### Example Operations

#### Adding a Calculated Column (Python)
- Column name: `full_age`
- Type: Python
- Expression: `age * 2`

#### Adding a Formatted Output (Command)
- Column name: `greeting`
- Type: Command
- Command: `echo "Hello, {name} from {city}"`

#### Adding a Static Column
- Column name: `status`
- Type: Value
- Value: `Active`

## Configuration Format

Column configurations are saved in JSON format:

```json
{
  "full_age": {
    "type": "python",
    "value": "age * 2"
  },
  "status": {
    "type": "value",
    "value": "Active"
  },
  "greeting": {
    "type": "command",
    "value": "echo {name}"
  }
}
```

## Running Tests

### Using pytest

```bash
pytest
```

### With coverage report:

```bash
pytest --cov=.
```

### Run specific test file:

```bash
pytest test_csv_operator.py
```

## Project Structure

```
csv_operator/
├── csv_operator.py      # Main application script
├── test_csv_operator.py # Unit tests
├── requirements.txt      # Python dependencies
├── pytest.ini          # Pytest configuration
└── README.md           # This file
```

## Technical Details

- Uses `tkinter` for the GUI
- Uses `pandas` for data manipulation and CSV handling
- Uses `subprocess` for shell command execution
- Stores column configurations in a dictionary for persistence

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is provided as-is for educational and practical purposes.

## Troubleshooting

### Issue: Tkinter not found
**Solution**: On Linux, install Tkinter:
```bash
sudo apt-get install python3-tk
```

### Issue: Excel CSVs with BOM
**Solution**: The app automatically handles UTF-8 BOM encoding with `encoding='utf-8-sig'`

### Issue: Command execution fails
**Solution**: Ensure shell commands are properly formatted and the required utilities are available in your system PATH.

## Author

Created as a CSV manipulation tool for enhanced productivity.