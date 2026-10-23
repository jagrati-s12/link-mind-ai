import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Map, Plus, CheckCircle2, Circle, Sparkles, Trash2, ArrowRight } from 'lucide-react';
import { api } from '../services/api';
import { EmptyState } from '../components/EmptyState';

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

  return (
    <div className="space-y-8 max-w-5xl mx-auto animate-fade-in pb-12">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Personalized Career Roadmaps</h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Grounded execution plans built directly around your saved courses, skill gaps, and target vacancies
          </p>
        </div>
      </div>

      {/* Generator Box */}
      <div className="bg-white dark:bg-slate-900 p-6 md:p-8 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-brand-600 dark:text-brand-400">
            Generate Dynamic Opportunity Plan
          </span>
          <h2 className="text-lg font-bold text-slate-900 dark:text-white mt-1">
            What is your next career objective?
          </h2>
        </div>

        <form onSubmit={handleGenerate} className="flex flex-col sm:flex-row gap-2">
          <input
            type="text"
            required
            value={goalInput}
            onChange={(e) => setGoalInput(e.target.value)}
            placeholder="e.g. AI/ML Engineer Internship, Core Backend SDE, Cloud DevOps Intern..."
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
          <span className="text-[11px] text-slate-400">Popular goals:</span>
          {['AI/ML Engineer Internship', 'Core Backend SDE', 'Full Stack Developer', 'Data Scientist'].map((g) => (
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
          description="Type in a career goal above (like 'AI Engineer Internship') to generate a step-by-step roadmap connected to your saved courses and vacancies."
        />
      ) : (
        <div className="space-y-6">
          {roadmaps.map((rm) => {
            const completedCount = rm.steps.filter(s => s.completed).length;
            const progressPct = Math.round((completedCount / (rm.steps.length || 1)) * 100);

            return (
              <div
                key={rm.id}
                className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 p-6 md:p-8 shadow-sm space-y-6"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100 dark:border-slate-800">
                  <div>
                    <h3 className="text-xl font-extrabold text-slate-900 dark:text-white tracking-tight">
                      {rm.goal_title}
                    </h3>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 max-w-2xl leading-relaxed">
                      {rm.description}
                    </p>
                  </div>

                  <div className="flex items-center space-x-3 self-end sm:self-center">
                    <div className="text-right">
                      <span className="text-xs font-bold text-slate-900 dark:text-white">{progressPct}% Complete</span>
                      <span className="block text-[10px] text-slate-400">{completedCount} of {rm.steps.length} steps</span>
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

                {/* Progress bar */}
                <div className="w-full bg-slate-100 dark:bg-slate-800 rounded-full h-2 overflow-hidden">
                  <div
                    className="bg-brand-600 h-full rounded-full transition-all duration-300"
                    style={{ width: `${progressPct}%` }}
                  />
                </div>

                {/* Checklist steps */}
                <div className="space-y-3">
                  {rm.steps.map((step) => (
                    <div
                      key={step.id}
                      onClick={() => toggleStepMutation.mutate({ roadmapId: rm.id, stepId: step.id })}
                      className={`flex items-start space-x-3.5 p-4 rounded-2xl border transition-all cursor-pointer ${
                        step.completed
                          ? 'bg-slate-50/60 dark:bg-slate-800/30 border-slate-200/60 dark:border-slate-800/60 opacity-70'
                          : 'bg-white dark:bg-slate-800/70 border-slate-200 dark:border-slate-700 hover:border-brand-500/50 shadow-sm'
                      }`}
                    >
                      <button className="mt-0.5 text-brand-600 dark:text-brand-400 shrink-0">
                        {step.completed ? (
                          <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                        ) : (
                          <Circle className="w-5 h-5 text-slate-400" />
                        )}
                      </button>

                      <div className="flex-1">
                        <div className={`text-xs sm:text-sm font-bold ${
                          step.completed
                            ? 'line-through text-slate-400 dark:text-slate-500'
                            : 'text-slate-900 dark:text-white'
                        }`}>
                          {step.title}
                        </div>
                        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 leading-relaxed">
                          {step.description}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
