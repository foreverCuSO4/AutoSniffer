
import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';

/** --- Types & Enums --- **/
enum ViewMode {
  INSIDE = 'INSIDE',
  OUTSIDE = 'OUTSIDE'
}

/** --- Decorative Components --- **/
const OrnateCorner = ({ className = "" }) => (
  <svg className={`absolute ${className}`} width="120" height="120" viewBox="0 0 120 120" fill="none">
    <path d="M10 10 Q 40 10, 40 40 M10 10 Q 10 40, 40 40 M10 10 L 100 10 M10 10 L 10 100" stroke="#c5a059" strokeWidth="0.5" strokeOpacity="0.5" />
    <circle cx="40" cy="40" r="2" fill="#c5a059" fillOpacity="0.4" />
    <path d="M10 10 L 25 25" stroke="#c5a059" strokeWidth="0.5" strokeOpacity="0.3" />
  </svg>
);

const OrnateDivider = () => (
  <div className="flex items-center justify-center gap-6 my-8 opacity-60">
    <div className="h-[0.5px] w-20 bg-gradient-to-r from-transparent to-[#c5a059]"></div>
    <div className="relative">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" className="gear-spin">
        <path d="M12 2L14.5 9H21.5L16 13L18.5 20L12 16L5.5 20L8 13L2.5 9H9.5L12 2Z" stroke="#c5a059" strokeWidth="1" />
      </svg>
    </div>
    <div className="h-[0.5px] w-20 bg-gradient-to-l from-transparent to-[#c5a059]"></div>
  </div>
);

const FloatingParticle = ({ style }: { style: React.CSSProperties }) => (
  <div 
    className="absolute pointer-events-none opacity-10 floating"
    style={{
      width: '12px',
      height: '12px',
      border: '0.5px solid #c5a059',
      borderRadius: '2px',
      ...style
    }}
  />
);

const TechnicalFiligree = ({ className = "" }) => (
  <svg className={`absolute opacity-10 pointer-events-none ${className}`} width="200" height="200" viewBox="0 0 100 100">
    <circle cx="50" cy="50" r="45" stroke="currentColor" strokeWidth="0.2" fill="none" />
    <circle cx="50" cy="50" r="30" stroke="currentColor" strokeWidth="0.1" fill="none" strokeDasharray="1 2" />
    <path d="M50 5 L 50 15 M95 50 L 85 50 M50 95 L 50 85 M5 50 L 15 50" stroke="currentColor" strokeWidth="0.5" />
  </svg>
);

/** --- Icons --- **/
const FolderIcon = ({ className = "w-6 h-6" }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
  </svg>
);

const RobotIcon = ({ className = "w-6 h-6" }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
  </svg>
);

const MagicWandIcon = ({ className = "w-6 h-6" }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a2 2 0 00-1.96 1.414l-.477 2.387a2 2 0 00.547 1.022l1.428 1.428a2 2 0 001.022.547l2.387.477a2 2 0 001.96-1.414l.477-2.387a2 2 0 00-.547-1.022l-1.428-1.428z" />
  </svg>
);

const UndoIcon = ({ className = "w-6 h-6" }) => (
  <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
  </svg>
);

const AppLogo = ({ className = "w-16 h-16" }) => (
  <div className={`relative flex items-center justify-center rounded-2xl bg-amber-100 p-2 shadow-inner border border-amber-200 ${className}`}>
    <FolderIcon className="w-10 h-10 text-amber-700 opacity-30 absolute" />
    <RobotIcon className="w-8 h-8 text-amber-800 relative z-10" />
    <div className="absolute top-1 right-1 w-3 h-3 bg-green-400 rounded-full border-2 border-white"></div>
  </div>
);

/** --- Layout Components --- **/
const BrochurePanel: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className = "" }) => (
  <div className={`flex-1 min-w-[320px] max-w-[400px] h-[720px] glass rounded-[2.5rem] p-8 flex flex-col shadow-2xl relative overflow-hidden transition-all duration-700 hover:shadow-amber-900/15 border-2 border-amber-100/50 panel-enter ${className}`}>
    <OrnateCorner className="top-2 left-2" />
    <OrnateCorner className="top-2 right-2 rotate-90" />
    <OrnateCorner className="bottom-2 left-2 -rotate-90" />
    <OrnateCorner className="bottom-2 right-2 rotate-180" />
    <div className="relative z-10 flex flex-col h-full">{children}</div>
    <div className="absolute inset-0 flex items-center justify-center opacity-[0.03] pointer-events-none">
      <svg width="400" height="400" viewBox="0 0 100 100" fill="currentColor" className="text-amber-900"><path d="M50 0 C 60 40 100 50 60 60 C 50 100 40 60 0 50 C 40 40 50 0" /></svg>
    </div>
  </div>
);

/** --- Main App --- **/
const App: React.FC = () => {
  const [view, setView] = useState<ViewMode>(ViewMode.OUTSIDE);

  return (
    <div className="min-h-screen rococo-gradient flex flex-col items-center py-12 px-4 relative overflow-hidden">
      {/* Background Particles */}
      <FloatingParticle style={{ top: '15%', left: '10%', animationDelay: '0s' }} />
      <FloatingParticle style={{ top: '70%', left: '5%', animationDelay: '2.5s' }} />
      <FloatingParticle style={{ top: '25%', right: '12%', animationDelay: '1.2s' }} />
      <FloatingParticle style={{ top: '85%', right: '8%', animationDelay: '4s' }} />
      
      {/* Header */}
      <div className="mb-14 text-center relative z-20">
        <div className="logo-font text-amber-800/60 text-[10px] tracking-[0.5em] mb-4 uppercase">Elegant Design • Seamless Experience</div>
        <h1 className="title-font text-6xl font-black text-amber-950 mb-2 tracking-tight">AutoSniffer</h1>
        <p className="text-amber-800/50 italic text-xl serif-font mb-8">为您忙碌的数字生活，寻觅一处温柔归宿</p>
        
        <button 
          onClick={() => setView(v => v === ViewMode.OUTSIDE ? ViewMode.INSIDE : ViewMode.OUTSIDE)}
          className="group relative px-10 py-4 bg-amber-950 text-amber-50 rounded-full shadow-[0_15px_40px_rgba(74,55,40,0.3)] transition-all hover:scale-105 active:scale-95"
        >
          <div className="absolute inset-0 bg-gradient-to-r from-amber-800 to-amber-950 opacity-0 group-hover:opacity-100 transition-opacity rounded-full"></div>
          <span className="relative flex items-center gap-4 font-bold tracking-widest text-sm uppercase">
            {view === ViewMode.OUTSIDE ? "开启整理之旅" : "返回封面"}
            <svg className={`w-5 h-5 transition-transform duration-700 ${view === ViewMode.INSIDE ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
            </svg>
          </span>
        </button>
      </div>

      <div className="w-full max-w-[1300px] perspective-container">
        <div className="flex flex-wrap gap-8 justify-center transition-all duration-1000">
          {view === ViewMode.OUTSIDE ? (
            <>
              {/* BACK PANEL */}
              <BrochurePanel className="bg-amber-50/20">
                <div className="flex flex-col h-full p-2">
                  <div className="title-font text-[10px] text-amber-600 font-bold tracking-[0.3em] mb-4 uppercase">Running Specs</div>
                  <h2 className="text-2xl font-black text-amber-950 mb-6 flex items-center gap-3 italic">⚙️ 运行规格</h2>
                  <div className="space-y-4 text-xs text-amber-900/80 italic leading-relaxed">
                    <div className="p-4 bg-white/50 rounded-2xl border border-amber-200/30">
                      <p className="font-bold text-amber-950 mb-1">🚀 Windows 免安装</p>
                      <p>提供独立 <strong>.exe</strong> 应用程序，无需配置 Python 或任何依赖环境。下载即用，让技术回归纯粹的简单。</p>
                    </div>
                    <div className="p-4 bg-white/50 rounded-2xl border border-amber-200/30">
                      <p className="font-bold text-amber-950 mb-1">🧠 智慧大脑</p>
                      <p>深度适配 Qwen 系列等 OpenAI 协议接口模型。轻量、极速，为您提供毫秒级的语义识别反馈。</p>
                    </div>
                    <div className="p-4 bg-white/50 rounded-2xl border border-amber-200/30">
                      <p className="font-bold text-amber-950 mb-1">📄 全面理解</p>
                      <p>完美支持 PDF、Word 及各类图片。AI 像老朋友一样“读懂”您的文件内容并分门别类。</p>
                    </div>
                  </div>
                  <div className="mt-auto pt-10 border-t border-amber-200/50">
                    <h3 className="text-xl font-black text-amber-950 mb-4 italic">立刻获取</h3>
                    <div className="space-y-3">
                      <a href="https://github.com/foreverCuSO4/AutoSniffer/releases" className="block w-full py-4 bg-amber-950 text-amber-50 rounded-2xl text-center font-black tracking-widest shadow-xl hover:shadow-amber-900/30 transition-all hover:-translate-y-1">
                        下载 .exe 立刻使用
                      </a>
                    </div>
                  </div>
                </div>
              </BrochurePanel>

              {/* INSIDE FLAP */}
              <BrochurePanel className="bg-sky-50/20">
                <div className="flex flex-col h-full text-center">
                  <TechnicalFiligree className="text-sky-900 top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 opacity-[0.05]" />
                  <div className="title-font text-[10px] text-sky-600 font-bold tracking-[0.3em] mb-6 uppercase">Safe & Considerate</div>
                  <h2 className="text-2xl font-black text-sky-950 mb-10 italic">↩️ 细致的守护</h2>
                  <div className="space-y-6 flex-1">
                    <div className="p-6 bg-white/90 rounded-[2.5rem] border border-sky-100 shadow-sm">
                      <div className="text-xl font-bold mb-2 text-sky-950">无损撤销</div>
                      <p className="text-xs text-sky-900/70 italic leading-relaxed">
                        基于 .autosniffer_history 的详尽记录，您可随时“一键撤销”，将文件还原至整理前的状态。
                      </p>
                    </div>
                    <div className="p-6 bg-white/90 rounded-[2.5rem] border border-sky-100 shadow-sm">
                      <div className="text-xl font-bold mb-2 text-sky-950">隐私即尊严</div>
                      <p className="text-xs text-sky-900/70 italic leading-relaxed">
                        文件操作全程在本地闭环运行。仅上传摘要特征供 AI 理解，您的原始大文件从不离开您的硬盘。
                      </p>
                    </div>
                  </div>
                  <div className="mt-auto">
                    <OrnateDivider />
                    <p className="text-[10px] text-sky-800 font-black tracking-widest uppercase opacity-40 italic">Efficiency with Heart</p>
                  </div>
                </div>
              </BrochurePanel>

              {/* FRONT COVER */}
              <BrochurePanel className="bg-rose-50/30 border-amber-200">
                <div className="flex flex-col items-center text-center h-full pt-10">
                  <AppLogo className="w-44 h-44 mb-12 shadow-[0_20px_60px_rgba(197,160,89,0.3)]" />
                  <div className="logo-font text-amber-800 text-[11px] tracking-[0.6em] mb-4 uppercase opacity-50">Intelligent File Concierge</div>
                  <h1 className="title-font text-6xl font-black text-amber-950 mb-4 tracking-tighter">AutoSniffer</h1>
                  <h3 className="text-2xl font-medium text-amber-800/80 serif-font italic mb-10">智慧文件整理管家</h3>
                  <OrnateDivider />
                  <p className="text-amber-950 font-black text-2xl italic mb-6">让文件找到最合适的归宿</p>
                  <p className="text-sm text-amber-900/60 leading-relaxed px-10 serif-font italic">
                    融合前沿大模型智慧，为您打造优雅、有序的数字办公环境。<br/>一键运行的便捷，将繁琐交给 AI，将时间留给生命。
                  </p>
                  <div className="mt-auto pb-4">
                    <div className="px-10 py-2 bg-amber-950/5 border border-amber-200 rounded-full text-[9px] text-amber-900/60 font-black tracking-[0.4em] uppercase italic">
                      Windows Standalone .EXE
                    </div>
                  </div>
                </div>
              </BrochurePanel>
            </>
          ) : (
            <>
              {/* INSIDE LEFT */}
              <BrochurePanel className="bg-white/90">
                <div className="title-font text-[10px] text-rose-600 font-bold tracking-[0.3em] mb-8 uppercase">Common Pain Points</div>
                <h2 className="text-3xl font-black text-rose-950 mb-10 italic">您的桌面是否也曾让您烦心？</h2>
                <div className="space-y-10 mb-14 flex-1">
                  {[
                    { i: "📂", t: "混乱的下载目录", d: "成堆的文件堆积，手动分类一次需要耗费数小时。" },
                    { i: "🔍", t: "难以名状的文件", d: "“截图_1”或“新建文档”让查找变成大海捞针。" },
                    { i: "🤯", t: "分类的选择困难", d: "犹豫该按日期还是项目分类？这往往是杂乱的开始。" }
                  ].map((item, idx) => (
                    <div key={idx} className="flex gap-6 items-start">
                      <span className="text-3xl opacity-50">{item.i}</span>
                      <div>
                        <p className="font-black text-rose-900 text-xl mb-1">{item.t}</p>
                        <p className="text-sm text-rose-800/70 serif-font italic leading-snug">{item.d}</p>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="mt-auto bg-gradient-to-br from-rose-50 to-amber-50 p-8 rounded-[3rem] border border-rose-100 shadow-inner relative overflow-hidden group">
                  <TechnicalFiligree className="text-rose-900 -right-10 -bottom-10 opacity-[0.05]" />
                  <p className="text-rose-950 font-black mb-4 flex items-center gap-3">
                    <RobotIcon className="w-6 h-6" /> 它比以往任何工具都更懂您
                  </p>
                  <p className="text-xs text-rose-900/70 leading-relaxed italic">
                    AutoSniffer 利用 <strong>LLM 多模态 AI</strong>，能领会文档深意，看懂图片内涵，为您提供极具逻辑的分类方案。
                  </p>
                </div>
              </BrochurePanel>

              {/* INSIDE CENTER */}
              <BrochurePanel className="bg-amber-50/10">
                <div className="title-font text-[10px] text-amber-700 font-bold tracking-[0.3em] mb-6 uppercase text-center">Core Wisdom</div>
                <h2 className="text-3xl font-black text-amber-950 mb-10 text-center flex items-center justify-center gap-4 italic">✨ 核心整理智慧</h2>
                <div className="space-y-10 flex-1">
                  <section className="relative pl-14">
                    <div className="absolute left-0 top-1 text-amber-500 opacity-20"><FolderIcon className="w-12 h-12" /></div>
                    <h4 className="font-black text-amber-950 text-xl mb-2">🧭 两阶段专业归档</h4>
                    <p className="text-xs text-amber-900/80 italic leading-relaxed">
                      <strong>第一阶段：</strong>深度扫描目录，为您生成完美的分类建议预览。<br/>
                      <strong>第二阶段：</strong>确认无误后，AI 会自动批量将成百上千个文件精准归位。
                    </p>
                  </section>
                  <section className="relative pl-14">
                    <div className="absolute left-0 top-1 text-sky-500 opacity-20"><MagicWandIcon className="w-12 h-12" /></div>
                    <h4 className="font-black text-sky-950 text-xl mb-2">🏷️ 语义智能重命名</h4>
                    <p className="text-xs text-sky-900/80 italic leading-relaxed">
                      <strong>文档：</strong>依据 PDF/Word 摘要生成描述性前缀。<br/>
                      <strong>图片：</strong>运用多模态模型描述画面内容，让文件从此有名有姓。
                    </p>
                  </section>
                  <section className="relative pl-14">
                    <div className="absolute left-0 top-1 text-emerald-500 opacity-20"><UndoIcon className="w-12 h-12" /></div>
                    <h4 className="font-black text-emerald-950 text-xl mb-2">↩️ 随时回滚的从容</h4>
                    <p className="text-xs text-emerald-900/80 italic leading-relaxed">
                      整理结果不合心意？点击撤销，一切即刻尽可能还原如初。
                    </p>
                  </section>
                </div>
                <div className="mt-auto pt-10 flex flex-col items-center">
                   <div className="px-10 py-3 border-2 border-amber-200 rounded-full text-amber-900 text-[10px] font-black tracking-widest uppercase italic bg-white/60 shadow-sm mb-4">
                     Experience the Future of Productivity
                   </div>
                   <p className="text-[10px] text-amber-800/40 font-bold italic">“秩序，让生活更从容”</p>
                </div>
              </BrochurePanel>

              {/* INSIDE RIGHT */}
              <BrochurePanel className="bg-white/90">
                <div className="title-font text-[10px] text-amber-700 font-bold tracking-[0.3em] mb-8 uppercase">User Guide</div>
                <h2 className="text-2xl font-black text-amber-950 mb-12 italic text-center">简单五步，开启清爽生活</h2>
                <div className="space-y-8 relative flex-1">
                  <div className="absolute left-6 top-6 bottom-6 w-[0.5px] bg-gradient-to-b from-amber-300 via-amber-100 to-transparent"></div>
                  {[
                    { n: "1", t: "基础配置", d: "双击 .exe 启动，在设置页填入您的 API Key。", c: "bg-rose-100 text-rose-800" },
                    { n: "2", t: "选取目录", d: "选择您需要整理的杂乱文件夹，点击‘扫描’。", c: "bg-sky-100 text-sky-800" },
                    { n: "3", t: "分析规划", d: "让 AI 为您生成分类建议，您可以根据需求微调。", c: "bg-amber-200 text-amber-900" },
                    { n: "4", t: "确认执行", d: "一键开启自动化整理流程，静待文件有序归位。", c: "bg-amber-950 text-white shadow-lg" },
                    { n: "5", t: "自由微调", d: "如有需要，可使用撤销或智能重命名功能。", c: "bg-emerald-100 text-emerald-800" }
                  ].map((step, idx) => (
                    <div key={idx} className="relative pl-16 group cursor-default">
                      <div className={`absolute left-0 top-0 w-10 h-10 ${step.c} rounded-full flex items-center justify-center font-black text-xs shadow-md group-hover:scale-125 transition-all duration-500`}>{step.n}</div>
                      <p className="font-black text-amber-950 text-lg mb-1">{step.t}</p>
                      <p className="text-xs text-amber-800/60 italic leading-relaxed">{step.d}</p>
                    </div>
                  ))}
                </div>
                <div className="mt-auto pt-10 text-center">
                   <p className="text-[10px] text-amber-800/30 font-black tracking-[0.4em] uppercase italic">Designed for Microsoft Windows</p>
                </div>
              </BrochurePanel>
            </>
          )}
        </div>
      </div>

      <footer className="mt-20 text-center relative z-20">
        <OrnateDivider />
        <p className="title-font text-amber-950/20 text-[10px] font-black tracking-[0.5em] uppercase italic">
          © 2025 AutoSniffer • Made by Jiayi Zhu, Ming Chen, Hangyu Tong, Zehui Liu • All Rights Reserved
        </p>
      </footer>
    </div>
  );
};

// Render logic
const rootElement = document.getElementById('root');
if (rootElement) {
  createRoot(rootElement).render(<App />);
}
