"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Target, Activity, ShieldAlert, Zap } from "lucide-react";
import { fetchTargets, fetchTasks } from "@/lib/api";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";

export default function DashboardHome() {
  const [stats, setStats] = useState({ targets: 0, activeTasks: 0, completedTasks: 0 });

  useEffect(() => {
    async function loadData() {
      try {
        const [targets, tasks] = await Promise.all([fetchTargets(), fetchTasks()]);
        setStats({
          targets: targets.length,
          activeTasks: tasks.filter((t: any) => t.status === "PENDING" || t.status === "RUNNING").length,
          completedTasks: tasks.filter((t: any) => t.status === "COMPLETED").length,
        });
      } catch (e) {
        console.error(e);
      }
    }
    loadData();
  }, []);

  const mockTimelineData = [
    { name: "Mon", vulns: 4 },
    { name: "Tue", vulns: 3 },
    { name: "Wed", vulns: 12 },
    { name: "Thu", vulns: 8 },
    { name: "Fri", vulns: 25 },
    { name: "Sat", vulns: 18 },
    { name: "Sun", vulns: 30 },
  ];

  const pieData = [
    { name: "Completed", value: stats.completedTasks || 15 },
    { name: "Active", value: stats.activeTasks || 4 },
    { name: "Failed", value: 2 },
  ];
  const COLORS = ["#10b981", "#3b82f6", "#ef4444"];

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.1 },
    },
  };

  const itemVariants: any = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 300, damping: 24 } },
  };

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Platform Overview</h1>
          <p className="text-slate-500 mt-1">Autonomous security cluster metrics.</p>
        </div>
      </div>

      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="show"
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
      >
        <motion.div variants={itemVariants} className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-blue-50 text-blue-600 rounded-xl"><Target size={24} /></div>
            <div>
              <p className="text-sm text-slate-500 font-medium">Monitored Targets</p>
              <h3 className="text-3xl font-bold text-slate-800">{stats.targets}</h3>
            </div>
          </div>
        </motion.div>

        <motion.div variants={itemVariants} className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-amber-50 text-amber-600 rounded-xl"><Activity size={24} /></div>
            <div>
              <p className="text-sm text-slate-500 font-medium">Active Tasks</p>
              <h3 className="text-3xl font-bold text-slate-800">{stats.activeTasks}</h3>
            </div>
          </div>
        </motion.div>

        <motion.div variants={itemVariants} className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-green-50 text-green-600 rounded-xl"><Zap size={24} /></div>
            <div>
              <p className="text-sm text-slate-500 font-medium">Completed Scans</p>
              <h3 className="text-3xl font-bold text-slate-800">{stats.completedTasks}</h3>
            </div>
          </div>
        </motion.div>

        <motion.div variants={itemVariants} className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-red-50 text-red-600 rounded-xl"><ShieldAlert size={24} /></div>
            <div>
              <p className="text-sm text-slate-500 font-medium">Critical Findings</p>
              <h3 className="text-3xl font-bold text-slate-800">4</h3>
            </div>
          </div>
        </motion.div>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.4 }}
          className="lg:col-span-2 bg-white p-6 rounded-2xl shadow-sm border border-slate-200"
        >
          <h2 className="text-lg font-bold text-slate-800 mb-6">Vulnerability Discovery Rate</h2>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={mockTimelineData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorVulns" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <Tooltip
                  contentStyle={{ borderRadius: "12px", border: "none", boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)" }}
                />
                <Area type="monotone" dataKey="vulns" stroke="#ef4444" strokeWidth={3} fillOpacity={1} fill="url(#colorVulns)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.5 }}
          className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200 flex flex-col"
        >
          <h2 className="text-lg font-bold text-slate-800 mb-2">Task Distribution</h2>
          <div className="flex-1 flex items-center justify-center">
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie data={pieData} cx="50%" cy="50%" innerRadius={60} outerRadius={80} paddingAngle={5} dataKey="value">
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ borderRadius: "8px", border: "none", boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)" }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex justify-center gap-4 mt-4">
            {pieData.map((entry, i) => (
              <div key={entry.name} className="flex items-center gap-2 text-sm text-slate-600">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[i] }} />
                {entry.name}
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  );
}
