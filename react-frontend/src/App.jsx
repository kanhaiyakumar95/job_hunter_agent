import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, X, Check, Download, Briefcase, FileText, ExternalLink, LogOut } from 'lucide-react';
import DOMPurify from 'dompurify';
import JobCard from './components/JobCard';
import Login from './components/Login';
import './index.css';

// Validates whether a given URL safely belongs to the http or https web protocol
const isSafeUrl = (url) => {
  if (!url || typeof url !== 'string' || url === 'nan') return false;
  try {
    const parsed = new URL(url);
    return parsed.protocol === 'http:' || parsed.protocol === 'https:';
  } catch {
    return false;
  }
};

function App() {
  const [view, setView] = useState('start'); // 'start', 'loading', 'results'
  const [query, setQuery] = useState('');
  const [jobs, setJobs] = useState([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [activeResumeHTML, setActiveResumeHTML] = useState('');
  const [activeResumeMarkdown, setActiveResumeMarkdown] = useState('');
  const [activeJobUrl, setActiveJobUrl] = useState('');

  // Auth state
  const [authToken, setAuthToken] = useState(localStorage.getItem('auth_token'));

  // Loading states
  const [isSearching, setIsSearching] = useState(false);
  const [applyingJobId, setApplyingJobId] = useState(null);
  const [applyProgress, setApplyProgress] = useState('');

  // Initiates search query against backend scraping API and updates active jobs feed
  const handleSearch = async () => {
    setView('loading');
    setIsSearching(true);

    try {
      const searchVal = query.trim() || 'Senior Java Engineer Pune';
      const response = await fetch('/api/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({ query: searchVal })
      });

      if (response.status === 401) {
        setAuthToken(null);
        localStorage.removeItem('auth_token');
        return;
      }
      const result = await response.json();

      setJobs(result.data || []);
      setView('results');
    } catch (err) {
      console.error(err);
      alert("Error fetching jobs from the server.");
      setView('start');
    } finally {
      setIsSearching(false);
    }
  };

  // Sends ignore request to backend and optimistically removes job card from viewport
  const handleIgnore = async (jobId) => {
    // Optimistically remove from UI
    setJobs(jobs.filter(j => j.id !== jobId));

    try {
      await fetch('/api/ignore', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({ job_id: jobId, job_title: "", job_description: "", job_url: "" })
      });
    } catch (err) {
      console.error("Error ignoring job:", err);
    }
  };

  // Triggers the browser's native print dialog to save the rendered tailored resume as PDF
  const downloadResume = () => {
    // We use the browser's native print engine for perfect ATS-readable PDFs
    window.print();
  };

  // Submits job to AI pipeline for fit evaluation, resume tailoring, and auto-application
  const handleApply = async (job) => {
    setApplyingJobId(job.id);
    setApplyProgress('Analyzing & Tailoring Resume...');

    try {
      const response = await fetch('/api/apply', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({
          job_id: job.id,
          job_title: job.title,
          job_description: job.description,
          job_url: job.url
        })
      });
      const result = await response.json();

      if (result.status === 'success') {
        let md = result.data.tailored_resume;
        if (!md || md === "Error") md = "# AI determined this job wasn't a good fit to apply to.";

        let html = md
          .replace(/^### (.*$)/gim, '<h3>$1</h3>')
          .replace(/^## (.*$)/gim, '<h2>$1</h2>')
          .replace(/^# (.*$)/gim, '<h1>$1</h1>')
          .replace(/\*\*(.*)\*\*/gim, '<b>$1</b>')
          .replace(/\n/gim, '<br>');

        setActiveResumeMarkdown(md);
        setActiveResumeHTML(DOMPurify.sanitize(html));
        setActiveJobUrl(job.url);
        setModalOpen(true);

        // Remove from list since we applied
        setJobs(jobs.filter(j => j.id !== job.id));
      } else {
        alert("Failed to apply.");
      }
    } catch (err) {
      console.error(err);
      alert("Error applying to job.");
    } finally {
      setApplyingJobId(null);
      setApplyProgress('');
    }
  };

  // Clears stored authentication session and returns user to login view
  const handleLogout = () => {
    setAuthToken(null);
    localStorage.removeItem('auth_token');
  };

  if (!authToken) {
    return <Login onLoginSuccess={setAuthToken} />;
  }

  return (
    <>
      <header className="header" style={{ padding: '1rem 2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--glass-border)', background: 'var(--glass-bg)' }}>
        <div className="logo" style={{ fontWeight: 'bold', fontSize: '1.2rem', color: 'var(--accent-primary)' }}>
          🤖 JobHunter
        </div>
        <button onClick={handleLogout} className="secondary-btn" style={{ padding: '0.5rem 1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <LogOut size={16} /> Logout
        </button>
      </header>

      <div className="background-elements">
        <div className="blob blob-1"></div>
        <div className="blob blob-2"></div>
      </div>

      <main id="app-container">
        <AnimatePresence mode="wait">
          {view === 'start' && (
            <motion.section
              key="start"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.5 }}
              id="start-page"
              className="view active"
            >
              <header>
                <div className="logo">Hunter<span>.AI</span></div>
              </header>
              <div className="hero-content">
                <motion.h1
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.2, duration: 0.5 }}
                >
                  Land your dream job, <span>on autopilot.</span>
                </motion.h1>
                <motion.p
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.4 }}
                >
                  Our agent searches for roles matching your profile and generates a hyper-tailored resume for each job description.
                </motion.p>

                <motion.div
                  className="search-bar"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.6 }}
                >
                  <input
                    type="text"
                    id="search-input"
                    placeholder="e.g. Senior Java Spring Boot Pune"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                  />
                  <button id="start-search-btn" className="primary-btn" onClick={handleSearch} disabled={isSearching}>
                    <Search size={18} />
                    {isSearching ? 'Searching...' : 'Search Jobs'}
                  </button>
                </motion.div>
              </div>
            </motion.section>
          )}

          {view === 'loading' && (
            <motion.section
              key="loading"
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0 }}
              id="loading-page"
              className="view active"
              style={{ justifyContent: 'center', alignItems: 'center' }}
            >
              <div className="glass-card loading-card">
                <div className="spinner"></div>
                <h2 id="loading-text">Scraping Job Boards...</h2>
                <p className="subtitle">Finding the latest matches for you.</p>
              </div>
            </motion.section>
          )}

          {view === 'results' && (
            <motion.section
              key="results"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              id="results-page"
              className="view active"
            >
              <header className="results-header">
                <div className="logo">Hunter<span>.AI</span></div>
                <button id="new-search-btn" className="secondary-btn" onClick={() => setView('start')}>New Search</button>
              </header>

              <div className="results-container">
                <motion.h2
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                >
                  Recommended Roles ({jobs.length})
                </motion.h2>
                {jobs.length === 0 && (
                  <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                    No new jobs found. Try a different search.
                  </motion.p>
                )}

                <div className="job-list" id="job-list">
                  <AnimatePresence>
                    {jobs.map((job, index) => (
                      <JobCard
                        key={job.id}
                        job={job}
                        index={index}
                        applyingJobId={applyingJobId}
                        applyProgress={applyProgress}
                        onIgnore={handleIgnore}
                        onApply={handleApply}
                      />
                    ))}
                  </AnimatePresence>
                </div>
              </div>
            </motion.section>
          )}
        </AnimatePresence>
      </main>

      {/* Resume Modal */}
      <AnimatePresence>
        {modalOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            id="resume-modal"
            className="modal active"
            onClick={(e) => { if (e.target.id === 'resume-modal') setModalOpen(false); }}
          >
            <motion.div
              initial={{ scale: 0.8, y: 50 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.8, y: 50 }}
              className="modal-content glass-card"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="modal-header">
                <h3><FileText size={20} style={{ display: 'inline', marginRight: '8px', verticalAlign: 'middle' }} />Tailored Resume</h3>
                <button className="close-btn" onClick={() => setModalOpen(false)}>&times;</button>
              </div>
              <div id="resume-pdf-content" className="modal-body" dangerouslySetInnerHTML={{ __html: activeResumeHTML }}></div>
              <div className="modal-footer" style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
                <button className="secondary-btn" onClick={downloadResume}>
                  <Download size={18} /> Download (.pdf)
                </button>
                {isSafeUrl(activeJobUrl) && (
                  <a href={activeJobUrl} target="_blank" rel="noopener noreferrer" className="primary-btn" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    Apply Now <ExternalLink size={18} />
                  </a>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

export default App;
