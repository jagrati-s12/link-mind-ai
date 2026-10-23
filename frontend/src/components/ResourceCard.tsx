import React from 'react';
import { Link } from 'react-router-dom';
import { ExternalLink, Calendar, MapPin, Building, Sparkles, Folder, ArrowRight } from 'lucide-react';
import { Resource } from '../types';

interface ResourceCardProps {
  resource: Resource;
  onUpdateStatus?: (resourceId: number, status: string) => void;
}

export const ResourceCard: React.FC<ResourceCardProps> = ({ resource }) => {
  const isCourse = resource.type === 'course' || resource.type === 'certification';
  const score = resource.recommendation?.fit_score;

  const getTypeBadgeClass = (type: string) => {
    switch (type) {
      case 'internship':
        return 'bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-400 border-amber-200 dark:border-amber-900/50';
      case 'hackathon':
        return 'bg-orange-50 text-orange-700 dark:bg-orange-950/40 dark:text-orange-400 border-orange-200 dark:border-orange-900/50';
      case 'course':
        return 'bg-indigo-50 text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-400 border-indigo-200 dark:border-indigo-900/50';
      case 'certification':
        return 'bg-purple-50 text-purple-700 dark:bg-purple-950/40 dark:text-purple-400 border-purple-200 dark:border-purple-900/50';
      case 'project':
        return 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400 border-emerald-200 dark:border-emerald-900/50';
      default:
        return 'bg-blue-50 text-blue-700 dark:bg-blue-950/40 dark:text-blue-400 border-blue-200 dark:border-blue-900/50';
    }
  };

  return (
    <div className="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-5 hover:border-brand-500/50 dark:hover:border-brand-500/40 hover:shadow-md transition-all duration-200 flex flex-col justify-between group">
      <div>
        {/* Header row: type badge & match score */}
        <div className="flex items-center justify-between gap-2 mb-3">
          <span className={`text-[11px] font-semibold uppercase tracking-wider px-2.5 py-0.5 rounded-full border ${getTypeBadgeClass(resource.type)}`}>
            {resource.type}
          </span>

          {score !== undefined && score !== null && (
            <div className={`flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold ${
              score >= 75
                ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-900'
                : score >= 50
                ? 'bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-900'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400'
            }`}>
              <Sparkles className="w-3 h-3" />
              <span>{Math.round(score)}% Match</span>
            </div>
          )}
        </div>

        {/* Title */}
        <Link to={`/resources/${resource.id}`} className="block">
          <h4 className="font-semibold text-slate-900 dark:text-white text-base group-hover:text-brand-600 dark:group-hover:text-brand-400 transition-colors line-clamp-2">
            {resource.title}
          </h4>
        </Link>

        {/* Organization / Provider */}
        {resource.organization && (
          <div className="flex items-center space-x-1.5 text-xs text-slate-500 dark:text-slate-400 mt-1">
            <Building className="w-3.5 h-3.5" />
            <span className="font-medium">{resource.organization}</span>
          </div>
        )}

        {/* Description snippet */}
        {resource.description && (
          <p className="text-xs text-slate-600 dark:text-slate-400 mt-2.5 line-clamp-2 leading-relaxed">
            {resource.description}
          </p>
        )}

        {/* Metadata row: location & deadline */}
        <div className="flex flex-wrap items-center gap-3 mt-3.5 text-xs text-slate-500 dark:text-slate-400">
          {resource.location && (
            <div className="flex items-center space-x-1">
              <MapPin className="w-3.5 h-3.5" />
              <span>{resource.location}</span>
            </div>
          )}
          {resource.deadline && (
            <div className="flex items-center space-x-1 text-rose-600 dark:text-rose-400 font-medium">
              <Calendar className="w-3.5 h-3.5" />
              <span>{resource.deadline}</span>
            </div>
          )}
        </div>

        {/* Skills pills */}
        {((isCourse ? resource.taught_skills : resource.required_skills) || []).length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-3.5">
            {((isCourse ? resource.taught_skills : resource.required_skills) || []).slice(0, 4).map((skill, idx) => (
              <span
                key={idx}
                className="text-[11px] px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 font-medium"
              >
                {skill}
              </span>
            ))}
            {((isCourse ? resource.taught_skills : resource.required_skills) || []).length > 4 && (
              <span className="text-[10px] px-1.5 py-0.5 text-slate-400 font-medium">
                +{((isCourse ? resource.taught_skills : resource.required_skills) || []).length - 4} more
              </span>
            )}
          </div>
        )}

        {/* Collections */}
        {resource.collections && resource.collections.length > 0 && (
          <div className="flex flex-wrap items-center gap-1.5 mt-3 pt-3 border-t border-slate-100 dark:border-slate-800/60">
            {resource.collections.map((col) => (
              <Link
                key={col.id}
                to={`/collections/${col.id}`}
                className="flex items-center space-x-1 text-[10px] font-medium px-2 py-0.5 rounded-md bg-slate-50 dark:bg-slate-800/80 text-slate-500 dark:text-slate-400 hover:text-brand-600 transition-colors"
              >
                <Folder className="w-2.5 h-2.5" />
                <span>{col.name}</span>
              </Link>
            ))}
          </div>
        )}
      </div>

      {/* Footer controls */}
      <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between">
        <Link
          to={`/resources/${resource.id}`}
          className="text-xs font-semibold text-brand-600 dark:text-brand-400 hover:underline flex items-center space-x-1"
        >
          <span>View Details</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>

        {resource.direct_url && (
          <a
            href={resource.direct_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center space-x-1 text-xs text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors"
          >
            <span>Direct Link</span>
            <ExternalLink className="w-3 h-3" />
          </a>
        )}
      </div>
    </div>
  );
};
