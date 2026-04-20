"use client";

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import ReactMarkdown from 'react-markdown';
import { fetchReport } from '@/lib/api';
import Link from 'next/link';
import { ArrowLeft, Loader2 } from 'lucide-react';

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

  return (
    <div className="space-y-6 text-slate-800">
      <div className="flex items-center gap-4">
        <Link href="/targets" className="p-2 bg-slate-200 hover:bg-slate-300 rounded-full transition">
          <ArrowLeft size={20} />
        </Link>
        <h1 className="text-3xl font-bold">Vulnerability Report</h1>
      </div>

      <div className="bg-white p-8 rounded-xl border border-slate-200 shadow-sm min-h-[60vh] relative">
        {loading ? (
          <div className="flex items-center justify-center h-full absolute inset-0 text-slate-500">
            <Loader2 className="animate-spin mr-2" size={24} /> Generating Report...
          </div>
        ) : error ? (
          <div className="text-red-500 bg-red-50 p-4 rounded-lg border border-red-200">
            {error}
          </div>
        ) : report ? (
          <article className="prose prose-slate max-w-none prose-h1:text-red-600 prose-h2:text-blue-700 prose-a:text-blue-600">
            <ReactMarkdown>{report}</ReactMarkdown>
          </article>
        ) : null}
      </div>
    </div>
  );
}
