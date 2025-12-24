
import React, { useState } from 'react';
import { ViewMode } from './types';
import BrochurePanel from './components/BrochurePanel';
import { Logo, FolderIcon, RobotIcon, MagicWandIcon, UndoIcon } from './components/Icons';
import { OrnateDivider, FloatingParticle, TechnicalFiligree } from './components/Decorations';

const App: React.FC = () => {
  const [view, setView] = useState<ViewMode>(ViewMode.OUTSIDE);

  const toggleView = () => {
    setView(prev => prev === ViewMode.OUTSIDE ? ViewMode.INSIDE : ViewMode.OUTSIDE);
  };

  return (
    <div className="min-h-screen rococo-gradient flex flex-col items-center py-12 px-4 relative overflow-hidden">
      {/* Ornate Particles */}
      <FloatingParticle style={{ top: '15%', left: '10%', animationDelay: '0s' }} />
      <FloatingParticle style={{ top: '70%', left: '5%', animationDelay: '2.5s' }} />
      <FloatingParticle style={{ top: '25%', right: '12%', animationDelay: '1.2s' }} />
      <FloatingParticle style={{ top: '85%', right: '8%', animationDelay: '4s' }} />
      
      {/* Header */}
      <div className="mb-14 text-center relative z-20">
        <div className="logo-font text-amber-800/60 text-[10px] tracking-[0.5em] mb-4 uppercase">Elegant Design • Seamless Experience</div>
        <h1 className="title-font text-6xl font-black text-amber-950 mb-4 tracking-tight">AutoSniffer</h1>
        <p className="text-amber-800/50 italic text-xl serif-font mb-8">为您忙碌的数字生活，寻觅一处温柔归宿</p>
        
        <button 
          onClick={toggleView}
          className="group relative px-10 py-4 bg-amber-950 text-amber-50 rounded-full shadow-[0_15px_40px_rgba(74,55,40,0.3)] transition-all hover:scale-105 active:scale-95"
        >
          <div className="absolute inset-0 bg-gradient-to-r from-amber-800 to-amber-950 opacity-0 group-hover:opacity-100 transition-opacity"></div>
          <span className="relative flex items-center gap-4 font-bold tracking-widest text-sm text-amber-50">
            {view === ViewMode.OUTSIDE ? "开启整理之旅 (Explore More)" : "返回封面 (Back to Cover)"}
            <svg className={`w-5 h-5 transition-transform duration-700 ${view === ViewMode.INSIDE ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
            </svg>
          </span>
        </button>
      </div>

      <div className="w-full max-w-[1300px] perspective-container">
        <div className={`flex flex-wrap gap-8 justify-center transition-all duration-1000 ease-in-out`}>
          
          {view === ViewMode.OUTSIDE ? (
            <>
              {/* BACK PANEL (Panel 5: Specs & Download) */}
              <BrochurePanel className="bg-amber-50/20">
                <div className="flex flex-col h-full scroll-shadow p-2">
                  <div className="title-font text-[10px] text-amber-600 font-bold tracking-[0.3em] mb-4 uppercase">Technical Excellence</div>
                  <h2 className="text-2xl font-black text-amber-950 mb-6 flex items-center gap-3">
                    <span className="bg-amber-100 p-1 rounded-lg">⚙️</span> 运行规格
                  </h2>
                  <div className="space-y-4 text-xs text-amber-900/80 italic leading-relaxed">
                    <div className="p-4 bg-white/50 rounded-2xl border border-amber-200/30">
                      <p className="font-bold text-amber-950 mb-1">🚀 Windows 免安装</p>
                      <p>提供独立 <strong>.exe</strong> 应用程序，无需配置 Python 环境。下载即可一键运行，让技术回归简单与纯粹。</p>
                    </div>
                    <div className="p-4 bg-white/50 rounded-2xl border border-amber-200/30">
                      <p className="font-bold text-amber-950 mb-1">🧠 模型支持</p>
                      <p>深度兼容 OpenAI 协议。推荐使用阿里云 DashScope/Qwen 系列大模型，享受毫秒级的语义识别反馈。</p>
                    </div>
                    <div className="p-4 bg-white/50 rounded-2xl border border-amber-200/30">
                      <p className="font-bold text-amber-950 mb-1">📂 全面支持</p>
                      <p>无论是 PDF 汇报、Word 提案，还是海量工作照片，均能获得最细腻的理解与分类。</p>
                    </div>
                  </div>

                  <div className="mt-auto pt-10 border-t border-amber-200/50">
                    <div className="mb-6">
                      <p className="text-[10px] font-bold text-amber-500 uppercase tracking-widest mb-1">Get Started</p>
                      <h3 className="text-xl font-black text-amber-950">获取与体验</h3>
                    </div>
                    <div className="space-y-3">
                      <a href="https://github.com/foreverCuSO4/AutoSniffer" className="flex items-center justify-between p-4 bg-white border border-amber-200 rounded-2xl hover:bg-amber-50 transition-all shadow-sm group">
                        <span className="text-xs font-mono text-amber-800">访问项目开源仓库</span>
                        <svg className="w-4 h-4 text-amber-400 group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3" /></svg>
                      </a>
                      <a href="https://github.com/foreverCuSO4/AutoSniffer/releases" className="block w-full py-4 bg-amber-950 text-amber-50 rounded-2xl text-center font-black tracking-widest shadow-xl hover:shadow-amber-900/30 transition-all hover:-translate-y-1">
                        下载 .exe 立刻使用
                      </a>
                    </div>
                  </div>
                </div>
              </BrochurePanel>

              {/* INSIDE FLAP (Panel 6: Undo & Privacy) */}
              <BrochurePanel className="bg-sky-50/20">
                <div className="flex flex-col h-full text-center">
                  <TechnicalFiligree className="text-sky-900 top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 opacity-[0.05]" />
                  <div className="title-font text-[10px] text-sky-600 font-bold tracking-[0.3em] mb-6 uppercase">Safe & Reliable</div>
                  <h2 className="text-2xl font-black text-sky-950 mb-10 italic">↩️ 安全与细致守护</h2>
                  
                  <div className="space-y-6 flex-1">
                    <div className="p-6 bg-white/90 rounded-[2.5rem] border border-sky-100 shadow-sm transition-all hover:-translate-y-1">
                      <div className="text-xl font-bold mb-2 text-sky-950">无损撤销机制</div>
                      <p className="text-xs text-sky-900/70 italic leading-relaxed">
                        每一次移动都有迹可循。通过 .autosniffer_history 日志，您可以随时撤销操作，如有重名会自动保留副本。
                      </p>
                    </div>
                    <div className="p-6 bg-white/90 rounded-[2.5rem] border border-sky-100 shadow-sm transition-all hover:-translate-y-1">
                      <div className="text-xl font-bold mb-2 text-sky-950">隐私即是尊严</div>
                      <p className="text-xs text-sky-900/70 italic leading-relaxed">
                        文件操作全程本地运行。AI 仅处理摘要特征，您的原始大文件从不离开您的本地磁盘，保障绝对隐私。
                      </p>
                    </div>
                    <div className="p-6 bg-white/90 rounded-[2.5rem] border border-sky-100 shadow-sm transition-all hover:-translate-y-1">
                      <div className="text-xl font-bold mb-2 text-sky-950">极速模型适配</div>
                      <p className="text-xs text-sky-900/70 italic leading-relaxed">
                        完美支持 Qwen-Flash 等高效模型。只需极低成本，即可完成成千上万个文件的深度梳理。
                      </p>
                    </div>
                  </div>
                  
                  <div className="mt-auto">
                    <OrnateDivider />
                    <p className="text-[10px] text-sky-800 font-black tracking-widest uppercase opacity-40 italic">Efficiency with Heart</p>
                  </div>
                </div>
              </BrochurePanel>

              {/* FRONT PANEL (Panel 1) */}
              <BrochurePanel className="bg-rose-50/30 border-amber-200">
                <div className="flex flex-col items-center text-center h-full pt-10">
                  <Logo className="w-40 h-40 mb-12 shadow-[0_20px_60px_rgba(197,160,89,0.3)]" />
                  
                  <div className="logo-font text-amber-800 text-[11px] tracking-[0.6em] mb-4 uppercase opacity-50">Intelligent File Concierge</div>
                  <h1 className="title-font text-6xl font-black text-amber-950 mb-4 tracking-tighter drop-shadow-md">AutoSniffer</h1>
                  <h3 className="text-2xl font-medium text-amber-800/80 serif-font italic mb-10">智慧文件整理管家</h3>
                  
                  <OrnateDivider />
                  
                  <p className="text-amber-950 font-black text-2xl italic mb-6">让文件找到最合适的归宿</p>
                  <p className="text-sm text-amber-900/60 leading-relaxed px-10 serif-font italic">
                    融合前沿大模型智慧，为您打造优雅、有序的数字办公环境。<br/>下载即用的独立程序，将繁琐交给 AI，将时间留给生命。
                  </p>

                  <div className="mt-auto pb-4">
                    <div className="px-10 py-2 bg-amber-950/5 border border-amber-200 rounded-full text-[9px] text-amber-900/60 font-black tracking-[0.4em] uppercase italic">
                      Windows Standalone .EXE Experience
                    </div>
                  </div>
                </div>
              </BrochurePanel>
            </>
          ) : (
            <>
              {/* INSIDE LEFT (Panel 2: Pain Points) */}
              <BrochurePanel className="bg-white/90">
                <div className="title-font text-[10px] text-rose-600 font-bold tracking-[0.3em] mb-8 uppercase">Common Challenges</div>
                <h2 className="text-3xl font-black text-rose-950 mb-10 italic">您的桌面是否也曾让您烦心？</h2>
                
                <div className="space-y-10 mb-14">
                  {[
                    { i: "📂", t: "混乱的下载目录", d: "成堆的文件堆积，手动分类一次需要耗费数小时。" },
                    { i: "🔍", t: "难以名状的文件", d: "“截图_1”或“新建文档”让查找变成大海捞针。" },
                    { i: "🤯", t: "分类的焦虑症", d: "犹豫该按日期还是项目分类？我们为您提供专业方案。" }
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
                    不仅是分类，更是一种数字生活的体贴关怀。AutoSniffer 利用 <strong>LLM 多模态 AI</strong>，能领会文档深意，看懂图片内涵。
                  </p>
                </div>
              </BrochurePanel>

              {/* INSIDE CENTER (Panel 3: Two-Stage & Rename) */}
              <BrochurePanel className="bg-amber-50/10">
                <div className="title-font text-[10px] text-amber-700 font-bold tracking-[0.3em] mb-6 uppercase text-center">Core Wisdom</div>
                <h2 className="text-3xl font-black text-amber-950 mb-10 text-center flex items-center justify-center gap-4 italic">
                   ✨ 核心整理智慧
                </h2>

                <div className="space-y-10 flex-1">
                  <section className="relative pl-14">
                    <div className="absolute left-0 top-1 text-amber-500 opacity-20"><FolderIcon className="w-12 h-12" /></div>
                    <h4 className="font-black text-amber-950 text-xl mb-2">🧭 两阶段专业归档</h4>
                    <p className="text-xs text-amber-900/80 italic leading-relaxed">
                      <strong>分析规划：</strong>先分析蓝图并为您预览分类逻辑。<br/>
                      <strong>智能执行：</strong>一键完成目录创建与文件精准位移。
                    </p>
                  </section>

                  <section className="relative pl-14">
                    <div className="absolute left-0 top-1 text-sky-500 opacity-20"><MagicWandIcon className="w-12 h-12" /></div>
                    <h4 className="font-black text-sky-950 text-xl mb-2">🏷️ 语义智能重命名</h4>
                    <p className="text-xs text-sky-900/80 italic leading-relaxed">
                      <strong>文档解析：</strong>依据内容深度生成极具概括性的名称。<br/>
                      <strong>图片视觉：</strong>运用多模态模型描述画面，让文件从此有名有姓。
                    </p>
                  </section>

                  <section className="relative pl-14">
                    <div className="absolute left-0 top-1 text-emerald-500 opacity-20"><UndoIcon className="w-12 h-12" /></div>
                    <h4 className="font-black text-emerald-950 text-xl mb-2">↩️ 随时回滚的从容</h4>
                    <p className="text-xs text-emerald-900/80 italic leading-relaxed">
                      整理结果不合意？点击撤销，即可让文件尽量回归原位。空文件夹在撤销时也会随之退场，不留痕迹。
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

              {/* INSIDE RIGHT (Panel 4: Usage Steps) */}
              <BrochurePanel className="bg-white/90">
                <div className="title-font text-[10px] text-amber-700 font-bold tracking-[0.3em] mb-8 uppercase">User Guide</div>
                <h2 className="text-2xl font-black text-amber-950 mb-12 italic text-center">简单五步，告别杂乱</h2>
                
                <div className="space-y-8 relative">
                  <div className="absolute left-6 top-6 bottom-6 w-[0.5px] bg-gradient-to-b from-amber-300 via-amber-100 to-transparent"></div>
                  
                  {[
                    { n: "1", t: "基础配置", d: "启动程序，在设置页填入 API Key 与配置。", c: "bg-rose-100 text-rose-800" },
                    { n: "2", t: "选定目录", d: "选取您需要整理的杂乱文件夹，点击‘扫描’。", c: "bg-sky-100 text-sky-800" },
                    { n: "3", t: "智慧分析", d: "让 AI 为您生成分类建议，您可以根据需求微调。", c: "bg-amber-200 text-amber-900" },
                    { n: "4", t: "确认执行", d: "开启阶段 1 & 2，静待成百上千文件有序归位。", c: "bg-amber-950 text-white shadow-lg" },
                    { n: "5", t: "进阶重命名", d: "如有需要，可前往‘重命名’赋予文件语义名称。", c: "bg-emerald-100 text-emerald-800" }
                  ].map((step, idx) => (
                    <div key={idx} className="relative pl-16 group cursor-default">
                      <div className={`absolute left-0 top-0 w-10 h-10 ${step.c} rounded-full flex items-center justify-center font-black text-xs shadow-md group-hover:scale-125 transition-all duration-500`}>{step.n}</div>
                      <p className="font-black text-amber-950 text-lg mb-1">{step.t}</p>
                      <p className="text-xs text-amber-800/60 italic leading-relaxed">{step.d}</p>
                    </div>
                  ))}
                </div>

                <div className="mt-auto pt-12">
                  <div className="bg-gradient-to-br from-gray-50 to-white rounded-[2rem] overflow-hidden border border-amber-100 shadow-2xl group">
                    <div className="bg-amber-900/5 h-8 border-b border-amber-100 px-4 flex items-center justify-between">
                      <div className="flex gap-2">
                        <div className="w-2 h-2 rounded-full bg-rose-400"></div>
                        <div className="w-2 h-2 rounded-full bg-amber-400"></div>
                        <div className="w-2 h-2 rounded-full bg-emerald-400"></div>
                      </div>
                      <span className="text-[9px] font-black text-amber-800/30 tracking-widest italic">WORKFLOW INTERFACE</span>
                    </div>
                    <div className="p-8 bg-white flex flex-col gap-4">
                      <div className="flex gap-4">
                        <div className="w-20 h-16 bg-amber-50 rounded-2xl flex items-center justify-center">
                          <RobotIcon className="w-8 h-8 text-amber-200" />
                        </div>
                        <div className="flex-1 flex flex-col gap-3 justify-center">
                          <div className="w-full h-2 bg-amber-100/30 rounded-full"></div>
                          <div className="w-3/4 h-2 bg-amber-100/30 rounded-full"></div>
                        </div>
                      </div>
                      <div className="w-full h-1 bg-gradient-to-r from-amber-100/10 via-amber-400/20 to-amber-100/10 rounded-full"></div>
                    </div>
                  </div>
                </div>
              </BrochurePanel>
            </>
          )}
        </div>
      </div>

      <footer className="mt-20 text-center relative z-20">
        <OrnateDivider />
        <p className="title-font text-amber-950/20 text-[10px] font-black tracking-[0.5em] uppercase italic">
          © 2024 AutoSniffer Laboratory • Windows Standalone Native Experience
        </p>
      </footer>
    </div>
  );
};

export default App;
