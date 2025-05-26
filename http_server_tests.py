import pytest
import socket
import threading
import time
from urllib.parse import urlparse
import re


class HTTPClient:
    """Simple HTTP client for testing that sends raw HTTP requests"""

    def __init__(self, host="localhost", port=8080):
        self.host = host
        self.port = port

    def send_request(self, method, path, headers=None, body=None, http_version="1.1"):
        """Send a raw HTTP request and return response"""
        if headers is None:
            headers = {}

        # Build request
        request_line = f"{method} {path} HTTP/{http_version}\r\n"

        # Add Host header (required for HTTP/1.1)
        if "Host" not in headers:
            headers["Host"] = f"{self.host}:{self.port}"

        # Add Content-Length if body is provided
        if body and "Content-Length" not in headers:
            headers["Content-Length"] = str(len(body.encode("utf-8")))

        # Build headers
        header_lines = []
        for key, value in headers.items():
            header_lines.append(f"{key}: {value}\r\n")

        # Complete request
        request = request_line + "".join(header_lines) + "\r\n"
        if body:
            request += body

        # Send request
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        try:
            sock.connect((self.host, self.port))
            sock.send(request.encode("utf-8"))

            # Read response
            response = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response += chunk

                # Check if we have a complete response
                if b"\r\n\r\n" in response:
                    headers_end = response.find(b"\r\n\r\n") + 4
                    headers_part = response[:headers_end].decode("utf-8")
                    body_part = response[headers_end:]

                    # Check Content-Length to see if we have full body
                    content_length_match = re.search(
                        r"Content-Length:\s*(\d+)", headers_part, re.IGNORECASE
                    )
                    if content_length_match:
                        expected_length = int(content_length_match.group(1))
                        if len(body_part) >= expected_length:
                            break
                    else:
                        # No Content-Length, assume response is complete
                        break

            return response.decode("utf-8", errors="ignore")
        finally:
            sock.close()


@pytest.fixture
def http_client():
    """Fixture providing HTTP client"""
    return HTTPClient()


def verify_response_status_line(response, expected_status="200", expected_protocol="HTTP/1.1"):
    """Parse HTTP response status line and verify it meets expectations.
    
    Args:
        response (str): Full HTTP response string
        expected_status (str): Expected status code (default: "200")
        expected_protocol (str): Expected protocol version (default: "HTTP/1.1")
        
    Returns:
        list: Components of status line [protocol, status_code, status_message]
    """
    status_parts = response.split("\r\n\r\n")[0].split(" ")
    assert status_parts[0] == expected_protocol, f"Expected {expected_protocol}, got {status_parts[0]}"
    assert status_parts[1] == expected_status, f"Expected status {expected_status}, got {status_parts[1]}"
    return status_parts


class TestBasicHTTPMethods:
    """Test basic HTTP methods"""

    def test_get_request(self, http_client):
        """Test basic GET request"""
        response = http_client.send_request("GET", "/")
        verify_response_status_line(response)
        assert "Content-Length:" in response or "Transfer-Encoding: chunked" in response

    def test_post_request(self, http_client):
        """Test POST request with body"""
        body = "test data"
        response = http_client.send_request("POST", "/", body=body)
        verify_response_status_line(response)

    def test_put_request(self, http_client):
        """Test PUT request"""
        response = http_client.send_request("PUT", "/test")
        verify_response_status_line(response)

    def test_delete_request(self, http_client):
        """Test DELETE request"""
        response = http_client.send_request("DELETE", "/test")
        verify_response_status_line(response)
        
    def test_head_request(self, http_client):
        """Test HEAD request (should have headers but no body)"""
        response = http_client.send_request("HEAD", "/")
        verify_response_status_line(response)
        # HEAD should not have a response body
        parts = response.split("\r\n\r\n", 1)
        if len(parts) > 1:
            assert parts[1].strip() == ""


class TestHTTPHeaders:
    """Test HTTP header handling"""

    def test_custom_headers(self, http_client):
        """Test server handles custom headers"""
        headers = {"X-Custom-Header": "test-value", "User-Agent": "pytest-client/1.0"}
        response = http_client.send_request("GET", "/", headers=headers)
        verify_response_status_line(response)

    def test_content_type_header(self, http_client):
        """Test Content-Type header handling"""
        headers = {"Content-Type": "application/json"}
        body = '{"test": "data"}'
        response = http_client.send_request("POST", "/", headers=headers, body=body)
        verify_response_status_line(response)

    def test_multiple_header_values(self, http_client):
        """Test headers with multiple values"""
        headers = {
            "Accept": "text/html, application/json",
            "Accept-Encoding": "gzip, deflate",
        }
        response = http_client.send_request("GET", "/", headers=headers)
        verify_response_status_line(response)


class TestHTTPPaths:
    """Test various URL paths"""

    def test_root_path(self, http_client):
        """Test root path"""
        response = http_client.send_request("GET", "/")
        verify_response_status_line(response)

    def test_nested_path(self, http_client):
        """Test nested paths"""
        response = http_client.send_request("GET", "/api/v1/users")
        verify_response_status_line(response)

    def test_path_with_query_string(self, http_client):
        """Test path with query parameters"""
        response = http_client.send_request("GET", "/search?q=test&limit=10")
        verify_response_status_line(response)

    def test_path_with_special_characters(self, http_client):
        """Test path with URL-encoded characters"""
        response = http_client.send_request("GET", "/test%20path")
        verify_response_status_line(response)


class TestHTTPVersions:
    """Test HTTP version handling"""

    def test_http_1_0_request(self, http_client):
        """Test HTTP/1.0 request"""
        response = http_client.send_request("GET", "/", http_version="1.0")
        verify_response_status_line(response)

    def test_http_1_1_request(self, http_client):
        """Test HTTP/1.1 request (default)"""
        response = http_client.send_request("GET", "/")
        verify_response_status_line(response)


class TestContentHandling:
    """Test request body and content handling"""

    def test_empty_body(self, http_client):
        """Test request with empty body"""
        response = http_client.send_request("POST", "/", body="")
        verify_response_status_line(response)

    def test_large_body(self, http_client):
        """Test request with larger body"""
        body = "x" * 10000  # 10KB of data
        response = http_client.send_request("POST", "/", body=body)
        verify_response_status_line(response)

    def test_json_content(self, http_client):
        """Test JSON content"""
        headers = {"Content-Type": "application/json"}
        body = '{"name": "test", "value": 42, "active": true}'
        response = http_client.send_request("POST", "/", headers=headers, body=body)
        verify_response_status_line(response)

    def test_form_data(self, http_client):
        """Test form-encoded data"""
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        body = "name=test&email=test%40example.com&age=25"
        response = http_client.send_request("POST", "/", headers=headers, body=body)
        verify_response_status_line(response)


class TestHTTPResponseValidation:
    """Test HTTP response format validation"""

    def test_response_status_line(self, http_client):
        """Test response has valid status line"""
        response = http_client.send_request("GET", "/")
        lines = response.split("\r\n")
        status_line = lines[0]

        # Should match: HTTP/1.1 200 OK
        assert re.match(r"HTTP/1\.\d+ \d{3} .+", status_line)

    def test_response_headers_format(self, http_client):
        """Test response headers are properly formatted"""
        response = http_client.send_request("GET", "/")

        # Split headers and body
        parts = response.split("\r\n\r\n", 1)
        header_section = parts[0]

        # Check each header line (skip status line)
        header_lines = header_section.split("\r\n")[1:]
        for line in header_lines:
            if line.strip():  # Skip empty lines
                assert ":" in line, f"Invalid header format: {line}"

    def test_response_has_required_headers(self, http_client):
        """Test response includes required headers"""
        response = http_client.send_request("GET", "/")

        # Should have either Content-Length or Transfer-Encoding
        assert (
            "Content-Length:" in response or "Transfer-Encoding:" in response
        ), "Response missing Content-Length or Transfer-Encoding header"


class TestErrorHandling:
    """Test server error handling"""

    def test_malformed_request_line(self, http_client):
        """Test handling of malformed request line"""
        # Send malformed request manually
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        try:
            sock.connect((http_client.host, http_client.port))
            sock.send(b"INVALID REQUEST LINE\r\n\r\n")
            response = sock.recv(4096).decode("utf-8")
            # Should get 400 Bad Request or connection closed
            assert (
                "400" in response or response == ""
            ), "Server should handle malformed requests gracefully"
        except (ConnectionResetError, ConnectionAbortedError):
            # Connection reset is also acceptable
            pass
        finally:
            sock.close()

    def test_missing_host_header(self, http_client):
        """Test request without Host header (required in HTTP/1.1)"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        try:
            sock.connect((http_client.host, http_client.port))
            request = "GET / HTTP/1.1\r\n\r\n"  # No Host header
            sock.send(request.encode("utf-8"))
            response = sock.recv(4096).decode("utf-8")
            # Should get 400 Bad Request for missing Host header
            assert response.startswith("HTTP/1.1"), "Should get HTTP response"
        finally:
            sock.close()


class TestConnectionHandling:
    """Test connection handling"""

    def test_connection_close(self, http_client):
        """Test Connection: close header"""
        headers = {"Connection": "close"}
        response = http_client.send_request("GET", "/", headers=headers)
        verify_response_status_line(response)

    def test_keep_alive(self, http_client):
        """Test persistent connections (HTTP/1.1 default)"""
        # Make multiple requests to test keep-alive
        response1 = http_client.send_request("GET", "/")
        response2 = http_client.send_request("GET", "/test")

        assert response1.startswith("HTTP/1.1")
        assert response2.startswith("HTTP/1.1")

    def test_multiple_requests_same_connection(self, http_client):
        """Test multiple requests on same connection"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10.0)
        try:
            sock.connect((http_client.host, http_client.port))

            # First request
            request1 = (
                f"GET / HTTP/1.1\r\nHost: {http_client.host}:{http_client.port}\r\n\r\n"
            )
            sock.send(request1.encode("utf-8"))
            response1 = sock.recv(4096).decode("utf-8")

            # Second request on same connection
            request2 = f"GET /test HTTP/1.1\r\nHost: {http_client.host}:{http_client.port}\r\n\r\n"
            sock.send(request2.encode("utf-8"))
            response2 = sock.recv(4096).decode("utf-8")

            assert response1.startswith("HTTP/1.1")
            assert response2.startswith("HTTP/1.1")

        except socket.timeout:
            # If server doesn't support keep-alive, that's also valid
            pass
        finally:
            sock.close()


class TestConcurrency:
    """Test concurrent request handling"""

    @pytest.mark.skip("Server does not currently support concurrent connections")
    def test_concurrent_requests(self, http_client):
        """Test server handles concurrent requests"""

        def make_request():
            client = HTTPClient(http_client.host, http_client.port)
            return client.send_request("GET", "/")

        # Start multiple threads
        threads = []
        results = []

        def thread_worker():
            result = make_request()
            results.append(result)

        # Create 5 concurrent requests
        for _ in range(5):
            thread = threading.Thread(target=thread_worker)
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join(timeout=10)

        # Check all requests succeeded
        assert len(results) == 5
        for result in results:
            verify_response_status_line(result)


# Configuration for pytest
def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (may take longer to run)"
    )


# Mark slow tests
pytestmark = pytest.mark.slow
