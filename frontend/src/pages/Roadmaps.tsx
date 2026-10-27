import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Map,
  Sparkles,
  Trash2,
  ExternalLink,
  BookOpen,
  CheckCircle2,
  Circle,
  CheckSquare,
  Square,
  Target
} from 'lucide-react';
import { api } from '../services/api';
import { EmptyState } from '../components/EmptyState';
import { RoadmapStep, RoadmapTopic } from '../types';

export const Roadmaps: React.FC = () => {
  const queryClient = useQueryClient();
  const [goalInput, setGoalInput] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);

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
            Interactive, node-based roadmaps structured with roadmap.sh logic — sequential milestones, granular competencies, curated tutorials, and direct links to your saved courses.
          </p>
        </div>
      </div>

      {/* Generator Box */}
      <div className="bg-white dark:bg-slate-900 p-6 md:p-8 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-brand-600 dark:text-brand-400">
            roadmap.sh Dynamic Roadmap Generator
          </span>
          <h2 className="text-lg font-bold text-slate-900 dark:text-white mt-1">
            What technical competency or career role are you targeting?
          </h2>
        </div>

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

        <div className="flex flex-wrap items-center gap-2 pt-2">
          <span className="text-[11px] text-slate-400">Popular roadmaps:</span>
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

      {/* Roadmaps List */}
      {(!roadmaps || roadmaps.length === 0) ? (
        <EmptyState
          icon={Map}
          title="No career roadmaps generated yet"
          description="Type in a career goal above (like 'AI Engineer' or 'Data Structures & Algorithms') to generate a step-by-step roadmap connected to your saved courses and vacancies."
        />
      ) : (
        <div className="space-y-10">
          {roadmaps.map((rm) => {
            const allTopics = rm.steps.flatMap((s: RoadmapStep) => s.topics || []);
            const hasTopics = allTopics.length > 0;
            const completedCount = hasTopics
              ? allTopics.filter((t: RoadmapTopic) => t.completed).length
              : rm.steps.filter((s: RoadmapStep) => s.completed).length;
            const totalCount = hasTopics ? allTopics.length : (rm.steps.length || 1);
            const progressPct = Math.round((completedCount / (totalCount || 1)) * 100);

            return (
              <div
                key={rm.id}
                className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 p-6 md:p-8 shadow-sm space-y-6"
              >
                {/* Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100 dark:border-slate-800">
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-blue-50 text-blue-700 dark:bg-blue-950/50 dark:text-blue-300 border border-blue-200/60 dark:border-blue-800/60">
                        {rm.target_role || 'Target Role'}
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
                        {completedCount} of {totalCount} {hasTopics ? 'topics' : 'milestones'}
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
                    className="bg-gradient-to-r from-brand-600 to-indigo-600 h-full rounded-full transition-all duration-300"
                    style={{ width: `${progressPct}%` }}
                  />
                </div>

                {/* Connected Flow Timeline */}
                <div className="relative pl-4 sm:pl-6 space-y-8 before:absolute before:left-[19px] sm:before:left-[27px] before:top-4 before:bottom-4 before:w-0.5 before:bg-slate-200 dark:before:bg-slate-800">
                  {rm.steps.map((step: RoadmapStep, sIdx: number) => {
                    const stepTopics = step.topics || [];
                    const stepCompletedTopics = stepTopics.filter((t: RoadmapTopic) => t.completed).length;

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
                                {stepCompletedTopics} / {stepTopics.length} topics
                              </span>
                            )}
                          </div>

                          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 leading-relaxed">
                            {step.description}
                          </p>

                          {/* Subtopics Checklist (roadmap.sh node competencies) */}
                          {stepTopics.length > 0 && (
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
