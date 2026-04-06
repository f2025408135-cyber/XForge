package browser

import (
	"fmt"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"
)

func TestBrowserEngine_EvaluatePage(t *testing.T) {
	// Create mock server serving dynamic HTML
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "text/html")
		fmt.Fprintln(w, `<html><body>
			<div id="target">Initial</div>
			<script>
				setTimeout(function(){
					document.getElementById('target').innerText = 'Dynamic Content Loaded';
				}, 100);
			</script>
		</body></html>`)
	}))
	defer server.Close()

	engine, err := NewBrowserEngine("", false)
	if err != nil {
		t.Fatalf("Failed to initialize browser engine: %v", err)
	}
	defer engine.Close()

	// Test page rendering (waiting for dynamic content JS execution)
	res := engine.EvaluatePage(server.URL, `
		() => {
			return new Promise(resolve => {
				setTimeout(() => {
					let el = document.getElementById('target');
					if(el.innerText === 'Dynamic Content Loaded') {
						el.innerText = 'XForge Hooked';
					}
					resolve();
				}, 200); // Wait for the page's original JS to finish first
			});
		}
	`, 5*time.Second)

	if len(res.Errors) > 0 {
		t.Fatalf("EvaluatePage returned errors: %v", res.Errors)
	}

	if !strings.Contains(res.Body, "XForge Hooked") {
		t.Errorf("Expected DOM to be manipulated by injected JS, but got body: %s", res.Body)
	}
}

func TestBrowserEngine_SetCookies(t *testing.T) {
	engine, err := NewBrowserEngine("", false)
	if err != nil {
		t.Fatalf("Failed to initialize browser engine: %v", err)
	}
	defer engine.Close()

	// Ensure the browser object accepts standard cookie sets
	err = engine.SetCookies(nil)
	if err != nil {
		t.Errorf("SetCookies returned an error on empty slice: %v", err)
	}
}
