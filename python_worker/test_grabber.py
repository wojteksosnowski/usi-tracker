import pytest
from .grabber import extract_links_with_regex

def test_extract_links_with_regex():
    html = """
    <html>
        <body>
            <img src="https://example.com/1.jpg" />
            <a href="https://example.com/2.png">Link</a>
            <div data-url="https://example.com/3.webp">Data</div>
            <!-- Mixed case and special chars -->
            <img src="https://example.com/space%20image.jpg" />
        </body>
    </html>
    """
    
    # Simple image regex
    regex = r'https?://[^\s"\'<>]+?\.(?:jpg|jpeg|png|webp)'
    
    links = extract_links_with_regex(html, regex)
    assert len(links) == 4
    assert "https://example.com/1.jpg" in links
    assert "https://example.com/2.png" in links
    assert "https://example.com/3.webp" in links
    assert "https://example.com/space image.jpg" in links # unquoted
