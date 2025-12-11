import React from 'react';

const NLPSection = ({ nlpData }) => {
    if (!nlpData) return null;

    const { skills_detected = [], ner_entities = {} } = nlpData;

    return (
        <section id="nlp" className="mb-8 scroll-mt-20">
            <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <span className="text-indigo-400">🔍</span> NLP Entity Extraction
            </h3>

            <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden shadow-lg">
                <div className="p-6 border-b border-slate-700 bg-slate-800/50">
                    <h4 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Detected Skills</h4>
                    <div className="flex flex-wrap gap-2">
                        {skills_detected.length > 0 ? (
                            skills_detected.map((skill, idx) => (
                                <span key={idx} className="px-2.5 py-1 rounded-md text-sm font-medium bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
                                    {skill}
                                </span>
                            ))
                        ) : (
                            <span className="text-slate-500 italic">No skills explicitly detected via NLP.</span>
                        )}
                    </div>
                </div>

                <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
                    {Object.entries(ner_entities).map(([label, entities]) => (
                        entities.length > 0 && (
                            <div key={label}>
                                <h4 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-2 border-b border-slate-700 pb-1">
                                    {label}
                                </h4>
                                <ul className="space-y-1">
                                    {entities.slice(0, 5).map((ent, idx) => (
                                        <li key={idx} className="text-slate-300 text-sm truncate" title={ent}>
                                            • {ent}
                                        </li>
                                    ))}
                                    {entities.length > 5 && (
                                        <li className="text-xs text-slate-500 italic">+{entities.length - 5} more...</li>
                                    )}
                                </ul>
                            </div>
                        )
                    ))}
                </div>
            </div>
        </section>
    );
};

export default NLPSection;
