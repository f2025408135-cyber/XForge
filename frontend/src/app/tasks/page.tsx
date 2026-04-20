"use client";

import { useEffect, useState } from 'react';
import { fetchTasks } from '@/lib/api';
import { Activity, Clock, CheckCircle, AlertCircle, RefreshCw } from 'lucide-react';

type Task = {
  id: number;
  attack_type: string;
  status: string;
  created_at: string;
};

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);

  const loadTasks = async () => {
    try {
      const data = await fetchTasks();
      setTasks(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTasks();
    const interval = setInterval(loadTasks, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6 text-slate-800">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold flex items-center gap-3">
          <Activity size={32} className="text-blue-600" /> Active Tasks
        </h1>
        <button onClick={loadTasks} className="text-slate-500 hover:text-slate-900 transition flex items-center gap-2 bg-white px-4 py-2 rounded-lg border border-slate-200 shadow-sm">
          <RefreshCw size={18} /> Refresh
        </button>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200">
              <th className="px-6 py-4 font-semibold text-slate-600">Task ID</th>
              <th className="px-6 py-4 font-semibold text-slate-600">Attack Type</th>
              <th className="px-6 py-4 font-semibold text-slate-600">Started At</th>
              <th className="px-6 py-4 font-semibold text-slate-600">Status</th>
            </tr>
          </thead>
          <tbody>
            {loading && tasks.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-6 py-8 text-center text-slate-500">Loading tasks...</td>
              </tr>
            ) : tasks.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-6 py-8 text-center text-slate-500">No active tasks.</td>
              </tr>
            ) : (
              tasks.map((task) => (
                <tr key={task.id} className="border-b border-slate-100 hover:bg-slate-50">
                  <td className="px-6 py-4 font-mono text-sm font-medium">#{task.id}</td>
                  <td className="px-6 py-4 font-medium uppercase text-slate-700 tracking-wide text-xs">{task.attack_type.replace('_', ' ')}</td>
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
                      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-blue-100 text-blue-700">
                        <Clock size={14} className="animate-spin" /> {task.status}
                      </span>
                    )}
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
