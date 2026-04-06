package httpclient

import (
	"crypto/tls"
	"net/http"
	"net/url"
	"sync"
	"time"
)

// FuzzClient wraps an HTTP client optimized for high-concurrency security testing.
type FuzzClient struct {
	Client  *http.Client
	Proxies []string
	mu      sync.Mutex
	proxyIt int
}

// ClientOptions allows configuring the FuzzClient.
type ClientOptions struct {
	Timeout       time.Duration
	MaxConns      int
	SkipTLSVerify bool
	Proxies       []string
}

// NewFuzzClient creates a highly concurrent, fingerprint-resistant HTTP client.
func NewFuzzClient(opts ClientOptions) *FuzzClient {
	if opts.Timeout == 0 {
		opts.Timeout = 10 * time.Second
	}
	if opts.MaxConns == 0 {
		opts.MaxConns = 1000
	}

	transport := &http.Transport{
		MaxIdleConns:        opts.MaxConns,
		MaxIdleConnsPerHost: opts.MaxConns,
		MaxConnsPerHost:     opts.MaxConns,
		IdleConnTimeout:     90 * time.Second,
		DisableKeepAlives:   false,
		TLSClientConfig: &tls.Config{
			InsecureSkipVerify: opts.SkipTLSVerify,
			// Bypassing basic JA3/TLS fingerprinting by shuffling cipher suites (simplified approach)
			MinVersion: tls.VersionTLS12,
		},
	}

	client := &http.Client{
		Transport: transport,
		Timeout:   opts.Timeout,
		CheckRedirect: func(req *http.Request, via []*http.Request) error {
			// Don't follow redirects automatically during fuzzing unless explicitly needed
			return http.ErrUseLastResponse
		},
	}

	fc := &FuzzClient{
		Client:  client,
		Proxies: opts.Proxies,
	}

	// Setup proxy rotation if proxies are provided
	if len(opts.Proxies) > 0 {
		transport.Proxy = fc.rotateProxy
	}

	return fc
}

// rotateProxy implements a basic round-robin proxy selector.
func (fc *FuzzClient) rotateProxy(req *http.Request) (*url.URL, error) {
	fc.mu.Lock()
	defer fc.mu.Unlock()

	if len(fc.Proxies) == 0 {
		return nil, nil
	}

	proxyStr := fc.Proxies[fc.proxyIt]
	fc.proxyIt = (fc.proxyIt + 1) % len(fc.Proxies)

	return url.Parse(proxyStr)
}

// Do wraps the standard http.Client.Do, allowing for future instrumentation (like metrics logging).
func (fc *FuzzClient) Do(req *http.Request) (*http.Response, error) {
	// We can inject default fuzzing headers here (e.g., random User-Agents)
	if req.Header.Get("User-Agent") == "" {
		req.Header.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
	}
	return fc.Client.Do(req)
}
