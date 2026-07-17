import React, { useState, useEffect, useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import { 
  Repeat, Plus, Trash2, Calendar, Clock, ArrowRight, User as UserIcon
} from 'lucide-react';
import api from '../api';
import { format } from 'date-fns';

const RecurringTasks = () => {
  const { user } = useContext(AuthContext);
  const [templates, setTemplates] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [error, setError] = useState('');

  // Form State
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState('medium');
  const [cadence, setCadence] = useState('daily');
  const [nextRunAt, setNextRunAt] = useState('');
  const [assigneeId, setAssigneeId] = useState('');

  const fetchTemplates = async () => {
    try {
      setLoading(true);
      const res = await api.get('/recurring');
      setTemplates(res.data.items);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchUsers = async () => {
    try {
      const res = await api.get('/auth/users', { baseURL: '' });
      setUsers(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchTemplates();
    fetchUsers();
  }, []);

  const handleCreateTemplate = async (e) => {
    e.preventDefault();
    setError('');
    
    // Ensure datetime is valid ISO
    let formattedDate;
    try {
      formattedDate = new Date(nextRunAt).toISOString();
    } catch {
      setError('Invalid date');
      return;
    }

    try {
      await api.post('/recurring', {
        title_template: title,
        description_template: description || null,
        priority: priority,
        cadence: cadence,
        next_run_at: formattedDate,
        assignee_id: assigneeId || null
      });
      setIsModalOpen(false);
      setTitle('');
      setDescription('');
      setNextRunAt('');
      setAssigneeId('');
      fetchTemplates();
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create template');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to delete this recurring task template?")) return;
    try {
      await api.delete(`/recurring/${id}`);
      fetchTemplates();
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) return <div>Loading...</div>;

  const isManager = user?.role === 'manager' || user?.role === 'admin';

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center">
            <Repeat className="w-6 h-6 mr-2 text-primary-500" />
            Recurring Tasks
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage templates that automatically generate tasks on a schedule.
          </p>
        </div>
        {isManager && (
          <button 
            onClick={() => setIsModalOpen(true)}
            className="flex items-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors shadow-sm"
          >
            <Plus className="w-5 h-5 mr-1" />
            New Template
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {templates.map(tmpl => (
          <div key={tmpl.id} className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-shadow">
            <div className="p-5">
              <div className="flex justify-between items-start mb-4">
                <div className={`px-2.5 py-1 rounded-full text-xs font-medium uppercase ${
                  tmpl.cadence === 'daily' ? 'bg-blue-100 text-blue-800' :
                  tmpl.cadence === 'weekly' ? 'bg-purple-100 text-purple-800' :
                  'bg-orange-100 text-orange-800'
                }`}>
                  {tmpl.cadence}
                </div>
                {isManager && (
                  <button onClick={() => handleDelete(tmpl.id)} className="text-gray-400 hover:text-red-500 transition-colors">
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
              </div>
              
              <h3 className="text-lg font-semibold text-gray-900 mb-1">{tmpl.title_template}</h3>
              {tmpl.description_template && (
                <p className="text-sm text-gray-500 line-clamp-2 mb-4">{tmpl.description_template}</p>
              )}
              
              <div className="space-y-2 mt-4 pt-4 border-t border-gray-100">
                <div className="flex items-center text-sm text-gray-600">
                  <UserIcon className="w-4 h-4 mr-2 text-gray-400" />
                  {tmpl.assignee ? tmpl.assignee.name : 'Unassigned'}
                </div>
                <div className="flex items-center text-sm text-gray-600">
                  <Calendar className="w-4 h-4 mr-2 text-gray-400" />
                  Next run: <span className="font-medium ml-1 text-gray-900">{format(new Date(tmpl.next_run_at), 'MMM d, yyyy')}</span>
                </div>
              </div>
            </div>
          </div>
        ))}
        {templates.length === 0 && (
          <div className="col-span-full py-12 text-center text-gray-500 bg-white rounded-xl border border-dashed border-gray-300">
            <Repeat className="w-12 h-12 mx-auto text-gray-300 mb-3" />
            <p>No recurring templates found.</p>
          </div>
        )}
      </div>

      {isModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex flex-col items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-xl relative max-h-screen overflow-y-auto">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Create Recurring Template</h2>
            {error && <div className="mb-4 p-3 bg-red-50 text-red-700 text-sm rounded-lg">{error}</div>}
            
            <form onSubmit={handleCreateTemplate} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Task Title Template *</label>
                <input 
                  type="text" required value={title} onChange={(e) => setTitle(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                  placeholder="e.g. Daily Standup Report"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description (Optional)</label>
                <textarea 
                  value={description} onChange={(e) => setDescription(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                  rows={2}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Cadence *</label>
                  <select 
                    value={cadence} onChange={(e) => setCadence(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="daily">Daily</option>
                    <option value="weekly">Weekly</option>
                    <option value="monthly">Monthly</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Priority *</label>
                  <select 
                    value={priority} onChange={(e) => setPriority(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Assign To</label>
                <select 
                  value={assigneeId} onChange={(e) => setAssigneeId(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                >
                  <option value="">-- Unassigned --</option>
                  {users.map(u => (
                    <option key={u.id} value={u.id}>{u.name} ({u.email})</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">First Run Date & Time *</label>
                <input 
                  type="datetime-local" required value={nextRunAt} onChange={(e) => setNextRunAt(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                />
              </div>

              <div className="flex justify-end space-x-3 pt-4 mt-6 border-t border-gray-100">
                <button type="button" onClick={() => setIsModalOpen(false)} className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
                  Cancel
                </button>
                <button type="submit" className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors shadow-sm">
                  Save Template
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default RecurringTasks;
