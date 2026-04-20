"use client";

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import ReactMarkdown from 'react-markdown';
import { fetchReport } from '@/lib/api';
import Link from 'next/link';
import { ArrowLeft, Loader2, Download, ExternalLink, ShieldCheck } from 'lucide-react';
import { motion } from 'framer-motion';

export default function ReportPage() {
  const params = useParams();
  const id = params?.id as string;
  const [report, setReport] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadReport = async () => {
      try {
        const data = await fetchReport(Number(id));
        setReport(data.markdown_report);
      } catch (err) {
        setError("Report not found or hasn't been generated yet for this target.");
      } finally {
        setLoading(false);
      }
    };
    if (id) {
        loadReport();
    }
  }, [id]);

  const handleExport = () => {
    if (!report) return;
    const blob = new Blob([report], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `xforge-report-${id}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6 text-slate-800 pb-20">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/targets" className="p-2 bg-white border border-slate-200 hover:bg-slate-50 hover:text-blue-600 rounded-full transition shadow-sm">
            <ArrowLeft size={20} />
          </Link>
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-3">
              Vulnerability Report
            </h1>
            <p className="text-slate-500 mt-1">Detailed findings for Target ID #{id}</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleExport}
            disabled={!report || loading}
            className="flex items-center gap-2 bg-slate-900 text-white px-4 py-2 rounded-lg font-medium hover:bg-slate-800 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Download size={18} /> Export MD
          </button>
        </div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white p-10 rounded-2xl border border-slate-200 shadow-sm min-h-[60vh] relative"
      >
        {loading ? (
          <div className="flex flex-col items-center justify-center h-[50vh] text-slate-500">
            <Loader2 className="animate-spin mb-4 text-blue-500" size={40} />
            <p className="font-medium text-lg">Assembling intelligence report...</p>
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center h-[50vh] text-slate-500">
            <ShieldCheck size={48} className="text-slate-300 mb-4" />
            <p className="text-lg font-medium text-slate-600">{error}</p>
            <p className="text-sm mt-2">Trigger a scan from the targets page to populate this report.</p>
          </div>
        ) : report ? (
          <article className="prose prose-slate max-w-none
            prose-headings:border-b prose-headings:border-slate-100 prose-headings:pb-2
            prose-h1:text-3xl prose-h1:font-extrabold prose-h1:text-slate-900 prose-h1:mb-8
            prose-h2:text-2xl prose-h2:font-bold prose-h2:text-blue-700 prose-h2:mt-12
            prose-h3:text-xl prose-h3:font-semibold prose-h3:text-slate-800
            prose-a:text-blue-600 prose-a:no-underline hover:prose-a:underline
            prose-code:text-red-600 prose-code:bg-red-50 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:before:content-none prose-code:after:content-none
            prose-pre:bg-slate-900 prose-pre:text-slate-50 prose-pre:shadow-lg prose-pre:rounded-xl
            prose-strong:text-slate-900 prose-strong:font-bold
            prose-blockquote:border-l-4 prose-blockquote:border-blue-500 prose-blockquote:bg-blue-50 prose-blockquote:py-1 prose-blockquote:px-4 prose-blockquote:not-italic prose-blockquote:rounded-r-lg
            prose-li:marker:text-blue-500
          ">
            <ReactMarkdown
              components={{
                a: ({ node, ...props }) => (
                  <a target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1" {...props}>
                    {props.children} <ExternalLink size={12} />
                  </a>
                ),
              }}
            >
              {report}
            </ReactMarkdown>
          </article>
        ) : null}
      </motion.div>
    </div>
  );
}
