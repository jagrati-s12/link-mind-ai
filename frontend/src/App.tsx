import React, { useState } from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { useQueryClient } from '@tanstack/react-query';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { CaptureModal } from './components/CaptureModal';

// Pages
import { Dashboard } from './pages/Dashboard';
import { Inbox } from './pages/Inbox';
import { Resources } from './pages/Resources';
import { Courses } from './pages/Courses';
import { Internships } from './pages/Internships';
import { Hackathons } from './pages/Hackathons';
import { Collections } from './pages/Collections';
import { CollectionDetail } from './pages/CollectionDetail';
import { ResourceDetail } from './pages/ResourceDetail';
import { Skills } from './pages/Skills';
import { Roadmaps } from './pages/Roadmaps';
import { Applications } from './pages/Applications';
import { Assistant } from './pages/Assistant';
import { Profile } from './pages/Profile';
import { Settings } from './pages/Settings';

export const App: React.FC = () => {
  const [isCaptureOpen, setIsCaptureOpen] = useState(false);
  const queryClient = useQueryClient();

  const handleCaptureSuccess = () => {
    queryClient.invalidateQueries();
  };

  return (
    <div className="flex h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 font-sans overflow-hidden">
      {/* Sidebar navigation */}
      <Sidebar onOpenCapture={() => setIsCaptureOpen(true)} />

      {/* Main content pane */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Header onOpenCapture={() => setIsCaptureOpen(true)} />

        <main className="flex-1 overflow-y-auto px-6 py-8 custom-scrollbar">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard onOpenCapture={() => setIsCaptureOpen(true)} />} />
            <Route path="/inbox" element={<Inbox onOpenCapture={() => setIsCaptureOpen(true)} />} />
            <Route path="/resources" element={<Resources onOpenCapture={() => setIsCaptureOpen(true)} />} />
            <Route path="/courses" element={<Courses onOpenCapture={() => setIsCaptureOpen(true)} />} />
            <Route path="/internships" element={<Internships onOpenCapture={() => setIsCaptureOpen(true)} />} />
            <Route path="/hackathons" element={<Hackathons onOpenCapture={() => setIsCaptureOpen(true)} />} />
            <Route path="/collections" element={<Collections />} />
            <Route path="/collections/:id" element={<CollectionDetail />} />
            <Route path="/resources/:id" element={<ResourceDetail />} />
            <Route path="/skills" element={<Skills />} />
            <Route path="/roadmaps" element={<Roadmaps />} />
            <Route path="/applications" element={<Applications />} />
            <Route path="/assistant" element={<Assistant />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </main>
      </div>

      {/* Global Quick Capture Modal */}
      <CaptureModal
        isOpen={isCaptureOpen}
        onClose={() => setIsCaptureOpen(false)}
        onSuccess={handleCaptureSuccess}
      />
    </div>
  );
};
export default App;
