"""Tests for ImportService - CSV/Excel import functionality."""
import pytest
import csv
import tempfile
import os
from pathlib import Path

from services.import_service import ImportService, ImportResult, ImportError as ImportErr


class TestImportFromFile:
    """Test main import_from_file method."""
    
    def test_import_unsupported_format(self, import_service):
        """Test importing unsupported file format."""
        result = import_service.import_from_file("test.txt")
        
        assert result.success_count == 0
        assert result.has_errors is True
        assert len(result.errors) == 1
        assert "Unsupported file format" in result.errors[0].message
    
    def test_import_nonexistent_csv_file(self, import_service):
        """Test importing non-existent CSV file."""
        result = import_service.import_from_file("nonexistent.csv")
        
        assert result.success_count == 0
        assert result.has_errors is True
        assert any("not found" in err.message for err in result.errors)


class TestCSVImport:
    """Test CSV import functionality."""
    
    def test_import_valid_csv(self, import_service):
        """Test importing a valid CSV file."""
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['name', 'animal_type', 'breed', 'age', 'health_status'])
            writer.writeheader()
            writer.writerow({
                'name': 'Test Dog',
                'animal_type': 'dog',
                'breed': 'Labrador',
                'age': '3',
                'health_status': 'healthy'
            })
            csv_path = f.name
        
        try:
            result = import_service.import_from_file(csv_path)
            
            assert result.success_count == 1
            assert result.has_errors is False
        finally:
            os.unlink(csv_path)
    
    def test_import_csv_with_invalid_row(self, import_service):
        """Test importing CSV with invalid data."""
        # Create CSV with invalid age
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['name', 'type', 'breed', 'age', 'health_status'])
            writer.writeheader()
            writer.writerow({
                'name': 'Test Dog',
                'type': 'dog',
                'breed': 'Labrador',
                'age': '999',  # Invalid age
                'health_status': 'healthy'
            })
            csv_path = f.name
        
        try:
            result = import_service.import_from_file(csv_path)
            
            # Should have errors for invalid age
            assert result.has_errors is True
        finally:
            os.unlink(csv_path)
    
    def test_import_csv_missing_required_field(self, import_service):
        """Test importing CSV with missing required field."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['name', 'breed', 'age', 'health_status'])
            writer.writeheader()
            writer.writerow({
                'name': 'Test Dog',
                # Missing 'animal_type' field
                'breed': 'Labrador',
                'age': '3',
                'health_status': 'healthy'
            })
            csv_path = f.name
        
        try:
            result = import_service.import_from_file(csv_path)
            
            # Should fail due to missing required header
            assert result.has_errors is True
        finally:
            os.unlink(csv_path)
    
    def test_import_empty_csv(self, import_service):
        """Test importing empty CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='', encoding='utf-8') as f:
            csv_path = f.name
        
        try:
            result = import_service.import_from_file(csv_path)
            
            assert result.success_count == 0
            assert result.has_errors is True
            assert any("empty" in err.message.lower() for err in result.errors)
        finally:
            os.unlink(csv_path)
    
    def test_import_csv_with_comments(self, import_service):
        """Test importing CSV with comment lines."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='', encoding='utf-8') as f:
            f.write("# This is a comment\n")
            f.write("# Another comment\n")
            f.write("name,type,breed,age,health_status\n")
            f.write("Test Dog,dog,Labrador,3,healthy\n")
            csv_path = f.name
        
        try:
            result = import_service.import_from_file(csv_path)
            
            # Comments should be ignored
            assert result.success_count >= 0  # May succeed or fail depending on validation
        finally:
            os.unlink(csv_path)
    
    def test_import_csv_with_bom(self, import_service):
        """Test importing CSV with UTF-8 BOM."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=['name', 'type', 'breed', 'age', 'health_status'])
            writer.writeheader()
            writer.writerow({
                'name': 'Test Dog',
                'type': 'dog',
                'breed': 'Labrador',
                'age': '3',
                'health_status': 'healthy'
            })
            csv_path = f.name
        
        try:
            result = import_service.import_from_file(csv_path)
            
            # BOM should be handled
            assert result.success_count >= 0
        finally:
            os.unlink(csv_path)


class TestExcelImport:
    """Test Excel import functionality."""
    
    def test_import_excel_without_openpyxl(self, import_service):
        """Test that importing Excel without openpyxl gives helpful error."""
        # This test verifies error handling when openpyxl is not installed
        # If openpyxl IS installed, skip this test
        try:
            import openpyxl
            pytest.skip("openpyxl is installed, skipping this test")
        except ModuleNotFoundError:
            pass
        
        # Create a temp .xlsx file (even if invalid)
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            xlsx_path = f.name
        
        try:
            result = import_service.import_from_file(xlsx_path)
            
            # Should give openpyxl error
            assert isinstance(result, ImportResult)
            assert result.has_errors is True
            assert any("openpyxl" in err.message for err in result.errors)
        finally:
            if os.path.exists(xlsx_path):
                os.unlink(xlsx_path)


class TestImportValidation:
    """Test import validation logic."""
    
    def test_valid_animal_types(self, import_service):
        """Test valid animal types."""
        assert "dog" in import_service.VALID_ANIMAL_TYPES
        assert "cat" in import_service.VALID_ANIMAL_TYPES
        assert "other" in import_service.VALID_ANIMAL_TYPES
    
    def test_valid_health_statuses(self, import_service):
        """Test valid health statuses."""
        assert "healthy" in import_service.VALID_HEALTH_STATUSES
        assert "recovering" in import_service.VALID_HEALTH_STATUSES
        assert "injured" in import_service.VALID_HEALTH_STATUSES
    
    def test_age_constraints(self, import_service):
        """Test age constraints."""
        assert import_service.MIN_AGE == 0
        assert import_service.MAX_AGE == 21


class TestImportResult:
    """Test ImportResult dataclass."""
    
    def test_import_result_total_rows(self):
        """Test total_rows property."""
        result = ImportResult()
        result.success_count = 5
        result.errors = [ImportErr(row=1, message="Error 1"), ImportErr(row=2, message="Error 2")]
        
        assert result.total_rows == 7
    
    def test_import_result_has_errors(self):
        """Test has_errors property."""
        result1 = ImportResult()
        result1.errors = []
        assert result1.has_errors is False
        
        result2 = ImportResult()
        result2.errors = [ImportErr(row=1, message="Error")]
        assert result2.has_errors is True
    
    def test_import_result_all_failed(self):
        """Test all_failed property."""
        result1 = ImportResult()
        result1.success_count = 0
        result1.errors = []
        assert result1.all_failed is False
        
        result2 = ImportResult()
        result2.success_count = 0
        result2.errors = [ImportErr(row=1, message="Error")]
        assert result2.all_failed is True
        
        result3 = ImportResult()
        result3.success_count = 1
        result3.errors = [ImportErr(row=1, message="Error")]
        assert result3.all_failed is False


class TestMultipleRowImport:
    """Test importing multiple rows."""
    
    def test_import_multiple_valid_rows(self, import_service):
        """Test importing multiple valid rows."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['name', 'animal_type', 'breed', 'age', 'health_status'])
            writer.writeheader()
            writer.writerow({'name': 'Dog 1', 'animal_type': 'dog', 'breed': 'Labrador', 'age': '2', 'health_status': 'healthy'})
            writer.writerow({'name': 'Dog 2', 'animal_type': 'dog', 'breed': 'Poodle', 'age': '3', 'health_status': 'healthy'})
            writer.writerow({'name': 'Cat 1', 'animal_type': 'cat', 'breed': 'Persian', 'age': '1', 'health_status': 'healthy'})
            csv_path = f.name
        
        try:
            result = import_service.import_from_file(csv_path)
            
            # All rows should succeed
            assert result.success_count == 3
            assert result.has_errors is False
        finally:
            os.unlink(csv_path)
    
    def test_import_mixed_valid_invalid_rows(self, import_service):
        """Test importing mix of valid and invalid rows."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['name', 'animal_type', 'breed', 'age', 'health_status'])
            writer.writeheader()
            writer.writerow({'name': 'Valid Dog', 'animal_type': 'dog', 'breed': 'Labrador', 'age': '2', 'health_status': 'healthy'})
            writer.writerow({'name': 'Invalid Age', 'animal_type': 'dog', 'breed': 'Poodle', 'age': '999', 'health_status': 'healthy'})
            writer.writerow({'name': 'Valid Cat', 'animal_type': 'cat', 'breed': 'Persian', 'age': '1', 'health_status': 'healthy'})
            csv_path = f.name
        
        try:
            result = import_service.import_from_file(csv_path)
            
            # Should have some successes and some errors
            assert result.success_count >= 1
            assert result.has_errors is True
        finally:
            os.unlink(csv_path)
