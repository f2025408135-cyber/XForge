package browser

import (
	"fmt"
	"time"

	"github.com/go-rod/rod"
	"github.com/go-rod/rod/lib/launcher"
	"github.com/go-rod/rod/lib/proto"
)

// BrowserEngine wraps the headless browser capabilities for DOM fuzzing.
type BrowserEngine struct {
	browser *rod.Browser
}

// NewBrowserEngine initializes a stealth-capable, headless Chrome instance.
func NewBrowserEngine(useProxy string, headful bool) (*BrowserEngine, error) {
	// Construct stealth launcher to bypass basic WAF/Bot detection
	u := launcher.New().
		Headless(!headful).
		Set("disable-blink-features", "AutomationControlled").
		Set("user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

	if useProxy != "" {
		u = u.Proxy(useProxy)
	}

	url, err := u.Launch()
	if err != nil {
		return nil, fmt.Errorf("failed to launch browser: %w", err)
	}

	// Connect browser to launcher
	b := rod.New().ControlURL(url).MustConnect()

	return &BrowserEngine{
		browser: b,
	}, nil
}

// Close gracefully shuts down the browser.
func (e *BrowserEngine) Close() {
	if e.browser != nil {
		e.browser.MustClose()
	}
}

// DomResult holds the status of a DOM manipulation or extraction attempt.
type DomResult struct {
	URL        string
	StatusCode int
	Body       string
	Errors     []string
}

// EvaluatePage navigates to a URL, waits for network idle, and executes an optional JS payload.
func (e *BrowserEngine) EvaluatePage(targetURL string, jsPayload string, timeout time.Duration) DomResult {
	if timeout == 0 {
		timeout = 10 * time.Second
	}

	res := DomResult{URL: targetURL}

	page := e.browser.MustPage()
	defer page.MustClose()

	// Apply timeout to operations
	page = page.Timeout(timeout)

	// Intercept network requests to capture the main document status code
	router := page.HijackRequests()
	defer router.MustStop()

	var mainStatus int
	router.MustAdd("*", func(ctx *rod.Hijack) {
		ctx.MustLoadResponse()
		if ctx.Request.URL().String() == targetURL {
			mainStatus = ctx.Response.Payload().ResponseCode
		}
	})
	go router.Run()

	// Navigate and wait for DOM load
	err := page.Navigate(targetURL)
	if err != nil {
		res.Errors = append(res.Errors, fmt.Sprintf("navigation failed: %v", err))
		return res
	}

	page.MustWaitLoad()
	res.StatusCode = mainStatus

	// Execute JS if provided (e.g., verifying XSS execution or extracting specific local storage tokens)
	if jsPayload != "" {
		_, err := page.Eval(jsPayload)
		if err != nil {
			res.Errors = append(res.Errors, fmt.Sprintf("js evaluation failed: %v", err))
		}
	}

	// Capture the fully rendered DOM
	body, err := page.HTML()
	if err != nil {
		res.Errors = append(res.Errors, fmt.Sprintf("failed to extract DOM: %v", err))
	} else {
		res.Body = body
	}

	return res
}

// SetCookies injects authentication state into the browser session.
func (e *BrowserEngine) SetCookies(cookies []*proto.NetworkCookieParam) error {
	return e.browser.SetCookies(cookies)
}
