"use client";

import { useEffect, useState } from 'react';
import { fetchTargets, createTarget, triggerFullScan } from '@/lib/api';
import { Plus, Play, ShieldAlert, CheckCircle, RefreshCw, XCircle } from 'lucide-react';
import Link from 'next/link';
import { toast } from 'sonner';
import { motion, AnimatePresence } from 'framer-motion';
import { format } from 'date-fns';

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
      toast.error('Failed to fetch targets from backend');
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
      toast.success(`${domain} added successfully!`);
      setDomain('');
      loadTargets();
    } catch (err) {
      toast.error('Failed to add target.');
    }
  };

  const handleScan = async (targetDomain: string) => {
    try {
      await triggerFullScan(targetDomain);
      toast.success(`Autonomous scan initiated for ${targetDomain}!`);
    } catch (err) {
      toast.error(`Failed to trigger scan for ${targetDomain}`);
    }
  };

  return (
    <div className="space-y-6 text-slate-800">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Target Management</h1>
        <button onClick={loadTargets} className="text-slate-500 hover:text-slate-900 transition flex items-center gap-2 bg-white px-4 py-2 rounded-lg border border-slate-200 shadow-sm hover:shadow">
          <RefreshCw size={18} /> Refresh
        </button>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm"
      >
        <h2 className="text-lg font-semibold mb-4 text-slate-700">Add New Target Scope</h2>
        <form onSubmit={handleCreate} className="flex gap-4">
          <input
            type="text"
            placeholder="e.g. example.com"
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
            className="flex-1 px-4 py-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-shadow bg-slate-50 focus:bg-white"
            required
          />
          <button type="submit" className="bg-blue-600 text-white px-8 py-3 rounded-lg hover:bg-blue-700 flex items-center gap-2 font-medium transition shadow-sm hover:shadow">
            <Plus size={20} />
            Register Target
          </button>
        </form>
      </motion.div>

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200">
              <th className="px-6 py-4 font-semibold text-slate-600 w-24">ID</th>
              <th className="px-6 py-4 font-semibold text-slate-600">Domain</th>
              <th className="px-6 py-4 font-semibold text-slate-600">Registered</th>
              <th className="px-6 py-4 font-semibold text-slate-600">Status</th>
              <th className="px-6 py-4 font-semibold text-slate-600 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            <AnimatePresence>
              {loading ? (
                Array.from({ length: 3 }).map((_, i) => (
                  <motion.tr key={`skeleton-${i}`} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                    <td className="px-6 py-4"><div className="h-4 bg-slate-200 rounded animate-pulse w-8"></div></td>
                    <td className="px-6 py-4"><div className="h-4 bg-slate-200 rounded animate-pulse w-48"></div></td>
                    <td className="px-6 py-4"><div className="h-4 bg-slate-200 rounded animate-pulse w-24"></div></td>
                    <td className="px-6 py-4"><div className="h-6 bg-slate-200 rounded-full animate-pulse w-20"></div></td>
                    <td className="px-6 py-4"><div className="h-8 bg-slate-200 rounded animate-pulse w-32 ml-auto"></div></td>
                  </motion.tr>
                ))
              ) : targets.length === 0 ? (
                <motion.tr initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                  <td colSpan={5} className="px-6 py-16 text-center text-slate-500">
                    <div className="flex flex-col items-center justify-center gap-3">
                      <XCircle size={48} className="text-slate-300" />
                      <p className="text-lg font-medium text-slate-600">No targets registered yet.</p>
                      <p className="text-sm">Add a domain above to begin mapping the attack surface.</p>
                    </div>
                  </td>
                </motion.tr>
              ) : (
                targets.map((target) => (
                  <motion.tr
                    key={target.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="border-b border-slate-100 hover:bg-slate-50 transition-colors"
                  >
                    <td className="px-6 py-4 font-mono text-sm text-slate-500">#{target.id}</td>
                    <td className="px-6 py-4 font-medium text-slate-800">{target.domain}</td>
                    <td className="px-6 py-4 text-sm text-slate-500">
                      {format(new Date(target.created_at), 'MMM dd, yyyy')}
                    </td>
                    <td className="px-6 py-4">
                      {target.is_active ? (
                        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-700">
                          <CheckCircle size={14} /> ACTIVE
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-600">
                          INACTIVE
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-right flex items-center justify-end gap-3">
                      <button onClick={() => handleScan(target.domain)} className="text-red-600 hover:text-red-700 hover:bg-red-50 px-3 py-1.5 rounded-lg transition font-medium flex items-center gap-2 text-sm border border-transparent hover:border-red-200 focus:ring-2 focus:ring-red-200">
                        <Play size={16} /> Fuzz
                      </button>
                      <Link href={`/reports/${target.id}`} className="text-blue-600 hover:text-blue-700 hover:bg-blue-50 px-3 py-1.5 rounded-lg transition font-medium flex items-center gap-2 text-sm border border-transparent hover:border-blue-200 focus:ring-2 focus:ring-blue-200">
                        <ShieldAlert size={16} /> Report
                      </Link>
                    </td>
                  </motion.tr>
                ))
              )}
            </AnimatePresence>
          </tbody>
        </table>
      </div>
    </div>
  );
}
