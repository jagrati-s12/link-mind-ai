import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Map,
  Sparkles,
  Trash2,
  ExternalLink,
  BookOpen,
  CheckCircle2,
  CheckSquare,
  Square,
  Flame,
  ArrowRight,
  Shuffle,
  Check,
  Plus,
  GitMerge,
  SplitSquareVertical,
  Laptop,
  Clock
} from 'lucide-react';
import { api } from '../services/api';
import { EmptyState } from '../components/EmptyState';
import { RoadmapStep, RoadmapTopic, Roadmap } from '../types';

export const Roadmaps: React.FC = () => {
  const queryClient = useQueryClient();
  const [goalInput, setGoalInput] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatorMode, setGeneratorMode] = useState<'single' | 'hybrid'>('hybrid');
  const [selectedTracks, setSelectedTracks] = useState<string[]>([
    'Data Structures & Algorithms',
    'AI Engineer (roadmap.sh/ai)'
  ]);
  const [customTrackInput, setCustomTrackInput] = useState('');

  const { data: roadmaps, isLoading } = useQuery({
    queryKey: ['roadmaps-list'],
    queryFn: api.getRoadmaps
  });

  const generateMutation = useMutation({
    mutationFn: (goal: string) => api.generateRoadmap(goal),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roadmaps-list'] });
      setGoalInput('');
      setIsGenerating(false);
    },
    onError: () => setIsGenerating(false)
  });

  const toggleStepMutation = useMutation({
    mutationFn: ({ roadmapId, stepId }: { roadmapId: number; stepId: string }) =>
      api.toggleRoadmapStep(roadmapId, stepId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roadmaps-list'] });
    }
  });

  const toggleTopicMutation = useMutation({
    mutationFn: ({ roadmapId, stepId, topicIdx }: { roadmapId: number; stepId: string; topicIdx: number }) =>
      api.toggleRoadmapSubtopic(roadmapId, stepId, topicIdx),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roadmaps-list'] });
    }
  });

  const deleteRoadmapMutation = useMutation({
    mutationFn: (id: number) => api.deleteRoadmap(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roadmaps-list'] });
    }
  });

  const handleGenerate = (e: React.FormEvent) => {
    e.preventDefault();
    if (goalInput.trim()) {
      setIsGenerating(true);
      generateMutation.mutate(goalInput.trim());
    }
  };

  const handleQuickGoal = (goal: string) => {
    setIsGenerating(true);
    generateMutation.mutate(goal);
  };

  const handleToggleTrack = (track: string) => {
    if (selectedTracks.includes(track)) {
      if (selectedTracks.length > 1) {
        setSelectedTracks(selectedTracks.filter(t => t !== track));
      }
    } else {
      if (selectedTracks.length < 3) {
        setSelectedTracks([...selectedTracks, track]);
      }
    }
  };

  const handleAddCustomTrack = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = customTrackInput.trim();
    if (trimmed && !selectedTracks.includes(trimmed) && selectedTracks.length < 3) {
      setSelectedTracks([...selectedTracks, trimmed]);
      setCustomTrackInput('');
    }
  };

  const handleGenerateHybrid = () => {
    if (selectedTracks.length >= 2) {
      setIsGenerating(true);
      const combinedGoal = selectedTracks.join(' + ');
      generateMutation.mutate(combinedGoal);
    }
  };

  const getImportanceBadge = (importance?: string) => {
    switch (importance) {
      case 'Must Know':
        return 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800/60';
      case 'Advanced':
        return 'bg-purple-50 text-purple-700 dark:bg-purple-950/40 dark:text-purple-400 border-purple-200 dark:border-purple-800/60';
      default:
        return 'bg-sky-50 text-sky-700 dark:bg-sky-950/40 dark:text-sky-400 border-sky-200 dark:border-sky-800/60';
    }
  };

  return (
    <div className="space-y-8 max-w-5xl mx-auto animate-fade-in pb-16">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-brand-50 text-brand-700 dark:bg-brand-950/50 dark:text-brand-300 border border-brand-200/60 dark:border-brand-800/60">
              Interactive Execution Paths
            </span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white mt-1.5">
            Personalized Career Roadmaps
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 max-w-2xl leading-relaxed">
            Pursue single careers or synchronize 2–3 career tracks on the exact same timeline with interleaved milestones, side-by-side competency checks, and unified bridge capstones.
          </p>
        </div>
      </div>

      {/* Generator Box with Dual-Career / Single Mode */}
      <div className="bg-white dark:bg-slate-900 p-6 md:p-8 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100 dark:border-slate-800">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-brand-600 dark:text-brand-400 flex items-center space-x-1.5">
              <GitMerge className="w-4 h-4" />
              <span>Multi-Career & Hybrid Roadmap Engine</span>
            </span>
            <h2 className="text-lg font-bold text-slate-900 dark:text-white mt-0.5">
              {generatorMode === 'hybrid' ? 'Pursue 2 Careers on the Same Timeline' : 'What do you want to learn?'}
            </h2>
          </div>

          {/* Mode Switch Pills */}
          <div className="flex items-center p-1 bg-slate-100 dark:bg-slate-800 rounded-xl self-start sm:self-auto text-xs font-medium">
            <button
              onClick={() => setGeneratorMode('hybrid')}
              className={`px-3 py-1.5 rounded-lg transition-all flex items-center space-x-1.5 ${
                generatorMode === 'hybrid'
                  ? 'bg-brand-600 text-white shadow-xs font-bold'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              <SplitSquareVertical className="w-3.5 h-3.5" />
              <span>Dual-Career Timeline (Method 1)</span>
            </button>
            <button
              onClick={() => setGeneratorMode('single')}
              className={`px-3 py-1.5 rounded-lg transition-all ${
                generatorMode === 'single'
                  ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-xs font-bold'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              Single Career
            </button>
          </div>
        </div>

        {/* Mode A: Single Goal */}
        {generatorMode === 'single' ? (
          <div className="space-y-4">
            <form onSubmit={handleGenerate} className="flex flex-col sm:flex-row gap-2">
              <input
                type="text"
                required
                value={goalInput}
                onChange={(e) => setGoalInput(e.target.value)}
                placeholder="e.g. AI Engineer (roadmap.sh/ai), Data Structures & Algorithms, Backend SDE..."
                className="flex-1 px-4 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-xs sm:text-sm text-slate-900 dark:text-white focus:outline-none focus:border-brand-500"
              />
              <button
                type="submit"
                disabled={isGenerating || !goalInput.trim()}
                className="flex items-center justify-center space-x-1.5 bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white font-medium text-xs px-5 py-2.5 rounded-xl shadow-sm whitespace-nowrap transition-colors"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>{isGenerating ? 'Synthesizing...' : 'Generate Roadmap'}</span>
              </button>
            </form>

            <div className="flex flex-wrap items-center gap-2 pt-1">
              <span className="text-[11px] text-slate-400">Popular single roadmaps:</span>
              {[
                'AI Engineer (roadmap.sh/ai)',
                'Data Structures & Algorithms',
                'Core Backend SDE',
                'Full Stack Developer',
                'Cloud & DevOps'
              ].map((g) => (
                <button
                  key={g}
                  onClick={() => handleQuickGoal(g)}
                  className="text-[11px] font-medium px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-brand-50 dark:hover:bg-brand-950/40 text-slate-600 dark:text-slate-300 hover:text-brand-600 transition-colors"
                >
                  + {g}
                </button>
              ))}
            </div>
          </div>
        ) : (
          /* Mode B: Dual-Career Synchronized Timeline (Method 1) */
          <div className="space-y-4">
            <div className="p-4 rounded-2xl bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-950/30 dark:to-purple-950/30 border border-blue-200/70 dark:border-blue-900/50 flex items-start space-x-3.5">
              <div className="p-2 rounded-xl bg-blue-600 text-white shrink-0 mt-0.5">
                <GitMerge className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-xs font-bold text-slate-900 dark:text-white">
                  Dual-Career Same-Timeline Architecture
                </h4>
                <p className="text-[11px] text-slate-600 dark:text-slate-300 mt-0.5 leading-relaxed">
                  Select two careers (e.g. <b>Data Structures & Algorithms</b> + <b>AI Engineer</b>). The engine merges both paths onto a <b>single synchronized timeline</b> so you work through matched milestones side-by-side each month and build one unified bridge capstone.
                </p>
              </div>
            </div>

            {/* Popular Career Pairs */}
            <div className="space-y-2">
              <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400">
                Quick 1-Click Dual-Career Pairs:
              </span>
              <div className="flex flex-wrap gap-2">
                {[
                  ['Data Structures & Algorithms', 'AI Engineer (roadmap.sh/ai)'],
                  ['Core Backend SDE', 'Cloud & DevOps'],
                  ['Full Stack Developer', 'AI Engineer (roadmap.sh/ai)'],
                  ['Data Structures & Algorithms', 'Core Backend SDE']
                ].map(([c1, c2], idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => setSelectedTracks([c1, c2])}
                    className={`text-[11px] font-medium px-3 py-1.5 rounded-xl border transition-all ${
                      selectedTracks.includes(c1) && selectedTracks.includes(c2) && selectedTracks.length === 2
                        ? 'bg-brand-600 text-white border-brand-600 font-bold shadow-xs'
                        : 'bg-slate-50 dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:border-brand-400'
                    }`}
                  >
                    {c1.replace(/\s*\(.*?\)/, '')} + {c2.replace(/\s*\(.*?\)/, '')}
                  </button>
                ))}
              </div>
            </div>

            {/* Select 2 Careers Grid */}
            <div className="space-y-2 pt-1">
              <div className="flex items-center justify-between text-xs font-medium">
                <span className="text-slate-700 dark:text-slate-300">
                  Or pick any 2 careers to sync:
                </span>
                <span className="text-brand-600 dark:text-brand-400 font-bold">
                  {selectedTracks.length} / 2 selected
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5">
                {[
                  'Data Structures & Algorithms',
                  'AI Engineer (roadmap.sh/ai)',
                  'Core Backend SDE',
                  'Cloud & DevOps',
                  'Full Stack Developer'
                ].map((track) => {
                  const isChecked = selectedTracks.includes(track);
                  return (
                    <button
                      key={track}
                      type="button"
                      onClick={() => handleToggleTrack(track)}
                      className={`flex items-center justify-between p-3 rounded-xl border text-xs font-semibold text-left transition-all ${
                        isChecked
                          ? 'bg-brand-50 dark:bg-brand-950/60 border-brand-500 text-brand-900 dark:text-brand-100 shadow-xs'
                          : 'bg-slate-50 dark:bg-slate-800/60 border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:border-slate-300'
                      }`}
                    >
                      <span className="truncate pr-1">{track}</span>
                      <div className={`w-4 h-4 rounded-md flex items-center justify-center shrink-0 border ${
                        isChecked ? 'bg-brand-600 border-brand-600 text-white' : 'border-slate-300 dark:border-slate-600'
                      }`}>
                        {isChecked && <Check className="w-3 h-3" />}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Custom Track Input */}
            <form onSubmit={handleAddCustomTrack} className="flex gap-2 pt-1">
              <input
                type="text"
                value={customTrackInput}
                onChange={(e) => setCustomTrackInput(e.target.value)}
                placeholder="Or type a custom career (e.g. Rust, Mobile iOS)..."
                disabled={selectedTracks.length >= 3}
                className="flex-1 px-3.5 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-xs text-slate-900 dark:text-white focus:outline-none focus:border-brand-500 disabled:opacity-50"
              />
              <button
                type="submit"
                disabled={!customTrackInput.trim() || selectedTracks.length >= 3}
                className="px-3.5 py-2 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 disabled:opacity-50 text-slate-700 dark:text-slate-300 rounded-xl text-xs font-semibold flex items-center space-x-1"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add Career</span>
              </button>
            </form>

            {/* Combined Action Button */}
            <div className="pt-2">
              <button
                onClick={handleGenerateHybrid}
                disabled={isGenerating || selectedTracks.length < 2}
                className="w-full sm:w-auto flex items-center justify-center space-x-2 bg-brand-600 hover:bg-brand-700 disabled:opacity-50 text-white font-bold text-xs sm:text-sm px-7 py-3 rounded-2xl shadow-sm transition-all"
              >
                <GitMerge className="w-4 h-4" />
                <span>
                  {isGenerating
                    ? 'Synthesizing Dual-Career Timeline...'
                    : `Generate Synchronized Timeline (${selectedTracks.map(t => t.replace(/\s*\(.*?\)/, '')).join(' + ')})`}
                </span>
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Roadmaps List (renders single or synchronized dual-career timeline) */}
      {(!roadmaps || roadmaps.length === 0) ? (
        <EmptyState
          icon={Map}
          title="No career roadmaps generated yet"
          description="Select 2 careers above to synthesize an integrated dual-career timeline, or generate a single career roadmap."
        />
      ) : (
        <div className="space-y-12">
          {roadmaps.map((rm) => {
            const allTopics = rm.steps.flatMap((s: RoadmapStep) => s.topics || []);
            const hasTopics = allTopics.length > 0;
            const completedCount = hasTopics
              ? allTopics.filter((t: RoadmapTopic) => t.completed).length
              : rm.steps.filter((s: RoadmapStep) => s.completed).length;
            const totalCount = hasTopics ? allTopics.length : (rm.steps.length || 1);
            const progressPct = Math.round((completedCount / (totalCount || 1)) * 100);
            const isHybrid = rm.goal_title.includes('+') || rm.goal_title.toLowerCase().includes('hybrid');

            return (
              <div
                key={rm.id}
                id={`roadmap-${rm.id}`}
                className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 p-6 md:p-8 shadow-sm space-y-6 scroll-mt-20"
              >
                {/* Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100 dark:border-slate-800">
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider border ${
                        isHybrid
                          ? 'bg-purple-50 text-purple-700 dark:bg-purple-950/50 dark:text-purple-300 border-purple-200/60 dark:border-purple-800/60'
                          : 'bg-blue-50 text-blue-700 dark:bg-blue-950/50 dark:text-blue-300 border-blue-200/60 dark:border-blue-800/60'
                      }`}>
                        {isHybrid ? 'Dual-Career Synchronized Timeline' : (rm.target_role || 'Target Role')}
                      </span>
                    </div>
                    <h3 className="text-xl font-extrabold text-slate-900 dark:text-white tracking-tight">
                      {rm.goal_title}
                    </h3>
                    <p className="text-xs text-slate-500 dark:text-slate-400 max-w-2xl leading-relaxed">
                      {rm.description}
                    </p>
                  </div>

                  <div className="flex items-center space-x-4 self-end sm:self-center">
                    <div className="text-right">
                      <span className="text-sm font-bold text-slate-900 dark:text-white">
                        {progressPct}% Complete
                      </span>
                      <span className="block text-[11px] text-slate-400">
                        {completedCount} of {totalCount} {hasTopics ? 'competencies' : 'milestones'}
                      </span>
                    </div>

                    <button
                      onClick={() => deleteRoadmapMutation.mutate(rm.id)}
                      className="p-2 text-slate-400 hover:text-rose-500 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition-colors"
                      title="Delete Roadmap"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2.5 overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-300 ${
                      isHybrid
                        ? 'bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600'
                        : 'bg-gradient-to-r from-brand-600 to-indigo-600'
                    }`}
                    style={{ width: `${progressPct}%` }}
                  />
                </div>

                {/* Connected Flow Timeline */}
                <div className="relative pl-4 sm:pl-6 space-y-8 before:absolute before:left-[19px] sm:before:left-[27px] before:top-4 before:bottom-4 before:w-0.5 before:bg-slate-200 dark:before:bg-slate-800">
                  {rm.steps.map((step: RoadmapStep, sIdx: number) => {
                    const stepTopics = step.topics || [];
                    const stepCompletedTopics = stepTopics.filter((t: RoadmapTopic) => t.completed).length;

                    // Detect Dual-Career Split for this step
                    const stepTracks = step.tracks || [];
                    const t1 = stepTracks[0];
                    const t2 = stepTracks[1];

                    // Partition topics into Career 1, Career 2, and Shared/Capstone
                    const t1Topics: { topic: RoadmapTopic; idx: number }[] = [];
                    const t2Topics: { topic: RoadmapTopic; idx: number }[] = [];
                    const sharedTopics: { topic: RoadmapTopic; idx: number }[] = [];

                    stepTopics.forEach((topic: RoadmapTopic, tIdx: number) => {
                      if (t1 && (topic.track === t1 || topic.name.startsWith(`[${t1}]`))) {
                        t1Topics.push({ topic, idx: tIdx });
                      } else if (t2 && (topic.track === t2 || topic.name.startsWith(`[${t2}]`))) {
                        t2Topics.push({ topic, idx: tIdx });
                      } else {
                        sharedTopics.push({ topic, idx: tIdx });
                      }
                    });

                    const hasDualSplit = t1 && t2 && (t1Topics.length > 0 || t2Topics.length > 0);

                    return (
                      <div key={step.id} className="relative flex items-start space-x-4 sm:space-x-5 group">
                        {/* Milestone Number / Toggle Badge */}
                        <button
                          onClick={() => toggleStepMutation.mutate({ roadmapId: rm.id, stepId: step.id })}
                          className={`relative z-10 w-9 h-9 sm:w-10 sm:h-10 rounded-2xl flex items-center justify-center font-bold text-xs shrink-0 transition-all shadow-sm ${
                            step.completed
                              ? 'bg-emerald-600 text-white shadow-emerald-500/20'
                              : 'bg-white dark:bg-slate-800 border-2 border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:border-brand-500'
                          }`}
                          title={step.completed ? 'Mark Milestone Incomplete' : 'Mark Entire Milestone Complete'}
                        >
                          {step.completed ? (
                            <CheckCircle2 className="w-5 h-5 text-white" />
                          ) : (
                            <span>{String(step.order || sIdx + 1).padStart(2, '0')}</span>
                          )}
                        </button>

                        {/* Module Content Card */}
                        <div
                          className={`flex-1 p-5 sm:p-6 rounded-2xl border transition-all ${
                            step.completed
                              ? 'bg-slate-50/70 dark:bg-slate-800/30 border-slate-200/60 dark:border-slate-800/60'
                              : 'bg-white dark:bg-slate-800/60 border-slate-200 dark:border-slate-700/80 shadow-sm'
                          }`}
                        >
                          {/* Module Header */}
                          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                            <h4
                              className={`text-sm sm:text-base font-bold ${
                                step.completed
                                  ? 'line-through text-slate-400 dark:text-slate-500'
                                  : 'text-slate-900 dark:text-white'
                              }`}
                            >
                              {step.title}
                            </h4>

                            {stepTopics.length > 0 && (
                              <span className="text-[11px] font-semibold text-slate-400 dark:text-slate-500">
                                {stepCompletedTopics} / {stepTopics.length} competencies
                              </span>
                            )}
                          </div>

                          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 leading-relaxed">
                            {step.description}
                          </p>

                          {/* DUAL-CAREER SPLIT VIEW (On the SAME Timeline Node) */}
                          {hasDualSplit ? (
                            <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 space-y-3">
                              {/* Shared Cadence Topics if any */}
                              {sharedTopics.length > 0 && (
                                <div className="space-y-1.5 pb-1">
                                  <span className="text-[10px] font-bold uppercase tracking-wider text-amber-500 flex items-center space-x-1">
                                    <Clock className="w-3 h-3 mr-1" />
                                    Synchronized Study Cadence & Strategy
                                  </span>
                                  <div className="grid grid-cols-1 gap-2">
                                    {sharedTopics.map(({ topic, idx: tIdx }) => (
                                      <div
                                        key={tIdx}
                                        onClick={() =>
                                          toggleTopicMutation.mutate({
                                            roadmapId: rm.id,
                                            stepId: step.id,
                                            topicIdx: tIdx
                                          })
                                        }
                                        className={`flex items-center justify-between p-2.5 rounded-xl border text-xs cursor-pointer transition-colors ${
                                          topic.completed
                                            ? 'bg-slate-100/60 dark:bg-slate-800/40 border-slate-200/50 dark:border-slate-800 text-slate-400 line-through'
                                            : 'bg-amber-50/50 dark:bg-amber-950/20 border-amber-200/70 dark:border-amber-800/50 text-slate-800 dark:text-slate-200 hover:border-amber-400'
                                        }`}
                                      >
                                        <div className="flex items-center space-x-2 truncate pr-2">
                                          {topic.completed ? (
                                            <CheckSquare className="w-4 h-4 text-emerald-500 shrink-0" />
                                          ) : (
                                            <Square className="w-4 h-4 text-amber-500 shrink-0" />
                                          )}
                                          <span className="truncate font-medium">{topic.name}</span>
                                        </div>
                                        {topic.importance && (
                                          <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded border whitespace-nowrap shrink-0 ${getImportanceBadge(topic.importance)}`}>
                                            {topic.importance}
                                          </span>
                                        )}
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}

                              {/* Two Columns Side-by-Side: Career 1 and Career 2 */}
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
                                {/* Career 1 Column */}
                                <div className="p-3.5 rounded-2xl bg-blue-50/40 dark:bg-blue-950/20 border border-blue-200/60 dark:border-blue-900/50 space-y-2">
                                  <div className="flex items-center justify-between">
                                    <span className="text-[10px] font-bold uppercase tracking-wider text-blue-700 dark:text-blue-300 flex items-center space-x-1">
                                      <Laptop className="w-3.5 h-3.5 mr-1 text-blue-600" />
                                      {t1}
                                    </span>
                                    <span className="text-[10px] font-semibold text-blue-600/80 dark:text-blue-400/80">Career 1</span>
                                  </div>

                                  <div className="space-y-1.5">
                                    {t1Topics.map(({ topic, idx: tIdx }) => (
                                      <div
                                        key={tIdx}
                                        onClick={() =>
                                          toggleTopicMutation.mutate({
                                            roadmapId: rm.id,
                                            stepId: step.id,
                                            topicIdx: tIdx
                                          })
                                        }
                                        className={`flex items-center justify-between p-2 rounded-xl border text-xs cursor-pointer transition-colors ${
                                          topic.completed
                                            ? 'bg-slate-100/60 dark:bg-slate-800/40 border-slate-200/50 dark:border-slate-800 text-slate-400 line-through'
                                            : 'bg-white dark:bg-slate-900 border-blue-200/80 dark:border-blue-800/60 text-slate-800 dark:text-slate-200 hover:border-blue-500'
                                        }`}
                                      >
                                        <div className="flex items-center space-x-2 truncate pr-2">
                                          {topic.completed ? (
                                            <CheckSquare className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
                                          ) : (
                                            <Square className="w-3.5 h-3.5 text-blue-500 shrink-0" />
                                          )}
                                          <span className="truncate font-medium">{topic.name.replace(`[${t1}]`, '').trim()}</span>
                                        </div>
                                        {topic.importance && (
                                          <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded border whitespace-nowrap shrink-0 ${getImportanceBadge(topic.importance)}`}>
                                            {topic.importance}
                                          </span>
                                        )}
                                      </div>
                                    ))}
                                  </div>
                                </div>

                                {/* Career 2 Column */}
                                <div className="p-3.5 rounded-2xl bg-purple-50/40 dark:bg-purple-950/20 border border-purple-200/60 dark:border-purple-900/50 space-y-2">
                                  <div className="flex items-center justify-between">
                                    <span className="text-[10px] font-bold uppercase tracking-wider text-purple-700 dark:text-purple-300 flex items-center space-x-1">
                                      <Sparkles className="w-3.5 h-3.5 mr-1 text-purple-600" />
                                      {t2}
                                    </span>
                                    <span className="text-[10px] font-semibold text-purple-600/80 dark:text-purple-400/80">Career 2</span>
                                  </div>

                                  <div className="space-y-1.5">
                                    {t2Topics.map(({ topic, idx: tIdx }) => (
                                      <div
                                        key={tIdx}
                                        onClick={() =>
                                          toggleTopicMutation.mutate({
                                            roadmapId: rm.id,
                                            stepId: step.id,
                                            topicIdx: tIdx
                                          })
                                        }
                                        className={`flex items-center justify-between p-2 rounded-xl border text-xs cursor-pointer transition-colors ${
                                          topic.completed
                                            ? 'bg-slate-100/60 dark:bg-slate-800/40 border-slate-200/50 dark:border-slate-800 text-slate-400 line-through'
                                            : 'bg-white dark:bg-slate-900 border-purple-200/80 dark:border-purple-800/60 text-slate-800 dark:text-slate-200 hover:border-purple-500'
                                        }`}
                                      >
                                        <div className="flex items-center space-x-2 truncate pr-2">
                                          {topic.completed ? (
                                            <CheckSquare className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
                                          ) : (
                                            <Square className="w-3.5 h-3.5 text-purple-500 shrink-0" />
                                          )}
                                          <span className="truncate font-medium">{topic.name.replace(`[${t2}]`, '').trim()}</span>
                                        </div>
                                        {topic.importance && (
                                          <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded border whitespace-nowrap shrink-0 ${getImportanceBadge(topic.importance)}`}>
                                            {topic.importance}
                                          </span>
                                        )}
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              </div>
                            </div>
                          ) : (
                            /* Standard Single-Track Grid */
                            stepTopics.length > 0 && (
                              <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 space-y-2">
                                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                                  Core Competencies & Subtopics
                                </span>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 pt-1">
                                  {stepTopics.map((topic: RoadmapTopic, tIdx: number) => (
                                    <div
                                      key={tIdx}
                                      onClick={() =>
                                        toggleTopicMutation.mutate({
                                          roadmapId: rm.id,
                                          stepId: step.id,
                                          topicIdx: tIdx
                                        })
                                      }
                                      className={`flex items-center justify-between p-2.5 rounded-xl border text-xs cursor-pointer transition-colors ${
                                        topic.completed
                                          ? 'bg-slate-100/60 dark:bg-slate-800/40 border-slate-200/50 dark:border-slate-800 text-slate-400 line-through'
                                          : 'bg-slate-50 dark:bg-slate-900/60 border-slate-200/80 dark:border-slate-700/80 text-slate-800 dark:text-slate-200 hover:border-brand-500/60'
                                      }`}
                                    >
                                      <div className="flex items-center space-x-2 truncate pr-2">
                                        {topic.completed ? (
                                          <CheckSquare className="w-4 h-4 text-emerald-500 shrink-0" />
                                        ) : (
                                          <Square className="w-4 h-4 text-slate-400 shrink-0" />
                                        )}
                                        <span className="truncate font-medium">{topic.name}</span>
                                      </div>

                                      {topic.importance && (
                                        <span
                                          className={`text-[9px] font-bold px-1.5 py-0.5 rounded border whitespace-nowrap shrink-0 ${getImportanceBadge(
                                            topic.importance
                                          )}`}
                                        >
                                          {topic.importance}
                                        </span>
                                      )}
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )
                          )}

                          {/* Curated Resources / Saved Courses */}
                          {step.resources && step.resources.length > 0 && (
                            <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 space-y-2">
                              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center space-x-1">
                                <BookOpen className="w-3 h-3 mr-1" />
                                Curated Learning Resources & Saved Courses
                              </span>
                              <div className="flex flex-wrap gap-2 pt-1">
                                {step.resources.map((res: any, rIdx: number) => (
                                  <a
                                    key={rIdx}
                                    href={res.url || '#'}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-medium bg-brand-50 dark:bg-brand-950/40 text-brand-700 dark:text-brand-300 border border-brand-200/70 dark:border-brand-800/60 hover:bg-brand-100 dark:hover:bg-brand-900/50 transition-colors shadow-2xs"
                                  >
                                    <span>{res.title}</span>
                                    <ExternalLink className="w-3 h-3 text-brand-500" />
                                  </a>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
