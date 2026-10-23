import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { GitFork, Sparkles, BookOpen, Briefcase, Plus, CheckCircle2, AlertCircle, Trash2 } from 'lucide-react';
import { api } from '../services/api';
import { Link } from 'react-router-dom';

export const Skills: React.FC = () => {
  const queryClient = useQueryClient();
  const [targetRole, setTargetRole] = useState('AI Engineer');
  const [newSkillName, setNewSkillName] = useState('');
  const [newSkillLevel, setNewSkillLevel] = useState('intermediate');
  const [showAddModal, setShowAddModal] = useState(false);

  const { data: userSkills } = useQuery({
    queryKey: ['skills-user'],
    queryFn: api.getUserSkills
  });

  const { data: gapData } = useQuery({
    queryKey: ['skills-gap', targetRole],
    queryFn: () => api.getSkillGaps(targetRole)
  });

  const addSkillMutation = useMutation({
    mutationFn: (data: { skill_name: string; proficiency_level: string }) => api.addUserSkill(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skills-user'] });
      queryClient.invalidateQueries({ queryKey: ['skills-gap'] });
      setShowAddModal(false);
      setNewSkillName('');
    }
  });

  const deleteSkillMutation = useMutation({
    mutationFn: (id: number) => api.deleteUserSkill(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['skills-user'] });
      queryClient.invalidateQueries({ queryKey: ['skills-gap'] });
    }
  });

  const roles = [
    'AI Engineer',
    'Machine Learning Engineer',
    'Backend Developer',
    'Frontend Developer',
    'Full Stack Developer',
    'Data Scientist',
    'Cloud / DevOps'
  ];

  const handleAddSkill = (e: React.FormEvent) => {
    e.preventDefault();
    if (newSkillName.trim()) {
      addSkillMutation.mutate({ skill_name: newSkillName.trim(), proficiency_level: newSkillLevel });
    }
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto animate-fade-in pb-12">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Skill Map & Gap Intelligence</h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Connects skills taught by courses to requirements for top internships and target roles
          </p>
        </div>

        <button
          onClick={() => setShowAddModal(true)}
          className="self-start sm:self-auto flex items-center space-x-1.5 bg-brand-600 hover:bg-brand-700 text-white font-medium text-xs px-4 py-2 rounded-xl shadow-sm transition-colors"
        >
          <Plus className="w-4 h-4" />
          <span>Add Custom Skill</span>
        </button>
      </div>

      {/* Target Role Selector */}
      <div className="bg-white dark:bg-slate-900 p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
        <span className="text-xs font-bold uppercase tracking-wider text-slate-400 block">
          Analyze Gap For Target Career Role
        </span>

        <div className="flex flex-wrap gap-2">
          {roles.map((r) => (
            <button
              key={r}
              onClick={() => setTargetRole(r)}
              className={`text-xs font-semibold px-4 py-2 rounded-xl transition-all ${
                targetRole === r
                  ? 'bg-brand-600 text-white shadow-sm scale-105'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
              }`}
            >
              {r}
            </button>
          ))}
        </div>

        {/* Skill Gap Cards */}
        {gapData && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5 pt-4">
            {/* Possessed Skills */}
            <div className="p-5 rounded-2xl bg-emerald-50/70 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-900/50 space-y-3">
              <div className="flex items-center space-x-2 text-emerald-800 dark:text-emerald-300 font-bold text-sm">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>Possessed Competencies ({gapData.possessed_skills.length})</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {gapData.possessed_skills.map((s, idx) => (
                  <span key={idx} className="text-xs font-semibold px-3 py-1 rounded-lg bg-emerald-100 dark:bg-emerald-900/60 text-emerald-800 dark:text-emerald-200">
                    {s}
                  </span>
                ))}
              </div>
            </div>

            {/* Missing Skills */}
            <div className="p-5 rounded-2xl bg-amber-50/70 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-900/50 space-y-3">
              <div className="flex items-center space-x-2 text-amber-800 dark:text-amber-300 font-bold text-sm">
                <AlertCircle className="w-4 h-4 text-amber-600" />
                <span>Identified Skill Gaps ({gapData.missing_skills.length})</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {gapData.missing_skills.map((s, idx) => (
                  <span key={idx} className="text-xs font-semibold px-3 py-1 rounded-lg bg-amber-100 dark:bg-amber-900/60 text-amber-800 dark:text-amber-200">
                    + {s}
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Course-to-Internship Mapping */}
      {gapData && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Courses that teach missing skills */}
          <div className="bg-white dark:bg-slate-900 p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
            <div className="flex items-center space-x-2">
              <BookOpen className="w-4 h-4 text-indigo-600" />
              <h3 className="font-bold text-slate-900 dark:text-white text-base">Recommended Courses for Gaps</h3>
            </div>
            {gapData.recommended_courses.length === 0 ? (
              <p className="text-xs text-slate-500 dark:text-slate-400">
                No saved courses teaching these specific skills yet. Paste course links into Inbox to bridge your gaps!
              </p>
            ) : (
              <div className="space-y-3">
                {gapData.recommended_courses.map((c) => (
                  <Link
                    key={c.id}
                    to={`/resources/${c.id}`}
                    className="block p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-700 transition-colors"
                  >
                    <div className="font-semibold text-xs text-slate-900 dark:text-white">{c.title}</div>
                    <div className="text-[11px] text-slate-500 mt-1">Teaches: {c.teaches.join(', ')}</div>
                  </Link>
                ))}
              </div>
            )}
          </div>

          {/* Internships requiring these skills */}
          <div className="bg-white dark:bg-slate-900 p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
            <div className="flex items-center space-x-2">
              <Briefcase className="w-4 h-4 text-amber-600" />
              <h3 className="font-bold text-slate-900 dark:text-white text-base">Saved Target Vacancies</h3>
            </div>
            {gapData.recommended_internships.length === 0 ? (
              <p className="text-xs text-slate-500 dark:text-slate-400">
                No internships saved matching this role yet. Save internships to see direct skill alignments.
              </p>
            ) : (
              <div className="space-y-3">
                {gapData.recommended_internships.map((i) => (
                  <Link
                    key={i.id}
                    to={`/resources/${i.id}`}
                    className="block p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-700 transition-colors"
                  >
                    <div className="font-semibold text-xs text-slate-900 dark:text-white">{i.title}</div>
                    <div className="text-[11px] text-slate-500 mt-1">{i.organization || 'Provider'} • Deadline: {i.deadline || 'Open'}</div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Your Verified Skills List */}
      <div className="bg-white dark:bg-slate-900 p-6 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
        <h3 className="font-bold text-slate-900 dark:text-white text-base">All Verified Skills in Your Profile</h3>
        {(!userSkills || userSkills.length === 0) ? (
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Upload your resume in Profile to extract your skills automatically, or click "Add Custom Skill" above.
          </p>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
            {userSkills.map((us) => (
              <div
                key={us.id}
                className="flex items-center justify-between p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 text-xs"
              >
                <div>
                  <div className="font-bold text-slate-900 dark:text-white">{us.skill_name}</div>
                  <div className="text-[10px] text-slate-400 uppercase capitalize">{us.proficiency_level}</div>
                </div>
                <button
                  onClick={() => deleteSkillMutation.mutate(us.id)}
                  className="text-slate-400 hover:text-rose-500 transition-colors p-1"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Add Skill Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm animate-fade-in">
          <div className="bg-white dark:bg-slate-900 rounded-2xl max-w-sm w-full border border-slate-200 dark:border-slate-800 p-6 shadow-2xl">
            <h3 className="text-base font-bold text-slate-900 dark:text-white mb-3">Add Custom Skill</h3>
            <form onSubmit={handleAddSkill} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Skill Name
                </label>
                <input
                  type="text"
                  required
                  value={newSkillName}
                  onChange={(e) => setNewSkillName(e.target.value)}
                  placeholder="e.g. PyTorch, System Design, GraphQL"
                  className="w-full px-3.5 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-xs sm:text-sm text-slate-900 dark:text-white focus:outline-none focus:border-brand-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Proficiency Level
                </label>
                <select
                  value={newSkillLevel}
                  onChange={(e) => setNewSkillLevel(e.target.value)}
                  className="w-full px-3.5 py-2 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-xs text-slate-900 dark:text-white focus:outline-none focus:border-brand-500"
                >
                  <option value="beginner">Beginner</option>
                  <option value="intermediate">Intermediate</option>
                  <option value="advanced">Advanced</option>
                  <option value="expert">Expert</option>
                </select>
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 text-xs font-medium text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={addSkillMutation.isPending || !newSkillName.trim()}
                  className="px-4 py-2 text-xs font-medium bg-brand-600 hover:bg-brand-700 text-white rounded-xl shadow-sm"
                >
                  Add Skill
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
