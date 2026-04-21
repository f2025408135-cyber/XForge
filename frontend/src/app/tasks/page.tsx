"use client";

import { useEffect, useState, useRef } from 'react';
import { fetchTasks } from '@/lib/api';
import { Activity, Clock, CheckCircle, AlertCircle, RefreshCw, Filter } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

type Task = {
  id: number;
  attack_type: string;
  status: string;
  created_at: string;
};

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'ALL' | 'PENDING' | 'COMPLETED'>('ALL');
  const mountedRef = useRef(true);

  const loadTasks = async () => {
    try {
      const data = await fetchTasks();
      if (mountedRef.current) {
        setTasks(data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      if (mountedRef.current) {
        setLoading(false);
      }
    }
  };

  useEffect(() => {
    mountedRef.current = true;

    // Recursive polling to prevent request pile-ups
    const poll = async () => {
      await loadTasks();
      if (mountedRef.current) {
        setTimeout(poll, 5000);
      }
    };

    poll();

    return () => {
      mountedRef.current = false;
    };
  }, []);

  const filteredTasks = tasks.filter(task => {
    if (filter === 'ALL') return true;
    if (filter === 'COMPLETED') return task.status === 'COMPLETED';
    if (filter === 'PENDING') return task.status.includes('PENDING') || task.status === 'RUNNING';
    return true;
  });

  return (
    <div className="space-y-6 text-slate-800">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <Activity size={32} className="text-blue-600" /> Active Tasks
        </h1>

        <div className="flex items-center gap-4">
          <div className="flex bg-white rounded-lg border border-slate-200 shadow-sm p-1">
            {(['ALL', 'PENDING', 'COMPLETED'] as const).map(f => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-4 py-1.5 rounded-md text-sm font-medium transition ${
                  filter === f ? 'bg-blue-50 text-blue-600 shadow-sm' : 'text-slate-500 hover:text-slate-700 hover:bg-slate-50'
                }`}
              >
                {f}
              </button>
            ))}
          </div>

          <button onClick={loadTasks} className="text-slate-500 hover:text-slate-900 transition flex items-center gap-2 bg-white px-4 py-2 rounded-lg border border-slate-200 shadow-sm">
            <RefreshCw size={18} /> Refresh
          </button>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200">
              <th className="px-6 py-4 font-semibold text-slate-600 w-32">Task ID</th>
              <th className="px-6 py-4 font-semibold text-slate-600">Attack Type</th>
              <th className="px-6 py-4 font-semibold text-slate-600">Started At</th>
              <th className="px-6 py-4 font-semibold text-slate-600">Status</th>
            </tr>
          </thead>
          <tbody>
            <AnimatePresence mode="popLayout">
              {loading && tasks.length === 0 ? (
                <motion.tr key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                  <td colSpan={4} className="px-6 py-12 text-center">
                    <div className="flex flex-col items-center gap-2 text-slate-500">
                      <RefreshCw size={24} className="animate-spin text-blue-500" />
                      Loading execution queue...
                    </div>
                  </td>
                </motion.tr>
              ) : filteredTasks.length === 0 ? (
                <motion.tr key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                  <td colSpan={4} className="px-6 py-16 text-center text-slate-500">
                    <div className="flex flex-col items-center justify-center gap-3">
                      <Filter size={48} className="text-slate-300" />
                      <p className="text-lg font-medium text-slate-600">No tasks found.</p>
                      <p className="text-sm">Try adjusting your filters or initiating a new scan.</p>
                    </div>
                  </td>
                </motion.tr>
              ) : (
                filteredTasks.map((task) => (
                  <motion.tr
                    layout
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    transition={{ duration: 0.2 }}
                    key={task.id}
                    className="border-b border-slate-100 hover:bg-slate-50"
                  >
                    <td className="px-6 py-4 font-mono text-sm font-semibold text-slate-600">#{task.id}</td>
                    <td className="px-6 py-4 font-medium uppercase text-slate-700 tracking-wide text-xs">
                      {task.attack_type.replace('_', ' ')}
                    </td>
                    <td className="px-6 py-4 text-slate-500 text-sm">
                      {new Date(task.created_at).toLocaleString()}
                    </td>
                    <td className="px-6 py-4">
                      {task.status === "COMPLETED" ? (
                        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-green-100 text-green-700">
                          <CheckCircle size={14} /> Completed
                        </span>
                      ) : task.status.includes("FAILED") ? (
                        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-red-100 text-red-700">
                          <AlertCircle size={14} /> Failed
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-blue-100 text-blue-700 shadow-[0_0_10px_rgba(59,130,246,0.3)]">
                          <Clock size={14} className="animate-spin" /> {task.status}
                        </span>
                      )}
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
