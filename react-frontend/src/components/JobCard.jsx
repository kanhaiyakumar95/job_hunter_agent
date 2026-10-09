import React from 'react';
import { motion } from 'framer-motion';
import { Briefcase, X, Check } from 'lucide-react';

export default function JobCard({ job, index, applyingJobId, applyProgress, onIgnore, onApply }) {
  return (
    <motion.div 
      layout
      initial={{ opacity: 0, scale: 0.8, y: 50 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.5, transition: { duration: 0.2 } }}
      transition={{ delay: index * 0.1 }}
      className="glass-card job-card"
    >
      <div className="job-header">
        <div>
          <h3 className="job-title">
            <Briefcase size={16} style={{display:'inline', marginRight:'8px'}}/>
            {job.title}
          </h3>
          <div className="job-company">Found on {new Date(job.first_viewed).toLocaleDateString()}</div>
        </div>
      </div>
      <div className="job-description" style={{maxHeight: '150px', overflow: 'hidden', textOverflow: 'ellipsis'}}>
        {job.description.substring(0, 300)}...
      </div>
      
      {applyingJobId === job.id ? (
        <motion.div 
          initial={{ opacity: 0 }} 
          animate={{ opacity: 1 }}
          style={{marginTop: 'auto', textAlign: 'center', color: 'var(--accent-primary)', fontWeight: 'bold'}}
        >
          <div className="spinner" style={{width: '20px', height: '20px', borderWidth: '2px', margin: '0 auto 10px'}}></div>
          {applyProgress}
        </motion.div>
      ) : (
        <div className="job-actions">
          <button className="secondary-btn" onClick={() => onIgnore(job.id)}>
            <X size={16} /> Ignore
          </button>
          <button className="primary-btn" onClick={() => onApply(job)}>
            <Check size={16} /> Auto-Apply
          </button>
        </div>
      )}
    </motion.div>
  );
}
