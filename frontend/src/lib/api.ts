const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export async function fetchTargets() {
  const response = await fetch(`${API_URL}/targets/`, { cache: 'no-store' });
  if (!response.ok) throw new Error('Failed to fetch targets');
  return response.json();
}

export async function createTarget(domain: string) {
  const response = await fetch(`${API_URL}/targets/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ domain }),
  });
  if (!response.ok) throw new Error('Failed to create target');
  return response.json();
}

export async function triggerFullScan(domain: string) {
  const response = await fetch(`${API_URL}/scan/full/${domain}`, {
    method: 'POST',
  });
  if (!response.ok) throw new Error('Failed to trigger scan');
  return response.json();
}

export async function fetchReport(targetId: number) {
  const response = await fetch(`${API_URL}/reports/${targetId}`, { cache: 'no-store' });
  if (!response.ok) throw new Error('Failed to fetch report');
  return response.json();
}

export async function fetchTasks() {
  const response = await fetch(`${API_URL}/tasks/`, { cache: 'no-store' });
  if (!response.ok) throw new Error('Failed to fetch tasks');
  return response.json();
}
