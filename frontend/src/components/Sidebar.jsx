import React from 'react';

const Sidebar = ({ activeSection, scrollToSection }) => {
    const navItems = [
        { id: 'overview', label: 'Candidate Overview', icon: '👤' },
        { id: 'nlp', label: 'NLP Extraction', icon: '🔍' },
        { id: 'structured', label: 'Structured Data', icon: '🧠' },
        { id: 'ml', label: 'ML Evaluation', icon: '🤖' },
        { id: 'report', label: 'HR Report', icon: '📝' },
        { id: 'logs', label: 'Pipeline Logs', icon: '⚙️' },
    ];

    return (
        <div className="w-64 bg-slate-900 h-screen fixed left-0 top-0 text-white flex flex-col shadow-xl z-50">
            <div className="p-6 border-b border-slate-800">
                <h1 className="text-2xl font-bold bg-gradient-to-r from-indigo-400 to-cyan-400 bg-clip-text text-transparent">
                    HR Buddy
                </h1>
                <p className="text-xs text-slate-500 mt-1 uppercase tracking-wider">AI Evaluation Platform</p>
            </div>

            <nav className="flex-1 overflow-y-auto py-6">
                <ul className="space-y-1 px-3">
                    {navItems.map((item) => (
                        <li key={item.id}>
                            <button
                                onClick={() => scrollToSection(item.id)}
                                className={`w-full flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-all duration-200
                                    ${activeSection === item.id 
                                        ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30' 
                                        : 'text-slate-400 hover:bg-slate-800 hover:text-white'
                                    }
                                `}
                            >
                                <span className="mr-3 text-lg">{item.icon}</span>
                                {item.label}
                            </button>
                        </li>
                    ))}
                </ul>
            </nav>

            <div className="p-4 border-t border-slate-800 bg-slate-950/50">
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 flex items-center justify-center font-bold text-xs">
                        AI
                    </div>
                    <div>
                        <p className="text-sm font-medium text-white">System Ready</p>
                        <p className="text-xs text-green-500 flex items-center gap-1">
                            <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                            Online
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Sidebar;
