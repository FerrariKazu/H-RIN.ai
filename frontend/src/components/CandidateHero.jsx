import React from 'react';

const CandidateHero = ({ structuredData, mlResult }) => {
    if (!structuredData) return null;

    const name = structuredData.name || "Unknown Candidate";
    const role = mlResult?.recommended_roles?.[0] || "Applicant";
    const exp = structuredData.total_experience_years || structuredData.experience?.length || 0;
    const score = mlResult?.predicted_ai_score || 0;
    
    // Determine badge color based on score
    let badgeColor = "bg-red-500/10 text-red-400 border-red-500/20";
    if (score >= 70) badgeColor = "bg-green-500/10 text-green-400 border-green-500/20";
    else if (score >= 40) badgeColor = "bg-amber-500/10 text-amber-400 border-amber-500/20";

    return (
        <div id="overview" className="bg-slate-800 rounded-xl border border-slate-700 p-8 mb-6 shadow-lg relative overflow-hidden">
            <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/10 rounded-full blur-3xl -mr-16 -mt-16 pointer-events-none"></div>

            <div className="flex flex-col md:flex-row justify-between items-start md:items-center relative z-10">
                <div className="flex items-center gap-6">
                    <div className="w-20 h-20 rounded-full bg-slate-700 flex items-center justify-center text-3xl shadow-inner border border-slate-600">
                        {name.charAt(0)}
                    </div>
                    <div>
                        <h2 className="text-3xl font-bold text-white tracking-tight">{name}</h2>
                        <div className="flex items-center gap-4 mt-2 text-slate-400 text-sm">
                            <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-700/50 border border-slate-600/50">
                                💼 {role}
                            </span>
                            <span className="flex items-center gap-1.5">
                                📅 {exp} Years Exp
                            </span>
                            {structuredData.contact_info?.location && (
                                <span className="flex items-center gap-1.5">
                                    📍 {structuredData.contact_info.location}
                                </span>
                            )}
                        </div>
                    </div>
                </div>

                <div className="mt-6 md:mt-0 flex flex-col items-end">
                    <div className={`px-4 py-2 rounded-lg border ${badgeColor} backdrop-blur-sm flex flex-col items-center min-w-[120px]`}>
                        <span className="text-xs font-semibold uppercase tracking-wider opacity-80">Resume Score</span>
                        <span className="text-3xl font-bold">{Math.round(score)}</span>
                    </div>
                    <div className="mt-3 flex gap-3">
                        {structuredData.contact_info?.email && (
                            <a href={`mailto:${structuredData.contact_info.email}`} className="p-2 rounded-lg bg-slate-700 text-slate-300 hover:bg-indigo-600 hover:text-white transition-colors">
                                ✉️
                            </a>
                        )}
                        {structuredData.contact_info?.phone && (
                            <a href={`tel:${structuredData.contact_info.phone}`} className="p-2 rounded-lg bg-slate-700 text-slate-300 hover:bg-green-600 hover:text-white transition-colors">
                                📞
                            </a>
                        )}
                        {structuredData.contact_info?.linkedin && (
                            <a href={structuredData.contact_info.linkedin} target="_blank" className="p-2 rounded-lg bg-slate-700 text-slate-300 hover:bg-blue-600 hover:text-white transition-colors">
                                🔗
                            </a>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default CandidateHero;
