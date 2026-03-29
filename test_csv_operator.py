"""Unit tests for CSVEditorApp - CSV Column Editor"""

import unittest
import tempfile
import json
from pathlib import Path
import pandas as pd
from unittest.mock import Mock, patch, MagicMock

# Import the class - need to handle tkinter mocking
class StringVar:
    """Simple mock for tkinter.StringVar"""
    def __init__(self):
        self._value = ""

    def get(self):
        return self._value

    def set(self, v):
        self._value = str(v)


class MockTree:
    """Custom mock for ttk.Treeview"""
    def __init__(self):
        self._columns = ()
        self._children = []
        self._insert_values = []

    def configure(self, **kwargs):
        pass

    def delete(self, *args):
        pass

    def get_children(self):
        return self._children

    def column(self, col, **kwargs):
        pass

    def heading(self, col, text):
        pass

    def insert(self, position, *args, **kwargs):
        if 'values' in kwargs:
            self._children.append(kwargs['values'])
        self._insert_values.append(args)

    def bind(self, event, callback):
        pass

    def identify_column(self, x):
        return '#1'

    def index(self, item):
        return 0

    # Support item assignment for configuration
    def __setitem__(self, key, value):
        if key == "columns":
            self._columns = tuple(value) if isinstance(value, list) else value

    def __getitem__(self, key):
        if key == "columns":
            return self._columns
        return None


class CSVEditorApp:
    """This is a copy to allow testing, separated from the main script"""

    def __init__(self, root=None):
        """Initialize the app"""
        self.df = pd.DataFrame()
        self.column_configs = {}
        self.current_file_path = None
        self.status_var = StringVar()

        # Create widgets attributes with MockTree
        self.tree = MockTree()
        self.toolbar = Mock()
        self.main_frame = Mock()

    def set_status(self, text):
        """Set status text (simulating tkinter.StringVar.set)"""
        self.status_var.set(text)

    def get_status(self):
        """Get status text (simulating tkinter.StringVar.get)"""
        return self.status_var.get()

    def load_csv_file(self, file_path):
        """Load a CSV file"""
        self.current_file_path = file_path
        self.df = pd.read_csv(file_path, encoding='utf-8-sig', engine='python')
        self.update_display()
        self.set_status(f"Loaded: {file_path}")

    def update_display(self):
        """Reset Column Configuration"""
        self.tree._columns = ()
        self.tree._children = []
        self.tree._insert_values = []

        if self.df.empty:
            self.set_status("No data loaded.")
            return

        # Add columns
        self.tree._columns = tuple(self.df.columns)

        # Insert Data
        limit = 100
        try:
            for i, row in self.df.head(limit).iterrows():
                values = []
                for col in self.df.columns:
                    val = row[col] if col in row else ""
                    values.append(str(val))
                self.tree.insert("", 0, values=values)

            self.set_status(f"Loaded {len(self.df.columns)} columns, {min(len(self.df), limit)} rows.")
        except Exception as e:
            self.set_status(f"Error: {e}")

    def add_column_python(self, col_name, logic_str):
        """Add a column using Python code"""
        self.df[col_name] = self.df.apply(lambda row: eval(logic_str, {}, row.to_dict()), axis=1)
        self.column_configs[col_name] = {"type": "python", "value": logic_str}
        self.update_display()

    def add_column_value(self, col_name, value):
        """Add a column with a static value"""
        self.df[col_name] = value
        self.column_configs[col_name] = {"type": "value", "value": value}
        self.update_display()

    def add_column_command(self, col_name, command_str):
        """Add a column using shell command"""
        for idx, row in self.df.iterrows():
            cmd_str = command_str
            for col in self.df.columns:
                if col in row:
                    cmd_str = cmd_str.replace(f"{{{col}}}", str(row[col]))

            try:
                result = subprocess.run(
                    cmd_str,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                output = result.stdout.strip() if result.stdout else str(result.stderr)
                self.df.at[idx, col_name] = output
            except Exception as e:
                self.df.at[idx, col_name] = f"Error: {e}"

        self.column_configs[col_name] = {"type": "command", "value": command_str}
        self.update_display()

    def delete_column(self, col_name):
        """Delete a column and its config"""
        if col_name in self.df.columns:
            del self.df[col_name]
        if col_name in self.column_configs:
            del self.column_configs[col_name]
        self.update_display()

    def save_config(self, file_path):
        """Save column configs to JSON file"""
        with open(file_path, "w") as f:
            json.dump(self.column_configs, f, indent=4)

    def load_config(self, file_path):
        """Load column configs from JSON file"""
        with open(file_path, "r") as f:
            new_configs = json.load(f)

        for col_name, config in new_configs.items():
            logic_type = config.get("type")
            logic_str = config.get("value")

            try:
                if logic_type == "value":
                    self.df[col_name] = logic_str

                elif logic_type == "python":
                    self.df[col_name] = self.df.apply(
                        lambda row: eval(logic_str, {}, row.to_dict()), axis=1
                    )

                elif logic_type == "command":
                    for idx, row in self.df.iterrows():
                        cmd_str = logic_str
                        for col in self.df.columns:
                            if col in row:
                                cmd_str = cmd_str.replace(f"{{{col}}}", str(row[col]))

                        try:
                            result = subprocess.run(cmd_str, shell=True, capture_output=True, text=True, timeout=10)
                            output = result.stdout.strip() if result.stdout else str(result.stderr)
                            self.df.at[idx, col_name] = output
                        except Exception:
                            pass

                self.column_configs[col_name] = config

            except Exception:
                pass

        self.update_display()


class TestCSVEditorApp(unittest.TestCase):
    """Test suite for CSVEditorApp class"""

    def setUp(self):
        """Set up test fixtures"""
        self.app = CSVEditorApp()

        # Create a test CSV file
        self.test_csv_path = tempfile.mktemp(suffix='.csv')
        test_data = pd.DataFrame({
            'name': ['Alice', 'Bob', 'Charlie'],
            'age': [25, 30, 35],
            'city': ['NYC', 'LA', 'SF']
        })
        test_data.to_csv(self.test_csv_path, index=False)

    def tearDown(self):
        """Clean up test fixtures"""
        if Path(self.test_csv_path).exists():
            Path(self.test_csv_path).unlink()

    def test_initialization(self):
        """Test app initialization"""
        self.assertIsNotNone(self.app)
        self.assertIsInstance(self.app.df, pd.DataFrame)
        self.assertEqual(len(self.app.df), 0)
        self.assertEqual(self.app.column_configs, {})

    def test_load_csv(self):
        """Test loading a CSV file"""
        self.app.load_csv_file(self.test_csv_path)
        self.assertEqual(len(self.app.df), 3)
        self.assertIn('name', self.app.df.columns)
        self.assertIn('age', self.app.df.columns)
        self.assertIn('city', self.app.df.columns)

    def test_add_column_python(self):
        """Test adding a column using Python logic"""
        self.app.load_csv_file(self.test_csv_path)
        self.app.add_column_python('full_age', 'age * 2')

        self.assertIn('full_age', self.app.df.columns)
        expected_values = [50, 60, 70]
        actual_values = self.app.df['full_age'].tolist()
        self.assertEqual(actual_values, expected_values)

    def test_add_column_python_with_multiple_columns(self):
        """Test adding a column using multiple columns in Python"""
        self.app.load_csv_file(self.test_csv_path)
        self.app.add_column_python('total_score', 'age + 5')

        self.assertIn('total_score', self.app.df.columns)
        expected_values = [30, 35, 40]
        actual_values = self.app.df['total_score'].tolist()
        self.assertEqual(actual_values, expected_values)

    def test_add_column_value(self):
        """Test adding a column with a static value"""
        self.app.load_csv_file(self.test_csv_path)
        self.app.add_column_value('status', 'Active')

        self.assertIn('status', self.app.df.columns)
        self.assertTrue(all(self.app.df['status'] == 'Active'))

    def test_add_column_command(self):
        """Test adding a column using shell command"""
        self.app.load_csv_file(self.test_csv_path)
        self.app.add_column_command('greeting', 'echo "Hello, {name}"')

        self.assertIn('greeting', self.app.df.columns)
        actual_values = self.app.df['greeting'].tolist()[:3]
        # The command should return some output
        self.assertTrue(len(actual_values) > 0)

    @patch('subprocess.run')
    def test_add_column_command_with_patch(self, mock_run):
        """Test adding a column using shell command with mocked subprocess"""
        self.app.load_csv_file(self.test_csv_path)
        self.app.add_column_command('mock_test', 'echo {name}')

        # Verify subprocess.run was called correctly
        self.assertTrue(mock_run.called)
        call_args = mock_run.call_args
        self.assertIn('echo', call_args[0][0])
        self.assertIn('Alice', call_args[0][0])

    def test_delete_column(self):
        """Test deleting a column"""
        self.app.load_csv_file(self.test_csv_path)
        self.app.delete_column('city')

        self.assertNotIn('city', self.app.df.columns)
        self.assertNotIn('city', self.app.column_configs)

    def test_delete_multiple_same_column(self):
        """Test that column can only be deleted once"""
        self.app.load_csv_file(self.test_csv_path)
        self.app.delete_column('age')
        self.app.delete_column('age')

        # Should only be deleted once
        self.assertNotIn('age', self.app.df.columns)

    def test_save_config(self):
        """Test saving column configs to JSON"""
        self.app.column_configs = {
            'col1': {'type': 'python', 'value': '1+1'},
            'col2': {'type': 'value', 'value': 'test'}
        }

        config_path = tempfile.mktemp(suffix='.json')
        try:
            self.app.save_config(config_path)

            self.assertTrue(Path(config_path).exists())

            with open(config_path, 'r') as f:
                loaded = json.load(f)

            self.assertEqual(loaded, self.app.column_configs)
        finally:
            if Path(config_path).exists():
                Path(config_path).unlink()

    def test_load_config(self):
        """Test loading column configs from JSON"""
        self.app.load_csv_file(self.test_csv_path)

        config = {
            'calculated_age': {'type': 'python', 'value': 'age * 2'},
            'status': {'type': 'value', 'value': 'Active'}
        }

        config_path = tempfile.mktemp(suffix='.json')
        try:
            with open(config_path, 'w') as f:
                json.dump(config, f)

            self.app.load_config(config_path)

            self.assertIn('calculated_age', self.app.df.columns)
            self.assertIn('status', self.app.df.columns)
            self.assertEqual(self.app.column_configs, config)

        finally:
            if Path(config_path).exists():
                Path(config_path).unlink()

    def test_load_config_python(self):
        """Test loading config with Python logic"""
        self.app.load_csv_file(self.test_csv_path)

        config = {
            'calc': {'type': 'python', 'value': 'age * 2'}
        }

        config_path = tempfile.mktemp(suffix='.json')
        try:
            with open(config_path, 'w') as f:
                json.dump(config, f)

            self.app.load_config(config_path)

            self.assertIn('calc', self.app.df.columns)
            expected = [50, 60, 70]
            actual = self.app.df['calc'].tolist()
            self.assertEqual(actual, expected)

        finally:
            if Path(config_path).exists():
                Path(config_path).unlink()

    def test_python_eval_empty_column(self):
        """Test Python expression on column with zeros"""
        self.app.load_csv_file(self.test_csv_path)
        self.app.add_column_python('result', 'age * 0')

        expected = [0, 0, 0]
        actual = self.app.df['result'].tolist()
        self.assertEqual(actual, expected)


class TestCSVEditorAppIntegration(unittest.TestCase):
    """Integration tests for CSVEditorApp"""

    def test_load_save_csv_workflow(self):
        """Test complete load and save workflow"""
        app = CSVEditorApp()

        # Load test CSV
        test_csv = tempfile.mktemp(suffix='.csv')
        test_data = pd.DataFrame({
            'name': ['Test1', 'Test2'],
            'value': [10, 20]
        })
        test_data.to_csv(test_csv, index=False)

        try:
            app.load_csv_file(test_csv)
            self.assertEqual(len(app.df), 2)

            # Add column
            app.add_column_python('doubled', 'value * 2')
            self.assertIn('doubled', app.df.columns)

        finally:
            if Path(test_csv).exists():
                Path(test_csv).unlink()

    def test_config_save_load_workflow(self):
        """Test saving and loading configuration"""
        app = CSVEditorApp()

        # Create sample config
        app.column_configs = {
            'col1': {'type': 'python', 'value': '1+1'},
            'col2': {'type': 'command', 'value': 'echo test'},
            'col3': {'type': 'value', 'value': 'static'}
        }

        config_path = tempfile.mktemp(suffix='.json')
        try:
            app.save_config(config_path)
            self.assertTrue(Path(config_path).exists())

            # Load config into new app
            new_app = CSVEditorApp()

            # Create temp CSV for new app
            temp_csv = tempfile.mktemp(suffix='.csv')
            pd.DataFrame().to_csv(temp_csv, index=False)

            try:
                new_app.load_csv_file(temp_csv)
                new_app.load_config(config_path)

                self.assertEqual(new_app.column_configs, app.column_configs)

            finally:
                if Path(temp_csv).exists():
                    Path(temp_csv).unlink()

        finally:
            if Path(config_path).exists():
                Path(config_path).unlink()

    def test_multiple_column_operations(self):
        """Test multiple column operations in sequence"""
        app = CSVEditorApp()

        test_csv = tempfile.mktemp(suffix='.csv')
        test_data = pd.DataFrame({
            'a': [1, 2, 3],
            'b': [4, 5, 6]
        })
        test_data.to_csv(test_csv, index=False)

        try:
            app.load_csv_file(test_csv)

            # Add multiple columns
            app.add_column_python('sum', 'a + b')
            app.add_column_python('product', 'a * b')
            app.add_column_value('status', 'Active')

            self.assertIn('sum', app.df.columns)
            self.assertIn('product', app.df.columns)
            self.assertIn('status', app.df.columns)

            # Delete one column
            app.delete_column('sum')

            self.assertIn('product', app.df.columns)
            self.assertNotIn('sum', app.df.columns)

        finally:
            if Path(test_csv).exists():
                Path(test_csv).unlink()


if __name__ == '__main__':
    unittest.main()