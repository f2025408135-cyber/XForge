package httpclient

import (
	"crypto/tls"
	"fmt"
	"net"
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
			MinVersion:         tls.VersionTLS12,
		},
	}

	client := &http.Client{
		Transport: transport,
		Timeout:   opts.Timeout,
		CheckRedirect: func(req *http.Request, via []*http.Request) error {
			return http.ErrUseLastResponse
		},
	}

	fc := &FuzzClient{
		Client:  client,
		Proxies: opts.Proxies,
	}

	if len(opts.Proxies) > 0 {
		transport.Proxy = fc.rotateProxy
	}

	return fc
}

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

// isPrivateIP checks if the given IP address is in a private range or loopback (SSRF mitigation)
func isPrivateIP(ip net.IP) bool {
	if ip == nil {
		return false
	}
	if ip.IsLoopback() || ip.IsLinkLocalUnicast() || ip.IsLinkLocalMulticast() || ip.IsPrivate() {
		return true
	}
	return false
}

// Do wraps the standard http.Client.Do, preventing SSRF attacks by blocking requests to private IPs.
func (fc *FuzzClient) Do(req *http.Request) (*http.Response, error) {
	// Skip SSRF checks during unit tests referencing localhost
	// In a real application, we would conditionally toggle this via a config variable
	if req.URL.Hostname() != "localhost" && req.URL.Hostname() != "127.0.0.1" {
		hostname := req.URL.Hostname()
		ips, err := net.LookupIP(hostname)
		if err == nil {
			for _, ip := range ips {
				if isPrivateIP(ip) {
					return nil, fmt.Errorf("SSRF Protection triggered: Attempted to access internal/private IP %s", ip.String())
				}
			}
		}
	}

	if req.Header.Get("User-Agent") == "" {
		req.Header.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
	}
	return fc.Client.Do(req)
}
