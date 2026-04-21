"use client";

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Target, Activity, FileText, Home, Network } from 'lucide-react';
import { motion } from 'framer-motion';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export default function Sidebar() {
  const pathname = usePathname();

  const links = [
    { href: '/', label: 'Dashboard', icon: Home },
    { href: '/targets', label: 'Targets', icon: Target },
    { href: '/tasks', label: 'Active Tasks', icon: Activity },
    { href: '/scope', label: 'Attack Graph', icon: Network },
    { href: '/reports', label: 'Reports', icon: FileText },
  ];

  return (
    <motion.div
      initial={{ x: -250 }}
      animate={{ x: 0 }}
      className="w-64 h-full bg-slate-900/95 backdrop-blur-xl text-white flex flex-col fixed left-0 top-0 border-r border-slate-800 shadow-2xl z-50"
    >
      <div className="p-6">
        <motion.h1
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-red-500 to-orange-400 tracking-wider"
        >
          XFORGE
        </motion.h1>
        <p className="text-xs text-slate-400 mt-1 uppercase tracking-widest font-semibold">Intelligence Layer</p>
      </div>

      <nav className="flex-1 px-3 space-y-2 mt-4">
        {links.map((link) => {
          const isActive = pathname === link.href || (pathname?.startsWith(link.href) && link.href !== '/');
          const Icon = link.icon;

          return (
            <Link key={link.href} href={link.href} className="block relative">
              {isActive && (
                <motion.div
                  layoutId="active-pill"
                  className="absolute inset-0 bg-blue-600/20 rounded-lg border border-blue-500/30"
                  transition={{ type: "spring", stiffness: 300, damping: 30 }}
                />
              )}
              <motion.div
                whileHover={{ x: 4 }}
                className={cn(
                  "flex items-center gap-3 px-4 py-3 rounded-lg transition-colors relative z-10",
                  isActive ? "text-blue-400" : "text-slate-400 hover:text-slate-200"
                )}
              >
                <Icon size={20} className={isActive ? "drop-shadow-md" : ""} />
                <span className="font-medium">{link.label}</span>
              </motion.div>
            </Link>
          )
        })}
      </nav>

      <div className="p-4 border-t border-slate-800 bg-slate-900/50">
        <div className="flex items-center justify-between text-sm text-slate-400">
          <div className="flex items-center gap-2 font-medium">
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
            </span>
            System Online
          </div>
          <span className="text-xs font-mono bg-slate-800 px-2 py-1 rounded">v1.3.0</span>
        </div>
      </div>
    </motion.div>
  );
}
