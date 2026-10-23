import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  ThumbsUp,
  ThumbsDown,
  CheckCircle2,
  Sparkles,
  HelpCircle,
  X,
  Brain,
  Edit3
} from 'lucide-react';
import { api } from '../services/api';

interface ListingFeedbackWidgetProps {
  resourceId: number;
  resourceTitle: string;
  resourceType: string;
  compact?: boolean;
}

export const ListingFeedbackWidget: React.FC<ListingFeedbackWidgetProps> = ({
  resourceId,
  resourceTitle,
  resourceType,
  compact = false
}) => {
  const queryClient = useQueryClient();
  const [isOpenCorrection, setIsOpenCorrection] = useState(false);
  const [correctedType, setCorrectedType] = useState<string>(
    resourceType === 'internship' ? 'job' : 'internship'
  );
  const [correctedTitle, setCorrectedTitle] = useState(resourceTitle);
  const [reason, setReason] = useState<string>('Wrong opportunity type');
  const [notes, setNotes] = useState('');
  const [justSubmitted, setJustSubmitted] = useState<string | null>(null);

  // Check if current user already submitted feedback
  const { data: existingFeedback } = useQuery({
    queryKey: ['feedback', resourceId],
    queryFn: () => api.getResourceFeedback(resourceId)
  });

  const feedbackMutation = useMutation({
    mutationFn: (data: {
      is_correct: boolean;
      corrected_type?: string;
      corrected_title?: string;
      reason?: string;
      notes?: string;
    }) =>
      api.submitFeedback({
        resource_id: resourceId,
        ...data
      }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['feedback', resourceId] });
      queryClient.invalidateQueries({ queryKey: ['resource', resourceId] });
      queryClient.invalidateQueries({ queryKey: ['resources-list'] });
      queryClient.invalidateQueries({ queryKey: ['courses-list'] });
      queryClient.invalidateQueries({ queryKey: ['internships-list'] });
      queryClient.invalidateQueries({ queryKey: ['jobs-list'] });
      queryClient.invalidateQueries({ queryKey: ['hackathons-list'] });
      queryClient.invalidateQueries({ queryKey: ['applications-list'] });
      queryClient.invalidateQueries({ queryKey: ['course-tracker-list'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
      queryClient.invalidateQueries({ queryKey: ['learning-stats'] });

      setIsOpenCorrection(false);
      if (data.is_correct) {
        setJustSubmitted('Verified as accurate! Feedback logged for AI reinforcement.');
      } else {
        setJustSubmitted(`Updated & trained! Reclassified to "${data.corrected_type}".`);
      }
    }
  });

  const handleVerifyAccurate = () => {
    feedbackMutation.mutate({ is_correct: true });
  };

  const handleCorrectionSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    feedbackMutation.mutate({
      is_correct: false,
      corrected_type: correctedType,
      corrected_title: correctedTitle.trim() || undefined,
      reason,
      notes: notes.trim() || undefined
    });
  };

  const typeOptions = [
    { value: 'internship', label: 'Internship' },
    { value: 'job', label: 'Full-time Job' },
    { value: 'course', label: 'Course / Tutorial' },
    { value: 'certification', label: 'Professional Certificate' },
    { value: 'hackathon', label: 'Hackathon' },
    { value: 'research', label: 'Research / Grant' }
  ];

  const reasonOptions = [
    'Wrong opportunity type',
    'Full-time engineering job, not internship',
    'College internship, not full-time job',
    'Course/tutorial, not job opportunity',
    'Inaccurate title or company',
    'Expired or closed opportunity',
    'Clutter or cookie banner text'
  ];

  // If already verified or just submitted
  if (justSubmitted || existingFeedback) {
    const isAccurate = existingFeedback?.is_correct ?? true;
    return (
      <div
        className={`inline-flex items-center space-x-1.5 px-3 py-1 rounded-xl text-xs font-semibold ${
          isAccurate
            ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800'
            : 'bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-800'
        }`}
      >
        <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
        <span>
          {justSubmitted ||
            (isAccurate
              ? 'Listing verified accurate ✓'
              : `Reclassified to ${existingFeedback?.corrected_type}`)}
        </span>
      </div>
    );
  }

  // Compact variant for cards
  if (compact) {
    return (
      <div className="relative inline-block">
        <div className="flex items-center space-x-1 bg-slate-50 dark:bg-slate-800/80 px-2 py-1 rounded-xl border border-slate-200 dark:border-slate-700/80 text-[11px] text-slate-500">
          <span className="text-[10px] uppercase font-bold text-slate-400 mr-1">Correct?</span>
          <button
            onClick={handleVerifyAccurate}
            disabled={feedbackMutation.isPending}
            className="p-1 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors"
            title="Mark as correct (trains AI)"
          >
            <ThumbsUp className="w-3 h-3" />
          </button>
          <button
            onClick={() => setIsOpenCorrection(true)}
            disabled={feedbackMutation.isPending}
            className="p-1 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors"
            title="Wrong listing type? Click to correct and train AI"
          >
            <ThumbsDown className="w-3 h-3" />
          </button>
        </div>

        {/* Modal for Card */}
        {isOpenCorrection && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm">
            <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 p-6 max-w-md w-full shadow-2xl space-y-4">
              <div className="flex items-center justify-between pb-2 border-b border-slate-100 dark:border-slate-800">
                <div className="flex items-center space-x-2">
                  <Brain className="w-4 h-4 text-indigo-600" />
                  <h3 className="font-bold text-sm text-slate-900 dark:text-white">
                    Correct & Train AI
                  </h3>
                </div>
                <button
                  onClick={() => setIsOpenCorrection(false)}
                  className="text-slate-400 hover:text-slate-600"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <form onSubmit={handleCorrectionSubmit} className="space-y-3 text-xs">
                <div>
                  <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    What type is this actually?
                  </label>
                  <select
                    value={correctedType}
                    onChange={(e) => setCorrectedType(e.target.value)}
                    className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-2.5 text-slate-900 dark:text-white font-medium"
                  >
                    {typeOptions.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Opportunity Title (Optional correction)
                  </label>
                  <input
                    type="text"
                    value={correctedTitle}
                    onChange={(e) => setCorrectedTitle(e.target.value)}
                    className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-2.5 text-slate-900 dark:text-white"
                  />
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Reason for correction
                  </label>
                  <select
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                    className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-2 text-slate-900 dark:text-white"
                  >
                    {reasonOptions.map((r) => (
                      <option key={r} value={r}>
                        {r}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="pt-2 flex justify-end space-x-2">
                  <button
                    type="button"
                    onClick={() => setIsOpenCorrection(false)}
                    className="px-3 py-2 rounded-xl text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={feedbackMutation.isPending}
                    className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-4 py-2 rounded-xl shadow-sm"
                  >
                    {feedbackMutation.isPending ? 'Training Model...' : 'Train Model & Update'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    );
  }

  // Full Rich Variant (For ResourceDetail Page)
  return (
    <div className="bg-gradient-to-br from-indigo-50/50 via-white to-slate-50 dark:from-slate-900 dark:via-slate-900/90 dark:to-indigo-950/20 p-5 rounded-3xl border border-indigo-100 dark:border-indigo-900/40 shadow-sm space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className="p-1.5 bg-indigo-100 dark:bg-indigo-950/60 rounded-lg text-indigo-600 dark:text-indigo-400">
            <Brain className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-xs font-bold text-slate-900 dark:text-white">
              AI Continuous Self-Improvement
            </h4>
            <span className="text-[11px] text-slate-500 dark:text-slate-400">
              Is this opportunity classified correctly as{' '}
              <strong className="text-indigo-600 dark:text-indigo-400 capitalize">
                {resourceType}
              </strong>
              ?
            </span>
          </div>
        </div>
      </div>

      <div className="flex items-center space-x-2 pt-1">
        <button
          onClick={handleVerifyAccurate}
          disabled={feedbackMutation.isPending}
          className="flex-1 flex items-center justify-center space-x-1.5 bg-emerald-50 hover:bg-emerald-100 dark:bg-emerald-950/40 dark:hover:bg-emerald-900/50 text-emerald-700 dark:text-emerald-300 font-semibold text-xs py-2 px-3 rounded-xl border border-emerald-200 dark:border-emerald-800/60 transition-colors"
        >
          <ThumbsUp className="w-3.5 h-3.5" />
          <span>Yes, Classified Correctly</span>
        </button>

        <button
          onClick={() => setIsOpenCorrection(true)}
          disabled={feedbackMutation.isPending}
          className="flex-1 flex items-center justify-center space-x-1.5 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 font-semibold text-xs py-2 px-3 rounded-xl border border-slate-200 dark:border-slate-700 transition-colors"
        >
          <Edit3 className="w-3.5 h-3.5" />
          <span>No, Correct / Retrain</span>
        </button>
      </div>

      {isOpenCorrection && (
        <form
          onSubmit={handleCorrectionSubmit}
          className="p-4 bg-white dark:bg-slate-850 rounded-2xl border border-indigo-200 dark:border-indigo-900/60 space-y-3 text-xs animate-fade-in mt-2"
        >
          <div className="flex items-center justify-between">
            <span className="font-bold text-indigo-600 dark:text-indigo-400 flex items-center space-x-1">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Model In-Context Correction</span>
            </span>
            <button
              type="button"
              onClick={() => setIsOpenCorrection(false)}
              className="text-slate-400 hover:text-slate-600"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>

          <div>
            <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
              Correct Category:
            </label>
            <select
              value={correctedType}
              onChange={(e) => setCorrectedType(e.target.value)}
              className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-2 font-medium text-slate-900 dark:text-white"
            >
              {typeOptions.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
              Correct Title (if scraped title had issues):
            </label>
            <input
              type="text"
              value={correctedTitle}
              onChange={(e) => setCorrectedTitle(e.target.value)}
              className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-2 text-slate-900 dark:text-white"
            />
          </div>

          <div>
            <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
              Why was the classification wrong?
            </label>
            <select
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-2 text-slate-900 dark:text-white"
            >
              {reasonOptions.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
              Additional Notes (Optional):
            </label>
            <input
              type="text"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="e.g. This is a 4-year degree cert, not an internship post"
              className="w-full bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl p-2 text-slate-900 dark:text-white"
            />
          </div>

          <div className="pt-2 flex justify-end space-x-2">
            <button
              type="button"
              onClick={() => setIsOpenCorrection(false)}
              className="px-3 py-1.5 rounded-xl text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={feedbackMutation.isPending}
              className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-4 py-1.5 rounded-xl shadow-sm"
            >
              {feedbackMutation.isPending ? 'Training Model...' : 'Train Model & Move Opportunity'}
            </button>
          </div>
        </form>
      )}
    </div>
  );
};
