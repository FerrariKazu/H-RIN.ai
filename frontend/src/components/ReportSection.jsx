import React from 'react';

const ReportSection = ({ reportHtml }) => {
    if (!reportHtml) return null;

    const handleDownload = () => {
        const blob = new Blob([reportHtml], { type: 'text/html' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `HR_Report_Generated.html`;
        a.click();
    };

    return (
        <section id="report" className="mb-20 scroll-mt-20">
            <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <span className="text-indigo-400">📝</span> Final HR Report
            </h3>

            <div className="bg-slate-800 rounded-xl border border-slate-700 shadow-2xl overflow-hidden">
                <div className="p-4 bg-slate-900 border-b border-slate-700 flex justify-between items-center">
                    <span className="text-sm text-slate-400 font-mono">report_v2.5_final.html</span>
                    <button 
                        onClick={handleDownload}
                        className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium transition-colors"
                    >
                        <span>💾</span> Download PDF / HTML
                    </button>
                </div>
                
                <div className="relative w-full h-[800px] bg-white">
                    <iframe 
                        srcDoc={reportHtml}
                        title="Final HR Report"
                        className="absolute inset-0 w-full h-full border-0"
                        sandbox="allow-same-origin"
                    />
                </div>
            </div>
        </section>
    );
};

export default ReportSection;
