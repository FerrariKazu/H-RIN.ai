import React from 'react';

const StructuredDataSection = ({ structuredData }) => {
    if (!structuredData) return null;

    const SectionCard = ({ title, icon, children }) => (
        <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden mb-4">
            <div className="bg-slate-900/50 px-6 py-3 border-b border-slate-700 flex items-center gap-2">
                <span>{icon}</span>
                <h4 className="font-semibold text-slate-200">{title}</h4>
            </div>
            <div className="p-6">{children}</div>
        </div>
    );

    return (
        <section id="structured" className="mb-8 scroll-mt-20">
            <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <span className="text-indigo-400">🧠</span> Structured Data (LLM)
            </h3>

            {/* Professional Experience */}
            <SectionCard title="Professional Experience" icon="💼">
                {structuredData.experience?.length > 0 ? (
                    <div className="space-y-6">
                        {structuredData.experience.map((job, idx) => (
                            <div key={idx} className="relative pl-6 border-l-2 border-slate-700 last:border-0">
                                <span className="absolute -left-[9px] top-0 w-4 h-4 rounded-full bg-slate-700 border-2 border-slate-800"></span>
                                <div className="flex flex-col md:flex-row md:justify-between md:items-start mb-2">
                                    <div>
                                        <h5 className="text-lg font-bold text-white">{job.title || "Unknown Role"}</h5>
                                        <div className="text-indigo-400">{job.company || "Unknown Company"}</div>
                                    </div>
                                    <div className="text-sm text-slate-400 font-mono bg-slate-700/50 px-2 py-1 rounded">
                                        {job.duration || job.years + " Years" || "N/A"}
                                    </div>
                                </div>
                                <p className="text-slate-400 text-sm leading-relaxed whitespace-pre-line">
                                    {job.description || "No description provided."}
                                </p>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="text-slate-500 italic">No experience detected.</div>
                )}
            </SectionCard>

            {/* Education */}
            <SectionCard title="Education" icon="🎓">
                {structuredData.education?.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {structuredData.education.map((edu, idx) => (
                            <div key={idx} className="bg-slate-700/30 p-4 rounded-lg border border-slate-600/50">
                                <div className="font-bold text-white">{edu.degree || "Degree"}</div>
                                <div className="text-sm text-indigo-300">{edu.institution || "Institution"}</div>
                                <div className="text-xs text-slate-500 mt-2">{edu.year || "Year N/A"}</div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="text-slate-500 italic">No education detected.</div>
                )}
            </SectionCard>

            {/* Projects */}
            {structuredData.projects?.length > 0 && (
                <SectionCard title="Key Projects" icon="🚀">
                    <div className="space-y-4">
                        {structuredData.projects.map((proj, idx) => (
                            <div key={idx} className="group">
                                <div className="flex justify-between items-baseline mb-1">
                                    <h5 className="font-medium text-slate-200 group-hover:text-indigo-400 transition-colors">
                                        {proj.name || "Project"}
                                    </h5>
                                    {proj.technologies && (
                                        <div className="text-xs text-slate-500">{proj.technologies.join(', ')}</div>
                                    )}
                                </div>
                                <p className="text-sm text-slate-400">{proj.description}</p>
                            </div>
                        ))}
                    </div>
                </SectionCard>
            )}
        </section>
    );
};

export default StructuredDataSection;
