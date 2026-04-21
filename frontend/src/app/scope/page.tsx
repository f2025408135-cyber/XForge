"use client";

import { useEffect, useState, useRef, useCallback } from 'react';
import dynamic from 'next/dynamic';
import { fetchTargetScope, fetchTargets } from '@/lib/api';
import { Network, Loader2, Maximize2 } from 'lucide-react';
import { motion } from 'framer-motion';

// ForceGraph2D requires document/window, so it must be dynamically imported with SSR disabled
const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), { ssr: false });

type GraphData = {
  nodes: { id: string; name: string; group: number; val: number }[];
  links: { source: string; target: string }[];
};

export default function ScopeGraphPage() {
  const [data, setData] = useState<GraphData | null>(null);
  const [targets, setTargets] = useState<any[]>([]);
  const [activeTarget, setActiveTarget] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const fgRef = useRef<any>(null);

  useEffect(() => {
    async function loadTargets() {
      try {
        const t = await fetchTargets();
        setTargets(t);
        if (t.length > 0) {
          setActiveTarget(t[0].id);
        }
      } catch (e) {
        console.error(e);
      }
    }
    loadTargets();
  }, []);

  useEffect(() => {
    if (!activeTarget) return;

    async function loadGraph() {
      setLoading(true);
      try {
        const scope = await fetchTargetScope(activeTarget!);
        setData(scope);
      } catch (e) {
        console.error(e);
        setData(null);
      } finally {
        setLoading(false);
      }
    }
    loadGraph();
  }, [activeTarget]);

  // Center graph on load
  useEffect(() => {
    if (data && fgRef.current) {
      setTimeout(() => {
        fgRef.current.zoomToFit(400, 50);
      }, 500);
    }
  }, [data]);

  const handleNodeClick = useCallback((node: any) => {
    if (fgRef.current) {
      fgRef.current.centerAt(node.x, node.y, 1000);
      fgRef.current.zoom(4, 1000);
    }
  }, []);

  return (
    <div className="space-y-6 h-[calc(100vh-6rem)] flex flex-col">
      <div className="flex justify-between items-center shrink-0">
        <h1 className="text-3xl font-bold flex items-center gap-3 text-slate-800">
          <Network size={32} className="text-blue-600" /> Attack Scope Graph
        </h1>

        <div className="flex items-center gap-3">
          <span className="text-sm font-medium text-slate-500">Target Context:</span>
          <select
            className="bg-white border border-slate-200 text-slate-700 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2.5 shadow-sm"
            value={activeTarget || ''}
            onChange={(e) => setActiveTarget(Number(e.target.value))}
          >
            {targets.map(t => (
              <option key={t.id} value={t.id}>{t.domain}</option>
            ))}
          </select>
        </div>
      </div>

      <motion.div
        initial={{ opacity: 0, scale: 0.98 }}
        animate={{ opacity: 1, scale: 1 }}
        className="flex-1 bg-slate-900 rounded-2xl border border-slate-800 shadow-2xl overflow-hidden relative"
      >
        {loading ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-900/80 z-10 text-white">
            <Loader2 className="animate-spin mb-4 text-blue-500" size={40} />
            <p className="font-medium text-lg tracking-widest uppercase">Mapping Infrastructure...</p>
          </div>
        ) : data && data.nodes.length > 0 ? (
          <>
            <button
              className="absolute top-4 right-4 z-10 p-2 bg-slate-800/80 hover:bg-slate-700 text-white rounded-lg backdrop-blur shadow-lg transition"
              onClick={() => fgRef.current?.zoomToFit(400, 50)}
              title="Reset View"
            >
              <Maximize2 size={20} />
            </button>
            <ForceGraph2D
              ref={fgRef}
              graphData={data}
              nodeLabel="name"
              nodeColor={node => {
                if (node.group === 1) return '#ef4444'; // Target Root
                if (node.group === 2) return '#3b82f6'; // Subdomains
                return '#10b981'; // Ports
              }}
              nodeRelSize={6}
              linkColor={() => 'rgba(255,255,255,0.2)'}
              backgroundColor="#0f172a"
              onNodeClick={handleNodeClick}
              nodeCanvasObject={(node: any, ctx, globalScale) => {
                const label = node.name;
                const fontSize = 12/globalScale;
                ctx.font = `${fontSize}px Sans-Serif`;
                const textWidth = ctx.measureText(label).width;
                const bckgDimensions = [textWidth, fontSize].map(n => n + fontSize * 0.2);

                ctx.fillStyle = 'rgba(15, 23, 42, 0.8)';
                ctx.fillRect(node.x - bckgDimensions[0] / 2, node.y + node.val - 2, bckgDimensions[0], bckgDimensions[1]);

                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillStyle = '#f8fafc';
                ctx.fillText(label, node.x, node.y + node.val + fontSize/2);

                // Draw Node
                ctx.beginPath();
                ctx.arc(node.x, node.y, node.val, 0, 2 * Math.PI, false);
                ctx.fillStyle = node.color;
                ctx.fill();
              }}
            />
          </>
        ) : (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-500">
            <Network size={64} className="mb-4 opacity-20" />
            <p className="text-xl font-medium">No scope data available</p>
            <p className="text-sm mt-2">Trigger a scan on this target to map subdomains and ports.</p>
          </div>
        )}
      </motion.div>
    </div>
  );
}
