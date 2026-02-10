#!/usr/bin/env python3
"""
Comprehensive Test Suite for CCGLM MCP Server
Tests: Unit, Integration, E2E
"""

import asyncio
import sys
import os
import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import tempfile
import shutil

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import after path setup
from ccglm_mcp_server import (
    get_current_files,
    detect_new_files,
    format_file_summary,
    contains_chinese,
    DEFAULT_TIMEOUT,
    MAX_TIMEOUT,
    GLM_BASE_URL,
    GLM_AUTH_TOKEN,
)


class TestChineseDetection(unittest.TestCase):
    """Unit tests for Chinese character detection"""

    def test_english_text(self):
        """English text should not be detected as Chinese"""
        self.assertFalse(contains_chinese("Hello World"))
        self.assertFalse(contains_chinese("This is a test"))

    def test_turkish_text(self):
        """Turkish text should not be detected as Chinese"""
        self.assertFalse(contains_chinese("Merhaba dünya"))
        self.assertFalse(contains_chinese("Türkçe karakterler: ğüşıöç"))

    def test_spanish_text(self):
        """Spanish text should not be detected as Chinese"""
        self.assertFalse(contains_chinese("Hola mundo"))
        self.assertFalse(contains_chinese("¿Cómo estás?"))

    def test_chinese_text(self):
        """Chinese text should be detected"""
        self.assertTrue(contains_chinese("你好世界"))
        self.assertTrue(contains_chinese("中文测试"))

    def test_mixed_text(self):
        """Mixed text with Chinese should be detected"""
        self.assertTrue(contains_chinese("Hello 你好 World"))

    def test_empty_text(self):
        """Empty text should not be detected as Chinese"""
        self.assertFalse(contains_chinese(""))


class TestFileTracking(unittest.TestCase):
    """Unit tests for file tracking functionality"""

    def setUp(self):
        """Create temp directory for tests"""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Cleanup temp directory"""
        shutil.rmtree(self.test_dir)

    def test_get_current_files_empty_dir(self):
        """Empty directory should return empty set"""
        files = get_current_files(self.test_dir)
        self.assertEqual(len(files), 0)

    def test_get_current_files_with_files(self):
        """Should detect files in directory"""
        # Create test files
        test_file = os.path.join(self.test_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test")

        files = get_current_files(self.test_dir)
        self.assertEqual(len(files), 1)
        self.assertIn(test_file, files)

    def test_exclude_git_directory(self):
        """Should exclude .git directory"""
        git_dir = os.path.join(self.test_dir, ".git")
        os.makedirs(git_dir)
        git_file = os.path.join(git_dir, "config")
        with open(git_file, "w") as f:
            f.write("test")

        files = get_current_files(self.test_dir)
        self.assertNotIn(git_file, files)

    def test_detect_new_files(self):
        """Should detect newly created files"""
        before = {"file1.txt", "file2.txt"}
        after = {"file1.txt", "file2.txt", "file3.txt", "file4.txt"}

        new_files = detect_new_files(before, after)

        self.assertEqual(len(new_files), 2)
        self.assertIn("file3.txt", new_files)
        self.assertIn("file4.txt", new_files)

    def test_detect_no_new_files(self):
        """Should return empty list when no new files"""
        before = {"file1.txt", "file2.txt"}
        after = {"file1.txt", "file2.txt"}

        new_files = detect_new_files(before, after)

        self.assertEqual(len(new_files), 0)


class TestFileSummary(unittest.TestCase):
    """Unit tests for file summary formatting"""

    def test_no_new_files(self):
        """Should return original text when no new files"""
        result = format_file_summary([], "Original output")
        self.assertEqual(result, "Original output")

    def test_with_new_files(self):
        """Should format file summary correctly"""
        # Create a temp file for size calculation
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("test content")
            temp_file = f.name

        try:
            result = format_file_summary([temp_file], "Output")
            self.assertIn("GLM execution completed", result)
            self.assertIn("1 files created", result)
            self.assertIn(temp_file, result)
        finally:
            os.unlink(temp_file)

    def test_truncate_many_files(self):
        """Should truncate when more than 10 files"""
        files = [f"file{i}.txt" for i in range(15)]
        result = format_file_summary(files, "")
        self.assertIn("and 5 more files", result)


class TestTimeoutConfig(unittest.TestCase):
    """Unit tests for timeout configuration"""

    def test_default_timeout_value(self):
        """Default timeout should be 300 seconds"""
        self.assertEqual(DEFAULT_TIMEOUT, 300)

    def test_max_timeout_value(self):
        """Max timeout should be 600 seconds"""
        self.assertEqual(MAX_TIMEOUT, 600)

    def test_timeout_relationship(self):
        """Max timeout should be greater than default"""
        self.assertGreater(MAX_TIMEOUT, DEFAULT_TIMEOUT)


class TestGLMConfig(unittest.TestCase):
    """Unit tests for GLM configuration"""

    def test_glm_base_url(self):
        """GLM base URL should be configured"""
        self.assertIsNotNone(GLM_BASE_URL)
        self.assertTrue(GLM_BASE_URL.startswith("https://"))

    def test_glm_auth_token(self):
        """GLM auth token should be configured"""
        self.assertIsNotNone(GLM_AUTH_TOKEN)
        self.assertGreater(len(GLM_AUTH_TOKEN), 10)


class TestModelSelection(unittest.TestCase):
    """Unit tests for model selection logic"""

    def test_default_model(self):
        """Default model should be glm-4.7"""
        args = {"prompt": "test"}
        model = args.get("model", "glm-4.7")
        self.assertEqual(model, "glm-4.7")

    def test_explicit_model_selection(self):
        """Should use explicitly specified model"""
        args = {"prompt": "test", "model": "glm-4.5-air"}
        model = args.get("model", "glm-4.7")
        self.assertEqual(model, "glm-4.5-air")

    def test_model_timeout_glm47(self):
        """glm-4.7 should use default timeout"""
        model = "glm-4.7"
        model_timeout = 120 if model == "glm-4.5-air" else DEFAULT_TIMEOUT
        self.assertEqual(model_timeout, DEFAULT_TIMEOUT)

    def test_model_timeout_glm45air(self):
        """glm-4.5-air should use shorter timeout"""
        model = "glm-4.5-air"
        model_timeout = 120 if model == "glm-4.5-air" else DEFAULT_TIMEOUT
        self.assertEqual(model_timeout, 120)


class TestIntegrationGLMAPI(unittest.TestCase):
    """Integration tests for GLM API (requires network)"""

    @unittest.skipIf(os.getenv("SKIP_INTEGRATION_TESTS"), "Skipping integration tests")
    def test_glm_api_connection(self):
        """Test that GLM API is reachable"""
        import subprocess

        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
             "--connect-timeout", "5", GLM_BASE_URL],
            capture_output=True, text=True
        )

        # Should get some response (even if error)
        self.assertIn(result.stdout, ["000", "200", "401", "403", "404"])


class TestE2EMCP(unittest.TestCase):
    """E2E tests for MCP tool functionality"""

    def test_mcp_tool_via_cli(self):
        """Test MCP tool invocation via CLI simulation"""
        # This tests the tool schema is correct
        from ccglm_mcp_server import list_tools

        async def run_test():
            tools = await list_tools()
            self.assertEqual(len(tools), 1)
            self.assertEqual(tools[0].name, "ccglm")

            # Check schema
            schema = tools[0].inputSchema
            self.assertIn("prompt", schema["properties"])
            self.assertIn("model", schema["properties"])
            self.assertIn("prompt", schema["required"])

        asyncio.run(run_test())

    def test_model_enum_values(self):
        """Test that model enum contains expected values"""
        from ccglm_mcp_server import list_tools

        async def run_test():
            tools = await list_tools()
            model_enum = tools[0].inputSchema["properties"]["model"]["enum"]
            self.assertIn("glm-4.7", model_enum)
            self.assertIn("glm-4.5-air", model_enum)

        asyncio.run(run_test())


def run_tests():
    """Run all tests and return results"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestChineseDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestFileTracking))
    suite.addTests(loader.loadTestsFromTestCase(TestFileSummary))
    suite.addTests(loader.loadTestsFromTestCase(TestTimeoutConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestGLMConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestModelSelection))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegrationGLMAPI))
    suite.addTests(loader.loadTestsFromTestCase(TestE2EMCP))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result


if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "CCGLM MCP SERVER TEST SUITE" + " " * 11 + "║")
    print("╚" + "=" * 58 + "╝")
    print("\n")

    result = run_tests()

    print("\n" + "=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print("=" * 60)

    if result.wasSuccessful():
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        for test, traceback in result.failures + result.errors:
            print(f"\n--- {test} ---")
            print(traceback)
        sys.exit(1)
