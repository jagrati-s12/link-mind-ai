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
  Clock,
  Video,
  Play,
  Layers,
  Network,
  ListChecks,
  Plus,
  X,
  FileText,
  Link2,
  Globe,
  Tag
} from 'lucide-react';
import { api } from '../services/api';
import { EmptyState } from '../components/EmptyState';
import { RoadmapStep, RoadmapTopic, Roadmap, RoadmapReference, RoadmapCatalogItem } from '../types';

export const Roadmaps: React.FC = () => {
  const queryClient = useQueryClient();
  const [goalInput, setGoalInput] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatorMode, setGeneratorMode] = useState<'single' | 'hybrid'>('hybrid');
  const [viewMode, setViewMode] = useState<'visual' | 'timeline'>('visual');
  const [selectedTracks, setSelectedTracks] = useState<string[]>([
    'Data Structures & Algorithms',
    'AI Engineer (roadmap.sh/ai)'
  ]);
  const [customTrackInput, setCustomTrackInput] = useState('');

  // Subtopic Inspector Drawer / Modal State
  const [inspectorTopic, setInspectorTopic] = useState<{
    roadmapId: number;
    stepId: string;
    stepTitle: string;
    topicIdx: number;
    topic: RoadmapTopic;
  } | null>(null);

  // New Reference Form State
  const [newRefTitle, setNewRefTitle] = useState('');
  const [newRefUrl, setNewRefUrl] = useState('');
  const [newRefType, setNewRefType] = useState('doc');
  const [newRefNotes, setNewRefNotes] = useState('');
  const [isAddingRef, setIsAddingRef] = useState(false);

  const { data: roadmaps, isLoading } = useQuery({
    queryKey: ['roadmaps-list'],
    queryFn: api.getRoadmaps
  });

  const { data: catalog } = useQuery({
    queryKey: ['roadmap-catalog'],
    queryFn: api.getRoadmapCatalog
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
    onSuccess: (updatedRoadmap) => {
      queryClient.invalidateQueries({ queryKey: ['roadmaps-list'] });
      // Update inspector topic if open
      if (inspectorTopic) {
        const step = updatedRoadmap.steps.find((s) => s.id === inspectorTopic.stepId);
        if (step && step.topics && step.topics[inspectorTopic.topicIdx]) {
          setInspectorTopic({
            ...inspectorTopic,
            topic: step.topics[inspectorTopic.topicIdx]
          });
        }
      }
    }
  });

  const addReferenceMutation = useMutation({
    mutationFn: ({
      roadmapId,
      stepId,
      topicIdx,
      payload
    }: {
      roadmapId: number;
      stepId: string;
      topicIdx: number;
      payload: { title: string; url: string; type?: string; notes?: string };
    }) => api.addRoadmapTopicReference(roadmapId, stepId, topicIdx, payload),
    onSuccess: (updatedRoadmap) => {
      queryClient.invalidateQueries({ queryKey: ['roadmaps-list'] });
      if (inspectorTopic) {
        const step = updatedRoadmap.steps.find((s) => s.id === inspectorTopic.stepId);
        if (step && step.topics && step.topics[inspectorTopic.topicIdx]) {
          setInspectorTopic({
            ...inspectorTopic,
            topic: step.topics[inspectorTopic.topicIdx]
          });
        }
      }
      setNewRefTitle('');
      setNewRefUrl('');
      setNewRefNotes('');
      setIsAddingRef(false);
    }
  });

  const deleteReferenceMutation = useMutation({
    mutationFn: ({
      roadmapId,
      stepId,
      topicIdx,
      refIdx
    }: {
      roadmapId: number;
      stepId: string;
      topicIdx: number;
      refIdx: number;
    }) => api.deleteRoadmapTopicReference(roadmapId, stepId, topicIdx, refIdx),
    onSuccess: (updatedRoadmap) => {
      queryClient.invalidateQueries({ queryKey: ['roadmaps-list'] });
      if (inspectorTopic) {
        const step = updatedRoadmap.steps.find((s) => s.id === inspectorTopic.stepId);
        if (step && step.topics && step.topics[inspectorTopic.topicIdx]) {
          setInspectorTopic({
            ...inspectorTopic,
            topic: step.topics[inspectorTopic.topicIdx]
          });
        }
      }
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
        setSelectedTracks(selectedTracks.filter((t) => t !== track));
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

  const handleSaveReference = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inspectorTopic || !newRefTitle.trim() || !newRefUrl.trim()) return;
    addReferenceMutation.mutate({
      roadmapId: inspectorTopic.roadmapId,
      stepId: inspectorTopic.stepId,
      topicIdx: inspectorTopic.topicIdx,
      payload: {
        title: newRefTitle.trim(),
        url: newRefUrl.trim(),
        type: newRefType,
        notes: newRefNotes.trim()
      }
    });
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

  // Fallback catalog presets if API hasn't loaded yet
  const catalogPresets: RoadmapCatalogItem[] = catalog || [
    {
      id: 'ai-engineer',
      title: 'AI Engineer (roadmap.sh/ai)',
      category: 'AI & Machine Learning',
      badge: 'roadmap.sh/ai',
      target_role: 'AI Engineer / Generative AI Specialist',
      description: 'Pre-trained models, prompt engineering, vector databases, RAG pipelines, and autonomous agent loops.',
      modules_count: 6,
      popular_pair: 'Data Structures & Algorithms',
      icon: 'bot'
    },
    {
      id: 'dsa',
      title: 'Data Structures & Algorithms',
      category: 'Computer Science',
      badge: 'roadmap.sh/dsa',
      target_role: 'Software Engineer (Algorithms & Problem Solving)',
      description: 'Algorithmic complexity, linear DSA, trees, graphs, dynamic programming, and NeetCode 150 patterns.',
      modules_count: 7,
      popular_pair: 'AI Engineer',
      icon: 'binary'
    },
    {
      id: 'backend',
      title: 'Backend Developer',
      category: 'Web Development',
      badge: 'roadmap.sh/backend',
      target_role: 'Core Backend Software Engineer',
      description: 'Language concurrency, relational databases, REST & gRPC, Redis caching, message queues, and system design.',
      modules_count: 6,
      popular_pair: 'DevOps & Cloud',
      icon: 'server'
    },
    {
      id: 'frontend',
      title: 'Frontend Developer',
      category: 'Web Development',
      badge: 'roadmap.sh/frontend',
      target_role: 'Modern Frontend Software Engineer',
      description: 'Modern HTML/CSS, TypeScript, React ecosystem, client caching, and Core Web Vitals performance.',
      modules_count: 6,
      popular_pair: 'Backend Developer',
      icon: 'layout'
    },
    {
      id: 'devops',
      title: 'DevOps & Cloud',
      category: 'Cloud & Infrastructure',
      badge: 'roadmap.sh/devops',
      target_role: 'DevOps / Site Reliability Engineer',
      description: 'Linux systems, Docker containers, Kubernetes orchestration, CI/CD pipelines, and Terraform IaC.',
      modules_count: 5,
      popular_pair: 'Backend Developer',
      icon: 'cloud'
    }
  ];

  return (
    <div className="space-y-8 max-w-6xl mx-auto animate-fade-in pb-16">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-amber-100 text-amber-800 dark:bg-amber-950/60 dark:text-amber-300 border border-amber-300 dark:border-amber-800/60 flex items-center gap-1">
              <Network className="w-3 h-3" />
              roadmap.sh Visual Architecture
            </span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white mt-1.5">
            Interactive Career Roadmaps
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 max-w-2xl leading-relaxed">
            Visual node-and-branch learning maps modeled after <strong className="font-semibold text-slate-700 dark:text-slate-200">roadmap.sh</strong>. Every subtopic includes curated reference links, video playlists, and the ability to attach your own learning materials.
          </p>
        </div>

        {/* Global View Switcher */}
        <div className="flex items-center p-1 bg-slate-100 dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700">
          <button
            onClick={() => setViewMode('visual')}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
              viewMode === 'visual'
                ? 'bg-amber-400 text-black shadow-sm'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <Network className="w-3.5 h-3.5" />
            <span>Visual Tree Graph</span>
          </button>
          <button
            onClick={() => setViewMode('timeline')}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
              viewMode === 'timeline'
                ? 'bg-brand-600 text-white shadow-sm'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <ListChecks className="w-3.5 h-3.5" />
            <span>Sequential Milestones</span>
          </button>
        </div>
      </div>

      {/* 1-Click Popular Roadmaps Catalog Shelf */}
      <div className="bg-white dark:bg-slate-900 p-5 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="p-1.5 rounded-xl bg-amber-100 dark:bg-amber-950/40 text-amber-600 border border-amber-300 dark:border-amber-800">
              <Sparkles className="w-4 h-4" />
            </span>
            <span className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider">
              1-Click Pre-Scraped roadmap.sh Tracks
            </span>
          </div>
          <span className="text-[11px] text-slate-400">Click any card to instantly generate with video playlists</span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2.5 pt-1">
          {catalogPresets.slice(0, 5).map((cat) => (
            <button
              key={cat.id}
              onClick={() => handleQuickGoal(cat.title)}
              disabled={isGenerating}
              className="p-3 rounded-2xl border border-slate-200 dark:border-slate-800 hover:border-amber-400 dark:hover:border-amber-500 bg-slate-50/50 dark:bg-slate-800/40 hover:bg-amber-50/30 dark:hover:bg-amber-950/20 text-left transition-all group flex flex-col justify-between"
            >
              <div>
                <span className="inline-block px-1.5 py-0.5 rounded text-[9px] font-bold bg-amber-200 dark:bg-amber-900/60 text-amber-900 dark:text-amber-200 mb-1.5">
                  {cat.badge}
                </span>
                <h4 className="text-xs font-bold text-slate-900 dark:text-white group-hover:text-amber-600 dark:group-hover:text-amber-400 transition-colors line-clamp-1">
                  {cat.title.replace(' (roadmap.sh/ai)', '')}
                </h4>
                <p className="text-[10px] text-slate-400 line-clamp-2 mt-1">
                  {cat.description}
                </p>
              </div>
              <div className="mt-2.5 pt-2 border-t border-slate-200/60 dark:border-slate-700/60 flex items-center justify-between text-[10px] font-semibold text-amber-600 dark:text-amber-400">
                <span>{cat.modules_count} Modules</span>
                <span className="group-hover:translate-x-0.5 transition-transform">&rarr;</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Generator / Multi-Track Synthesis Box */}
      <div className="bg-white dark:bg-slate-900 p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100 dark:border-slate-800">
          <div>
            <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center space-x-2">
              <Layers className="w-5 h-5 text-amber-500" />
              <span>Customize Single or Dual-Career Roadmap</span>
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Synchronize two careers side-by-side or generate a dedicated path for any role or technology.
            </p>
          </div>

          <div className="flex items-center p-1 bg-slate-100 dark:bg-slate-800 rounded-xl">
            <button
              type="button"
              onClick={() => setGeneratorMode('hybrid')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                generatorMode === 'hybrid'
                  ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-xs'
                  : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              Dual-Career Timeline
            </button>
            <button
              type="button"
              onClick={() => setGeneratorMode('single')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                generatorMode === 'single'
                  ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-xs'
                  : 'text-slate-500 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              Single Career
            </button>
          </div>
        </div>

        {generatorMode === 'hybrid' ? (
          <div className="space-y-4">
            <div className="flex flex-wrap gap-2">
              {[
                'Data Structures & Algorithms',
                'AI Engineer (roadmap.sh/ai)',
                'Backend Developer',
                'Frontend Developer',
                'DevOps & Cloud',
                'Python Developer'
              ].map((track) => {
                const isSelected = selectedTracks.includes(track);
                return (
                  <button
                    key={track}
                    type="button"
                    onClick={() => handleToggleTrack(track)}
                    className={`px-3 py-1.5 rounded-xl text-xs font-medium border transition-all flex items-center space-x-1.5 ${
                      isSelected
                        ? 'bg-amber-400 text-black border-black font-bold shadow-xs'
                        : 'bg-slate-50 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-700 hover:border-slate-400'
                    }`}
                  >
                    <span>{track}</span>
                    {isSelected && <span className="text-black font-bold text-xs">✓</span>}
                  </button>
                );
              })}
            </div>

            <div className="flex items-center justify-between pt-2">
              <span className="text-xs text-slate-500">
                Selected for Synchronized Timeline: <strong className="text-slate-900 dark:text-white">{selectedTracks.join(' + ')}</strong>
              </span>
              <button
                type="button"
                onClick={handleGenerateHybrid}
                disabled={isGenerating || selectedTracks.length < 2}
                className="px-5 py-2.5 rounded-xl bg-yellow-400 hover:bg-yellow-500 text-black font-bold text-xs transition-colors shadow-sm disabled:opacity-50 flex items-center space-x-2"
              >
                <Sparkles className="w-3.5 h-3.5 text-black" />
                <span>{isGenerating ? 'Synthesizing...' : 'Generate Synchronized Roadmap'}</span>
              </button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleGenerate} className="flex gap-2">
            <input
              type="text"
              value={goalInput}
              onChange={(e) => setGoalInput(e.target.value)}
              placeholder="e.g. AI Engineer, Machine Learning, Rust Developer, or https://roadmap.sh/ai"
              className="flex-1 px-4 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs focus:ring-2 focus:ring-amber-500 focus:outline-hidden"
            />
            <button
              type="submit"
              disabled={isGenerating || !goalInput.trim()}
              className="px-5 py-2.5 rounded-xl bg-yellow-400 hover:bg-yellow-500 text-black font-bold text-xs transition-colors shadow-sm disabled:opacity-50 flex items-center space-x-2"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>{isGenerating ? 'Generating...' : 'Generate Roadmap'}</span>
            </button>
          </form>
        )}
      </div>

      {/* Roadmaps List & Render */}
      {isLoading ? (
        <div className="p-12 text-center text-slate-400 text-xs">Loading execution roadmaps...</div>
      ) : !roadmaps || roadmaps.length === 0 ? (
        <EmptyState
          title="No Roadmaps Created Yet"
          description="Select an official track from the roadmap.sh shelf above or customize a dual-career synchronized path."
          icon={Map}
        />
      ) : (
        <div className="space-y-12">
          {roadmaps.map((rm: Roadmap) => {
            const allTopics = rm.steps.flatMap((s) => s.topics || []);
            const completedTopics = allTopics.filter((t) => t.completed).length;
            const totalCount = allTopics.length > 0 ? allTopics.length : rm.steps.length;
            const completedCount = allTopics.length > 0 ? completedTopics : rm.steps.filter((s) => s.completed).length;
            const progressPct = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;
            const isHybrid = rm.goal_title.startsWith('Hybrid Multi-Track:');

            return (
              <div
                key={rm.id}
                className="bg-white dark:bg-slate-900 rounded-3xl border-2 border-slate-200 dark:border-slate-800 shadow-sm p-6 sm:p-8 space-y-6"
              >
                {/* Roadmap Header & Actions */}
                <div className="flex flex-col md:flex-row md:items-start justify-between gap-4 pb-4 border-b border-slate-100 dark:border-slate-800">
                  <div className="space-y-1.5 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wider bg-yellow-300 dark:bg-yellow-400 text-black border border-black shadow-2xs">
                        roadmap.sh verified
                      </span>
                      {isHybrid && (
                        <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-purple-100 text-purple-700 dark:bg-purple-950/60 dark:text-purple-300 border border-purple-300 dark:border-purple-800">
                          Dual-Career Synchronized
                        </span>
                      )}
                    </div>
                    <h2 className="text-xl sm:text-2xl font-extrabold text-slate-900 dark:text-white">
                      {rm.goal_title}
                    </h2>
                    <p className="text-xs text-slate-500 dark:text-slate-400 max-w-3xl leading-relaxed">
                      {rm.description}
                    </p>
                  </div>

                  <div className="flex items-center space-x-3 shrink-0">
                    <div className="text-right">
                      <span className="text-base font-black text-slate-900 dark:text-white">
                        {progressPct}% Done
                      </span>
                      <span className="block text-[11px] text-slate-400">
                        {completedCount} of {totalCount} competencies
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
                    className="h-full rounded-full bg-amber-400 transition-all duration-300"
                    style={{ width: `${progressPct}%` }}
                  />
                </div>

                {/* Top Section: Related Roadmaps Box + Curated YouTube Playlists */}
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 pt-2">
                  {/* Related Roadmaps Floating Card (Matching Screenshot Top-Left Box!) */}
                  {rm.related_roadmaps && rm.related_roadmaps.length > 0 && (
                    <div className="lg:col-span-4 bg-slate-50 dark:bg-slate-800/60 border-2 border-slate-300 dark:border-slate-700 rounded-2xl p-4 space-y-2.5">
                      <div className="flex items-center space-x-2 pb-1 border-b border-slate-200 dark:border-slate-700">
                        <span className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider">
                          Related Roadmaps
                        </span>
                      </div>
                      <div className="space-y-1.5">
                        {rm.related_roadmaps.map((relTrack, rIdx) => (
                          <div
                            key={rIdx}
                            onClick={() => handleQuickGoal(relTrack)}
                            className="flex items-center space-x-2 text-xs text-slate-700 dark:text-slate-300 hover:text-amber-600 dark:hover:text-amber-400 cursor-pointer font-medium p-1 rounded-lg hover:bg-amber-50 dark:hover:bg-amber-950/30 transition-colors"
                          >
                            <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                            <span className="truncate">{relTrack}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Curated YouTube Playlists at Start of Roadmap */}
                  <div className={rm.related_roadmaps && rm.related_roadmaps.length > 0 ? "lg:col-span-8" : "lg:col-span-12"}>
                    <div className="bg-red-50/50 dark:bg-red-950/20 border border-red-200 dark:border-red-900/50 rounded-2xl p-4 space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-red-900 dark:text-red-200 flex items-center space-x-1.5 uppercase tracking-wider">
                          <Play className="w-3.5 h-3.5 fill-red-600 text-red-600" />
                          <span>Curated YouTube Playlists & Video Courses</span>
                        </span>
                        <span className="text-[10px] text-red-700 dark:text-red-300 font-semibold">
                          Recommended Watching
                        </span>
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                        {(rm.youtube_playlists && rm.youtube_playlists.length > 0
                          ? rm.youtube_playlists
                          : [
                              {
                                title: 'Full AI Engineer Course',
                                channel: 'freeCodeCamp.org',
                                url: 'https://www.youtube.com/@freecodecamp',
                                badge: 'Free Course',
                                videos_count: 'Full Series'
                              },
                              {
                                title: 'Neural Networks: Zero to Hero',
                                channel: 'Andrej Karpathy',
                                url: 'https://www.youtube.com/playlist?list=PLAqhIrjkxbuWI23v9cThsA9GvCAUhRvKZ',
                                badge: 'Top Rated',
                                videos_count: '8 Videos'
                              }
                            ]
                        ).map((pl, pIdx) => (
                          <a
                            key={pIdx}
                            href={pl.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="p-3 bg-white dark:bg-slate-900 rounded-xl border border-red-200/80 dark:border-red-800/60 hover:border-red-500 dark:hover:border-red-500 shadow-2xs transition-all flex items-start space-x-3 group"
                          >
                            <div className="w-8 h-8 rounded-lg bg-red-600 text-white flex items-center justify-center shrink-0 shadow-xs group-hover:scale-105 transition-transform">
                              <Play className="w-4 h-4 fill-white" />
                            </div>
                            <div className="min-w-0 flex-1">
                              <span className="block text-xs font-bold text-slate-900 dark:text-white group-hover:text-red-600 dark:group-hover:text-red-400 transition-colors truncate">
                                {pl.title}
                              </span>
                              <div className="flex items-center space-x-2 mt-0.5">
                                <span className="text-[11px] text-slate-500 truncate">
                                  {pl.channel}
                                </span>
                                {pl.badge && (
                                  <span className="text-[9px] font-bold px-1.5 py-0.2 rounded bg-red-100 dark:bg-red-900/60 text-red-800 dark:text-red-200 shrink-0">
                                    {pl.badge}
                                  </span>
                                )}
                              </div>
                            </div>
                            <ExternalLink className="w-3.5 h-3.5 text-slate-400 group-hover:text-red-500 shrink-0" />
                          </a>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                {/* -------------------------------------------------------------
                    VIEW MODE 1: VISUAL TREE GRAPH (roadmap.sh NODE & BRANCHES)
                    Modeled after uploaded screenshot media_1793081493341_6c25713c.png
                   ------------------------------------------------------------- */}
                {viewMode === 'visual' ? (
                  <div className="relative pt-6 pb-12 overflow-x-auto">
                    {/* Central Vertical Spine / Blue Trunk Line */}
                    <div className="relative min-w-[760px] max-w-4xl mx-auto">
                      {/* Vertical Spine Line */}
                      <div className="absolute left-1/2 top-0 bottom-0 w-1 -translate-x-1/2 bg-blue-600 dark:bg-blue-500 z-0 rounded-full" />

                      <div className="space-y-16 relative z-10">
                        {rm.steps.map((step: RoadmapStep, sIdx: number) => {
                          const stepTopics = step.topics || [];
                          // Split subtopics into left-side and right-side branches
                          const midPoint = Math.ceil(stepTopics.length / 2);
                          const leftTopics = stepTopics.slice(0, midPoint);
                          const rightTopics = stepTopics.slice(midPoint);

                          return (
                            <div key={step.id} className="relative">
                              {/* Section Name / Step Order Tag Above Center Milestone */}
                              <div className="text-center mb-2">
                                <span className="inline-block px-3 py-1 rounded-full text-[11px] font-bold bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 shadow-2xs">
                                  {step.title.split('.')[0] ? `Phase ${step.title.split('.')[0]}` : `Phase ${sIdx + 1}`} • Section Foundations
                                </span>
                              </div>

                              {/* Center Milestone Node + Radiating Left & Right Branches */}
                              <div className="grid grid-cols-12 items-center gap-4">
                                {/* LEFT BRANCH SUBTOPICS */}
                                <div className="col-span-4 flex flex-col items-end space-y-2.5 pr-2">
                                  {leftTopics.map((topic: RoadmapTopic, tIdx: number) => {
                                    const actualIdx = tIdx;
                                    const hasRefs = topic.references && topic.references.length > 0;
                                    return (
                                      <div
                                        key={actualIdx}
                                        className="relative flex items-center group w-full justify-end"
                                      >
                                        {/* Subtopic Card Styled in Warm Amber / Yellow */}
                                        <div
                                          onClick={() =>
                                            setInspectorTopic({
                                              roadmapId: rm.id,
                                              stepId: step.id,
                                              stepTitle: step.title,
                                              topicIdx: actualIdx,
                                              topic
                                            })
                                          }
                                          className={`w-full max-w-[240px] p-2.5 rounded-xl border-2 transition-all cursor-pointer shadow-sm text-left ${
                                            topic.completed
                                              ? 'bg-emerald-50/80 dark:bg-emerald-950/40 border-emerald-400 dark:border-emerald-700 opacity-60'
                                              : 'bg-[#fef3c7] dark:bg-amber-950/60 border-amber-300 dark:border-amber-700 hover:border-black dark:hover:border-white hover:shadow-md'
                                          }`}
                                        >
                                          <div className="flex items-start justify-between gap-1.5">
                                            <span
                                              className={`text-xs font-bold leading-tight ${
                                                topic.completed
                                                  ? 'line-through text-slate-400'
                                                  : 'text-slate-900 dark:text-slate-100'
                                              }`}
                                            >
                                              {topic.name}
                                            </span>
                                            <button
                                              type="button"
                                              onClick={(e) => {
                                                e.stopPropagation();
                                                toggleTopicMutation.mutate({
                                                  roadmapId: rm.id,
                                                  stepId: step.id,
                                                  topicIdx: actualIdx
                                                });
                                              }}
                                              className="shrink-0 p-0.5 hover:scale-110 transition-transform"
                                            >
                                              {topic.completed ? (
                                                <CheckSquare className="w-4 h-4 text-emerald-600" />
                                              ) : (
                                                <Square className="w-4 h-4 text-slate-400 hover:text-black dark:hover:text-white" />
                                              )}
                                            </button>
                                          </div>

                                          <div className="mt-1.5 flex items-center justify-between text-[10px]">
                                            <span className={`px-1 rounded text-[9px] font-bold ${getImportanceBadge(topic.importance)}`}>
                                              {topic.importance || 'Must Know'}
                                            </span>
                                            {hasRefs && (
                                              <span className="text-amber-800 dark:text-amber-300 font-bold flex items-center space-x-0.5">
                                                <BookOpen className="w-3 h-3 mr-0.5" />
                                                <span>{topic.references!.length} refs</span>
                                              </span>
                                            )}
                                          </div>
                                        </div>

                                        {/* Dotted Connector Line to Center */}
                                        <div className="w-6 border-b-2 border-dotted border-blue-500 dark:border-blue-400 shrink-0" />
                                      </div>
                                    );
                                  })}
                                </div>

                                {/* CENTER MILESTONE CARD (Yellow Box with Black Border) */}
                                <div className="col-span-4 flex justify-center">
                                  <div
                                    onClick={() =>
                                      toggleStepMutation.mutate({
                                        roadmapId: rm.id,
                                        stepId: step.id
                                      })
                                    }
                                    className={`relative z-20 py-3.5 px-5 rounded-2xl border-2 transition-all cursor-pointer shadow-md text-center group ${
                                      step.completed
                                        ? 'bg-emerald-600 text-white border-black'
                                        : 'bg-yellow-300 hover:bg-yellow-400 dark:bg-yellow-400 text-black border-black hover:scale-105'
                                    }`}
                                  >
                                    <h3 className="text-xs sm:text-sm font-black leading-snug">
                                      {step.title.replace(/^\d+\.\s*/, '')}
                                    </h3>
                                    <div className="mt-1 flex items-center justify-center space-x-1.5 text-[10px] font-bold">
                                      {step.completed ? (
                                        <span className="flex items-center text-white">
                                          <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
                                          Completed
                                        </span>
                                      ) : (
                                        <span className="opacity-80">
                                          {stepTopics.filter((t) => t.completed).length} / {stepTopics.length} done
                                        </span>
                                      )}
                                    </div>
                                  </div>
                                </div>

                                {/* RIGHT BRANCH SUBTOPICS */}
                                <div className="col-span-4 flex flex-col items-start space-y-2.5 pl-2">
                                  {rightTopics.map((topic: RoadmapTopic, tIdx: number) => {
                                    const actualIdx = midPoint + tIdx;
                                    const hasRefs = topic.references && topic.references.length > 0;
                                    return (
                                      <div
                                        key={actualIdx}
                                        className="relative flex items-center group w-full justify-start"
                                      >
                                        {/* Dotted Connector Line from Center */}
                                        <div className="w-6 border-b-2 border-dotted border-blue-500 dark:border-blue-400 shrink-0" />

                                        {/* Subtopic Card Styled in Warm Amber / Yellow */}
                                        <div
                                          onClick={() =>
                                            setInspectorTopic({
                                              roadmapId: rm.id,
                                              stepId: step.id,
                                              stepTitle: step.title,
                                              topicIdx: actualIdx,
                                              topic
                                            })
                                          }
                                          className={`w-full max-w-[240px] p-2.5 rounded-xl border-2 transition-all cursor-pointer shadow-sm text-left ${
                                            topic.completed
                                              ? 'bg-emerald-50/80 dark:bg-emerald-950/40 border-emerald-400 dark:border-emerald-700 opacity-60'
                                              : 'bg-[#fef3c7] dark:bg-amber-950/60 border-amber-300 dark:border-amber-700 hover:border-black dark:hover:border-white hover:shadow-md'
                                          }`}
                                        >
                                          <div className="flex items-start justify-between gap-1.5">
                                            <span
                                              className={`text-xs font-bold leading-tight ${
                                                topic.completed
                                                  ? 'line-through text-slate-400'
                                                  : 'text-slate-900 dark:text-slate-100'
                                              }`}
                                            >
                                              {topic.name}
                                            </span>
                                            <button
                                              type="button"
                                              onClick={(e) => {
                                                e.stopPropagation();
                                                toggleTopicMutation.mutate({
                                                  roadmapId: rm.id,
                                                  stepId: step.id,
                                                  topicIdx: actualIdx
                                                });
                                              }}
                                              className="shrink-0 p-0.5 hover:scale-110 transition-transform"
                                            >
                                              {topic.completed ? (
                                                <CheckSquare className="w-4 h-4 text-emerald-600" />
                                              ) : (
                                                <Square className="w-4 h-4 text-slate-400 hover:text-black dark:hover:text-white" />
                                              )}
                                            </button>
                                          </div>

                                          <div className="mt-1.5 flex items-center justify-between text-[10px]">
                                            <span className={`px-1 rounded text-[9px] font-bold ${getImportanceBadge(topic.importance)}`}>
                                              {topic.importance || 'Must Know'}
                                            </span>
                                            {hasRefs && (
                                              <span className="text-amber-800 dark:text-amber-300 font-bold flex items-center space-x-0.5">
                                                <BookOpen className="w-3 h-3 mr-0.5" />
                                                <span>{topic.references!.length} refs</span>
                                              </span>
                                            )}
                                          </div>
                                        </div>
                                      </div>
                                    );
                                  })}
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                ) : (
                  /* -------------------------------------------------------------
                      VIEW MODE 2: SEQUENTIAL MILESTONE TIMELINE
                     ------------------------------------------------------------- */
                  <div className="relative pl-4 sm:pl-6 space-y-8 before:absolute before:left-[19px] sm:before:left-[27px] before:top-4 before:bottom-4 before:w-0.5 before:bg-slate-200 dark:before:bg-slate-800">
                    {rm.steps.map((step: RoadmapStep, sIdx: number) => {
                      const stepTopics = step.topics || [];
                      const stepCompletedTopics = stepTopics.filter((t) => t.completed).length;

                      return (
                        <div key={step.id} className="relative flex items-start space-x-4 sm:space-x-5 group">
                          <button
                            onClick={() => toggleStepMutation.mutate({ roadmapId: rm.id, stepId: step.id })}
                            className={`relative z-10 w-9 h-9 sm:w-10 sm:h-10 rounded-2xl flex items-center justify-center font-bold text-xs shrink-0 transition-all shadow-sm ${
                              step.completed
                                ? 'bg-emerald-600 text-white shadow-emerald-500/20'
                                : 'bg-white dark:bg-slate-800 border-2 border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:border-amber-500'
                            }`}
                          >
                            {step.completed ? (
                              <CheckCircle2 className="w-5 h-5 text-white" />
                            ) : (
                              <span>{String(step.order || sIdx + 1).padStart(2, '0')}</span>
                            )}
                          </button>

                          <div
                            className={`flex-1 p-5 sm:p-6 rounded-2xl border transition-all ${
                              step.completed
                                ? 'bg-slate-50/70 dark:bg-slate-800/30 border-slate-200/60 dark:border-slate-800/60'
                                : 'bg-white dark:bg-slate-800/60 border-slate-200 dark:border-slate-700/80 shadow-sm'
                            }`}
                          >
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

                            {/* Subtopics Checklist with Clickable Reference Inspector */}
                            {stepTopics.length > 0 && (
                              <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 space-y-2">
                                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                                  Competencies & Learning References (Click any to inspect)
                                </span>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 pt-1">
                                  {stepTopics.map((topic: RoadmapTopic, tIdx: number) => (
                                    <div
                                      key={tIdx}
                                      onClick={() =>
                                        setInspectorTopic({
                                          roadmapId: rm.id,
                                          stepId: step.id,
                                          stepTitle: step.title,
                                          topicIdx: tIdx,
                                          topic
                                        })
                                      }
                                      className={`flex items-center justify-between p-2.5 rounded-xl border text-xs cursor-pointer transition-colors ${
                                        topic.completed
                                          ? 'bg-slate-100/60 dark:bg-slate-800/40 border-slate-200/50 dark:border-slate-800 text-slate-400 line-through'
                                          : 'bg-slate-50 dark:bg-slate-900/60 border-slate-200/80 dark:border-slate-700/80 text-slate-800 dark:text-slate-200 hover:border-amber-500/80'
                                      }`}
                                    >
                                      <div className="flex items-center space-x-2 truncate pr-2">
                                        <button
                                          type="button"
                                          onClick={(e) => {
                                            e.stopPropagation();
                                            toggleTopicMutation.mutate({
                                              roadmapId: rm.id,
                                              stepId: step.id,
                                              topicIdx: tIdx
                                            });
                                          }}
                                          className="shrink-0"
                                        >
                                          {topic.completed ? (
                                            <CheckSquare className="w-4 h-4 text-emerald-500 shrink-0" />
                                          ) : (
                                            <Square className="w-4 h-4 text-slate-400 shrink-0" />
                                          )}
                                        </button>
                                        <span className="truncate font-medium">{topic.name}</span>
                                      </div>

                                      <div className="flex items-center space-x-1.5 shrink-0">
                                        {topic.references && topic.references.length > 0 && (
                                          <BookOpen className="w-3.5 h-3.5 text-amber-500" />
                                        )}
                                        {topic.importance && (
                                          <span
                                            className={`text-[9px] font-bold px-1.5 py-0.5 rounded border whitespace-nowrap ${getImportanceBadge(
                                              topic.importance
                                            )}`}
                                          >
                                            {topic.importance}
                                          </span>
                                        )}
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* -------------------------------------------------------------
          SUBTOPIC INSPECTOR & REFERENCE MATERIAL MODAL / DRAWER
         ------------------------------------------------------------- */}
      {inspectorTopic && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 animate-fade-in">
          <div className="bg-white dark:bg-slate-900 rounded-3xl border-2 border-slate-200 dark:border-slate-800 max-w-xl w-full p-6 sm:p-7 shadow-2xl space-y-5 max-h-[90vh] overflow-y-auto">
            {/* Header */}
            <div className="flex items-start justify-between gap-3 pb-3 border-b border-slate-100 dark:border-slate-800">
              <div className="space-y-1">
                <span className="text-[10px] font-bold text-amber-600 dark:text-amber-400 uppercase tracking-wider">
                  {inspectorTopic.stepTitle}
                </span>
                <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                  {inspectorTopic.topic.name}
                </h3>
              </div>
              <button
                onClick={() => setInspectorTopic(null)}
                className="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Topic Description / Key Concept */}
            <div className="space-y-1.5">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                Concept & What to Learn
              </span>
              <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed bg-slate-50 dark:bg-slate-800/60 p-3 rounded-xl border border-slate-200 dark:border-slate-700">
                {inspectorTopic.topic.description ||
                  'Master the core architecture, syntax primitives, and production tradeoffs for this competency.'}
              </p>
            </div>

            {/* Action Toggle Status */}
            <div className="flex items-center justify-between p-3 rounded-xl bg-amber-50/60 dark:bg-amber-950/20 border border-amber-200/80 dark:border-amber-800/60">
              <div className="flex items-center space-x-2">
                <button
                  type="button"
                  onClick={() =>
                    toggleTopicMutation.mutate({
                      roadmapId: inspectorTopic.roadmapId,
                      stepId: inspectorTopic.stepId,
                      topicIdx: inspectorTopic.topicIdx
                    })
                  }
                  className="flex items-center space-x-2 text-xs font-bold text-slate-900 dark:text-white"
                >
                  {inspectorTopic.topic.completed ? (
                    <CheckSquare className="w-4 h-4 text-emerald-600" />
                  ) : (
                    <Square className="w-4 h-4 text-slate-400" />
                  )}
                  <span>
                    Status: {inspectorTopic.topic.completed ? 'Completed' : 'In Progress'}
                  </span>
                </button>
              </div>
              <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${getImportanceBadge(inspectorTopic.topic.importance)}`}>
                {inspectorTopic.topic.importance || 'Must Know'}
              </span>
            </div>

            {/* Reference Materials List */}
            <div className="space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-900 dark:text-white flex items-center space-x-1.5">
                  <BookOpen className="w-4 h-4 text-amber-500" />
                  <span>Curated Learning Materials & Documentation</span>
                </span>
                <span className="text-[10px] text-slate-400">
                  {(inspectorTopic.topic.references || []).length} resources
                </span>
              </div>

              <div className="space-y-2">
                {(inspectorTopic.topic.references || []).length === 0 ? (
                  <p className="text-xs text-slate-400 italic p-3 text-center border border-dashed rounded-xl">
                    No references added yet. Click &quot;Add Material&quot; below to attach documentation or video guides!
                  </p>
                ) : (
                  (inspectorTopic.topic.references || []).map((ref: RoadmapReference, rIdx: number) => (
                    <div
                      key={rIdx}
                      className="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-200 dark:border-slate-700/80 flex items-center justify-between gap-2"
                    >
                      <div className="flex items-center space-x-2.5 truncate">
                        <span className="p-1 rounded-lg bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300">
                          {ref.type === 'video' ? <Video className="w-3.5 h-3.5" /> : <FileText className="w-3.5 h-3.5" />}
                        </span>
                        <div className="truncate">
                          <a
                            href={ref.url || '#'}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs font-bold text-slate-900 dark:text-white hover:text-amber-600 dark:hover:text-amber-400 truncate flex items-center space-x-1"
                          >
                            <span className="truncate">{ref.title}</span>
                            <ExternalLink className="w-3 h-3 text-slate-400 shrink-0" />
                          </a>
                          {ref.notes && (
                            <span className="block text-[10px] text-slate-400 truncate">{ref.notes}</span>
                          )}
                        </div>
                      </div>

                      <div className="flex items-center space-x-2 shrink-0">
                        {ref.is_user_added && (
                          <span className="px-1.5 py-0.5 rounded text-[9px] font-bold bg-purple-100 dark:bg-purple-950 text-purple-700 dark:text-purple-300">
                            Your Added Material
                          </span>
                        )}
                        {ref.is_user_added && (
                          <button
                            type="button"
                            onClick={() =>
                              deleteReferenceMutation.mutate({
                                roadmapId: inspectorTopic.roadmapId,
                                stepId: inspectorTopic.stepId,
                                topicIdx: inspectorTopic.topicIdx,
                                refIdx: rIdx
                              })
                            }
                            className="p-1 text-slate-400 hover:text-rose-500 rounded"
                            title="Delete custom material"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* User Form: Add Reference Material to Subtopic */}
            <div className="pt-2 border-t border-slate-100 dark:border-slate-800">
              {!isAddingRef ? (
                <button
                  type="button"
                  onClick={() => setIsAddingRef(true)}
                  className="w-full py-2.5 rounded-xl border-2 border-dashed border-amber-300 dark:border-amber-700/80 hover:border-amber-500 text-amber-700 dark:text-amber-300 text-xs font-bold transition-colors flex items-center justify-center space-x-1.5"
                >
                  <Plus className="w-4 h-4" />
                  <span>Add Reference Material or Link to this Subtopic</span>
                </button>
              ) : (
                <form onSubmit={handleSaveReference} className="bg-amber-50/50 dark:bg-amber-950/20 p-4 rounded-2xl border border-amber-300 dark:border-amber-800 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-amber-900 dark:text-amber-200">
                      Attach Custom Material / Link
                    </span>
                    <button
                      type="button"
                      onClick={() => setIsAddingRef(false)}
                      className="text-slate-400 hover:text-slate-600 dark:hover:text-white"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>

                  <div className="space-y-2">
                    <input
                      type="text"
                      required
                      value={newRefTitle}
                      onChange={(e) => setNewRefTitle(e.target.value)}
                      placeholder="Material Title (e.g. Stanford Lecture Video, Deeplearning.ai Notes)"
                      className="w-full px-3 py-2 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-xs focus:ring-2 focus:ring-amber-500 focus:outline-hidden"
                    />

                    <input
                      type="url"
                      required
                      value={newRefUrl}
                      onChange={(e) => setNewRefUrl(e.target.value)}
                      placeholder="Link URL (e.g. https://youtube.com/watch?v=... or doc link)"
                      className="w-full px-3 py-2 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-xs focus:ring-2 focus:ring-amber-500 focus:outline-hidden"
                    />

                    <div className="grid grid-cols-2 gap-2">
                      <select
                        value={newRefType}
                        onChange={(e) => setNewRefType(e.target.value)}
                        className="px-3 py-2 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-xs focus:ring-2 focus:ring-amber-500 focus:outline-hidden"
                      >
                        <option value="doc">Official Documentation</option>
                        <option value="video">YouTube / Video Guide</option>
                        <option value="article">Article / Tutorial</option>
                        <option value="github">GitHub Repo</option>
                      </select>

                      <input
                        type="text"
                        value={newRefNotes}
                        onChange={(e) => setNewRefNotes(e.target.value)}
                        placeholder="Optional Notes / Chapter"
                        className="px-3 py-2 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-xs focus:ring-2 focus:ring-amber-500 focus:outline-hidden"
                      />
                    </div>
                  </div>

                  <div className="flex justify-end space-x-2 pt-1">
                    <button
                      type="button"
                      onClick={() => setIsAddingRef(false)}
                      className="px-3 py-1.5 rounded-xl text-xs text-slate-500 hover:text-slate-900 dark:hover:text-white"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={addReferenceMutation.isPending || !newRefTitle.trim() || !newRefUrl.trim()}
                      className="px-4 py-1.5 rounded-xl bg-amber-400 hover:bg-amber-500 text-black text-xs font-bold transition-colors disabled:opacity-50"
                    >
                      {addReferenceMutation.isPending ? 'Saving...' : 'Save Material'}
                    </button>
                  </div>
                </form>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
