import Link from 'next/link';
import { Target, Activity, FileText } from 'lucide-react';

export default function Sidebar() {
  return (
    <div className="w-64 h-full bg-slate-900 text-white flex flex-col fixed left-0 top-0">
      <div className="p-6">
        <h1 className="text-2xl font-bold text-red-500 tracking-wider">XFORGE</h1>
        <p className="text-xs text-slate-400 mt-1">Autonomous Security</p>
      </div>
      <nav className="flex-1 px-4 space-y-2 mt-4">
        <Link href="/targets" className="flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-slate-800 transition-colors text-slate-300 hover:text-white">
          <Target size={20} />
          <span>Targets</span>
        </Link>
        <Link href="/tasks" className="flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-slate-800 transition-colors text-slate-300 hover:text-white">
          <Activity size={20} />
          <span>Active Tasks</span>
        </Link>
        <Link href="/reports" className="flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-slate-800 transition-colors text-slate-300 hover:text-white">
          <FileText size={20} />
          <span>Reports</span>
        </Link>
      </nav>
      <div className="p-4 border-t border-slate-800">
        <div className="flex items-center gap-2 text-sm text-slate-400">
          <div className="w-2 h-2 rounded-full bg-green-500"></div>
          System Online
        </div>
      </div>
    </div>
  );
}
