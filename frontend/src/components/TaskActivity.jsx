import React, { useState, useEffect } from 'react';
import api from '../api';
import { format } from 'date-fns';
import { Activity } from 'lucide-react';

const TaskActivity = ({ taskId, users }) => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLogs();
  }, [taskId]);

  const fetchLogs = async () => {
    try {
      const res = await api.get(`/tasks/${taskId}/activity`);
      setLogs(res.data);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const getAuthorName = (id) => {
    const u = users.find(u => u.id === id);
    return u ? u.name : 'System';
  };

  if (loading) return <div className="text-sm text-gray-500 py-4">Loading activity...</div>;

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-bold text-gray-900 flex items-center">
        <Activity className="h-5 w-5 mr-2 text-primary-500" />
        Activity Log
      </h3>
      
      <div className="space-y-3 max-h-64 overflow-y-auto pr-2 relative before:absolute before:inset-0 before:ml-2 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-gray-200 before:to-transparent">
        {logs.length === 0 ? (
          <p className="text-sm text-gray-500 italic">No activity recorded.</p>
        ) : (
          logs.map(log => (
            <div key={log.id} className="relative flex items-center space-x-3 mb-2">
              <div className="h-4 w-4 bg-primary-100 rounded-full border-2 border-primary-500 shrink-0 z-10 mx-0.5"></div>
              <div className="flex-1 bg-white p-3 rounded-lg shadow-sm border border-gray-100 text-sm z-10">
                <span className="font-semibold text-gray-900">{getAuthorName(log.actor_id)}</span>
                <span className="text-gray-500 ml-1">
                  updated <span className="font-medium text-gray-700">{log.field_changed.replace('_', ' ')}</span>
                  {log.old_value && <span> from <span className="line-through">{log.old_value}</span></span>}
                  {log.new_value && <span> to <span className="font-medium">{log.new_value}</span></span>}
                </span>
                <div className="text-xs text-gray-400 mt-1">{format(new Date(log.created_at), 'MMM d, h:mm a')}</div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default TaskActivity;
