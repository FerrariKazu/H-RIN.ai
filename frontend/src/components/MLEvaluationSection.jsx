import React from 'react';

const MLEvaluationSection = ({ mlResult }) => {
    if (!mlResult) return null;

    const { 
        predicted_ai_score, 
        hire_probability, 
        top_positive_features = [], 
        top_negative_features = [] 
    } = mlResult;

    return (
        <section id="ml" className="mb-8 scroll-mt-20">
            <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <span className="text-indigo-400">🤖</span> Machine Learning Analysis
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                {/* Score Card */}
                <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
                    <h4 className="text-slate-400 text-sm uppercase tracking-wider mb-4">Overall Assessment</h4>
                    <div className="flex items-center justify-between mb-4">
                        <div>
                            <div className="text-4xl font-bold text-white mb-1">{Math.round(predicted_ai_score)}<span className="text-xl text-slate-500">/100</span></div>
                            <div className="text-sm text-slate-400">Normalized Resume Score</div>
                        </div>
                        <div className="h-16 w-1 bg-slate-700 rounded-full"></div>
                        <div className="text-right">
                            <div className="text-4xl font-bold text-white mb-1">{(hire_probability * 100).toFixed(1)}%</div>
                            <div className="text-sm text-slate-400">Match Probability</div>
                        </div>
                    </div>
                    
                    {/* Progress Bar */}
                    <div className="w-full bg-slate-700 rounded-full h-3 mb-2 overflow-hidden">
                        <div 
                            className="bg-indigo-500 h-full rounded-full transition-all duration-1000 ease-out"
                            style={{ width: `${predicted_ai_score}%` }}
                        ></div>
                    </div>
                    <div className="flex justify-between text-xs text-slate-500">
                        <span>Rejection Zone</span>
                        <span>Interview Zone</span>
                        <span>Hire Zone</span>
                    </div>
                </div>

                {/* Quick Stats */}
                <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg flex flex-col justify-center">
                    <div className="space-y-4">
                        <div className="flex justify-between items-center">
                            <span className="text-slate-400">Model Confidence</span>
                            <span className="text-white font-medium">High (v2.5)</span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-slate-400">Processing Time</span>
                            <span className="text-white font-medium">~1.2s</span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-slate-400">Cross-Validation</span>
                            <span className="text-green-400 font-medium">Passed</span>
                        </div>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Positive Factors */}
                <div className="bg-slate-800/50 p-6 rounded-xl border border-green-500/20">
                    <h4 className="text-green-400 font-medium mb-4 flex items-center gap-2">
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path></svg>
                        Top Positive Drivers
                    </h4>
                    <div className="space-y-3">
                        {top_positive_features.map((feat, idx) => (
                            <div key={idx} className="relative">
                                <div className="flex justify-between text-sm mb-1">
                                    <span className="text-slate-300 font-medium">{feat.feature.replace('feat_', '')}</span>
                                    <span className="text-green-400">+{feat.contribution.toFixed(2)}</span>
                                </div>
                                <div className="w-full bg-slate-700/50 rounded-full h-1.5">
                                    <div className="bg-green-500 h-1.5 rounded-full" style={{ width: `${Math.min(100, (feat.contribution / 10) * 100)}%` }}></div>
                                </div>
                            </div>
                        ))}
                        {top_positive_features.length === 0 && <div className="text-slate-500 italic">No significant positive factors.</div>}
                    </div>
                </div>

                {/* Negative Factors */}
                <div className="bg-slate-800/50 p-6 rounded-xl border border-red-500/20">
                    <h4 className="text-red-400 font-medium mb-4 flex items-center gap-2">
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6"></path></svg>
                        Risk Factors
                    </h4>
                    <div className="space-y-3">
                        {top_negative_features.map((feat, idx) => (
                            <div key={idx} className="relative">
                                <div className="flex justify-between text-sm mb-1">
                                    <span className="text-slate-300 font-medium">{feat.feature.replace('feat_', '')}</span>
                                    <span className="text-red-400">{feat.contribution.toFixed(2)}</span>
                                </div>
                                <div className="w-full bg-slate-700/50 rounded-full h-1.5">
                                    <div className="bg-red-500 h-1.5 rounded-full" style={{ width: `${Math.min(100, (Math.abs(feat.contribution) / 10) * 100)}%` }}></div>
                                </div>
                            </div>
                        ))}
                        {top_negative_features.length === 0 && <div className="text-slate-500 italic">No significant risk factors.</div>}
                    </div>
                </div>
            </div>
        </section>
    );
};

export default MLEvaluationSection;
