"use client";

import { useEffect, useState } from 'react';
import { fetchTargets, createTarget, triggerFullScan } from '@/lib/api';
import { Plus, Play, ShieldAlert, CheckCircle, RefreshCw } from 'lucide-react';
import Link from 'next/link';

type Target = {
  id: number;
  domain: string;
  is_active: boolean;
  created_at: string;
};

export default function TargetsPage() {
  const [targets, setTargets] = useState<Target[]>([]);
  const [domain, setDomain] = useState('');
  const [loading, setLoading] = useState(true);

  const loadTargets = async () => {
    try {
      const data = await fetchTargets();
      setTargets(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTargets();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!domain) return;
    try {
      await createTarget(domain);
      setDomain('');
      loadTargets();
    } catch (err) {
      alert('Failed to add target.');
    }
  };

  const handleScan = async (targetDomain: string) => {
    try {
      await triggerFullScan(targetDomain);
      alert(`Scan triggered for ${targetDomain}!`);
    } catch (err) {
      alert(`Failed to trigger scan for ${targetDomain}`);
    }
  };

  return (
    <div className="space-y-6 text-slate-800">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Target Management</h1>
        <button onClick={loadTargets} className="text-slate-500 hover:text-slate-900 transition flex items-center gap-2">
          <RefreshCw size={18} /> Refresh
        </button>
      </div>

      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <h2 className="text-lg font-semibold mb-4">Add New Target</h2>
        <form onSubmit={handleCreate} className="flex gap-4">
          <input
            type="text"
            placeholder="example.com"
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
            className="flex-1 px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
          <button type="submit" className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 flex items-center gap-2 font-medium transition">
            <Plus size={20} />
            Register Target
          </button>
        </form>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200">
              <th className="px-6 py-4 font-semibold text-slate-600">ID</th>
              <th className="px-6 py-4 font-semibold text-slate-600">Domain</th>
              <th className="px-6 py-4 font-semibold text-slate-600">Status</th>
              <th className="px-6 py-4 font-semibold text-slate-600 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={4} className="px-6 py-8 text-center text-slate-500">Loading targets...</td>
              </tr>
            ) : targets.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-6 py-8 text-center text-slate-500">No targets registered yet.</td>
              </tr>
            ) : (
              targets.map((target) => (
                <tr key={target.id} className="border-b border-slate-100 hover:bg-slate-50">
                  <td className="px-6 py-4">{target.id}</td>
                  <td className="px-6 py-4 font-medium">{target.domain}</td>
                  <td className="px-6 py-4">
                    {target.is_active ? (
                      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700">
                        <CheckCircle size={14} /> Active
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-600">
                        Inactive
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-right flex items-center justify-end gap-3">
                    <button onClick={() => handleScan(target.domain)} className="text-red-600 hover:text-red-700 hover:bg-red-50 px-3 py-1.5 rounded-lg transition font-medium flex items-center gap-2 text-sm border border-transparent hover:border-red-200">
                      <Play size={16} /> Scan
                    </button>
                    <Link href={`/reports/${target.id}`} className="text-blue-600 hover:text-blue-700 hover:bg-blue-50 px-3 py-1.5 rounded-lg transition font-medium flex items-center gap-2 text-sm border border-transparent hover:border-blue-200">
                      <ShieldAlert size={16} /> View Report
                    </Link>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
