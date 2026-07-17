import React, { useState, useEffect, useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import api from '../api';
import { format } from 'date-fns';
import { Search, Plus, X } from 'lucide-react';
import TaskComments from '../components/TaskComments';
import TaskActivity from '../components/TaskActivity';
import TaskAttachments from '../components/TaskAttachments';

const Tasks = () => {
  const { user } = useContext(AuthContext);
  const [tasks, setTasks] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentTab, setCurrentTab] = useState('to_do');
  
  // Filtering state
  const [searchQuery, setSearchQuery] = useState('');
  const [filterPriority, setFilterPriority] = useState('all');
  const [filterAssignee, setFilterAssignee] = useState('all');
  
  // Modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedTask, setSelectedTask] = useState(null);
  const [formData, setFormData] = useState({ 
    title: '', 
    description: '', 
    priority: 'medium', 
    status: 'to_do',
    assignee_id: '',
    due_date: ''
  });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchData();
  }, [currentTab]);

  const fetchData = async () => {
    setLoading(true);
    try {
      let url = '/tasks/';
      if (currentTab === 'archived') {
        url += '?is_deleted=true';
      } else {
        url += `?status=${currentTab}`;
      }
      
      const [tasksRes, usersRes] = await Promise.all([
        api.get(url),
        api.get('/auth/users', { baseURL: '' })
      ]);
      setTasks(tasksRes.data.items);
      setUsers(usersRes.data);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const handleOpenModal = (task = null) => {
    if (task) {
      setSelectedTask(task);
      setFormData({
        title: task.title,
        description: task.description || '',
        priority: task.priority,
        status: task.status,
        assignee_id: task.assignee_id || '',
        due_date: task.due_date ? task.due_date : ''
      });
    } else {
      setSelectedTask(null);
      setFormData({ 
        title: '', 
        description: '', 
        priority: 'medium', 
        status: 'to_do',
        assignee_id: user?.id || '',
        due_date: '' 
      });
    }
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedTask(null);
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    
    // Clean up empty strings to null for backend
    const payload = {
      ...formData,
      assignee_id: formData.assignee_id || null,
      due_date: formData.due_date || null
    };

    try {
      if (selectedTask) {
        await api.patch(`/tasks/${selectedTask.id}`, payload);
      } else {
        await api.post('/tasks/', payload);
      }
      fetchData();
      handleCloseModal();
    } catch (err) {
      console.error(err);
      alert('Failed to save task.');
    }
    setSaving(false);
  };

  const handleDelete = async () => {
    if (!window.confirm("Are you sure you want to delete this task?")) return;
    try {
      await api.delete(`/tasks/${selectedTask.id}`);
      fetchData();
      handleCloseModal();
    } catch (err) {
      console.error(err);
      alert('Failed to delete task.');
    }
  };

  const statusColors = {
    'to_do': 'bg-gray-100 text-gray-800',
    'in_progress': 'bg-blue-100 text-blue-800',
    'completed': 'bg-green-100 text-green-800'
  };

  const priorityColors = {
    'low': 'bg-blue-50 text-blue-700',
    'medium': 'bg-yellow-50 text-yellow-700',
    'high': 'bg-red-50 text-red-700'
  };

  const getAssigneeName = (id) => {
    if (!id) return 'Unassigned';
    const u = users.find(u => u.id === id);
    return u ? u.name : 'Unknown';
  };

  const filteredTasks = tasks.filter(task => {
    const matchesSearch = task.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          (task.description && task.description.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesPriority = filterPriority === 'all' || task.priority === filterPriority;
    const matchesAssignee = filterAssignee === 'all' || task.assignee_id === filterAssignee;
    return matchesSearch && matchesPriority && matchesAssignee;
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <h1 className="text-2xl font-bold text-gray-900">Tasks</h1>
        <div className="flex w-full md:w-auto flex-wrap gap-3">
          <div className="relative flex-1 md:w-48">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input 
              type="text" 
              placeholder="Search..." 
              className="input-field pl-10" 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <select 
            className="input-field md:w-36"
            value={filterPriority}
            onChange={(e) => setFilterPriority(e.target.value)}
          >
            <option value="all">All Priorities</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
          <select 
            className="input-field md:w-40"
            value={filterAssignee}
            onChange={(e) => setFilterAssignee(e.target.value)}
          >
            <option value="all">All Assignees</option>
            <option value="">Unassigned</option>
            {users.map(u => (
              <option key={u.id} value={u.id}>{u.name}</option>
            ))}
          </select>
          <button onClick={() => handleOpenModal()} className="btn-primary flex items-center shrink-0">
            <Plus className="h-5 w-5 mr-1" /> New Task
          </button>
        </div>
      </div>

      <div className="flex space-x-1 bg-gray-100 p-1 rounded-xl w-full md:w-fit">
        {['to_do', 'in_progress', 'completed', 'archived'].map((tab) => (
          <button
            key={tab}
            onClick={() => setCurrentTab(tab)}
            className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
              currentTab === tab 
                ? 'bg-white text-gray-900 shadow-sm' 
                : 'text-gray-500 hover:text-gray-700 hover:bg-gray-200/50'
            }`}
          >
            {tab.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="p-8 text-center text-gray-500">Loading tasks...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredTasks.map(task => (
            <div 
              key={task.id} 
              onClick={() => handleOpenModal(task)}
              className="glass-card p-5 hover:shadow-2xl hover:-translate-y-1 transition-all duration-300 cursor-pointer flex flex-col"
            >
              <div className="flex justify-between items-start mb-3">
                <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${priorityColors[task.priority] || priorityColors.medium}`}>
                  {task.priority.toUpperCase()}
                </span>
                <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${statusColors[task.status] || statusColors.to_do}`}>
                  {task.status.replace('_', ' ').toUpperCase()}
                </span>
              </div>
              <h3 className="text-lg font-bold text-gray-900 mb-2 truncate">{task.title}</h3>
              <p className="text-sm text-gray-500 line-clamp-2 mb-4 flex-grow">
                {task.description || 'No description provided.'}
              </p>
              <div className="flex items-center justify-between pt-4 border-t border-gray-100">
                <div className="text-xs font-medium text-gray-600 bg-gray-50 px-2 py-1 rounded-md max-w-[120px] truncate" title={getAssigneeName(task.assignee_id)}>
                  {getAssigneeName(task.assignee_id)}
                </div>
                <div className="text-xs text-gray-400">
                  {task.due_date ? format(new Date(task.due_date), 'MMM d, yyyy') : 'No due date'}
                </div>
              </div>
            </div>
          ))}
          {filteredTasks.length === 0 && (
            <div className="col-span-full py-12 text-center text-gray-500 bg-white rounded-2xl border border-dashed border-gray-300">
              No tasks found. Try adjusting your filters or create a new task!
            </div>
          )}
        </div>
      )}

      {isModalOpen && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl w-full max-w-2xl shadow-xl overflow-hidden flex flex-col max-h-[90vh]">
            <div className="flex justify-between items-center p-6 border-b border-gray-100 shrink-0">
              <h2 className="text-xl font-bold text-gray-900">{selectedTask ? 'Edit Task' : 'New Task'}</h2>
              <button onClick={handleCloseModal} className="text-gray-400 hover:text-gray-600 transition-colors">
                <X className="h-6 w-6" />
              </button>
            </div>
            
            <div className="p-6 overflow-y-auto space-y-4">
              <form id="task-form" onSubmit={handleSave} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
                  <input 
                    type="text" 
                    required
                    className="input-field" 
                    value={formData.title} 
                    onChange={e => setFormData({...formData, title: e.target.value})}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                  <textarea 
                    className="input-field min-h-[100px]" 
                    value={formData.description} 
                    onChange={e => setFormData({...formData, description: e.target.value})}
                  />
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
                    <select 
                      className="input-field" 
                      value={formData.priority}
                      onChange={e => setFormData({...formData, priority: e.target.value})}
                    >
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Status
                      {selectedTask && selectedTask.assignee_id !== user.id && (
                        <span className="ml-2 text-xs text-red-500 font-normal">(Only assignee can modify)</span>
                      )}
                    </label>
                    <select 
                      className="input-field" 
                      value={formData.status}
                      onChange={e => setFormData({...formData, status: e.target.value})}
                      disabled={selectedTask && selectedTask.assignee_id !== user.id}
                    >
                      <option value="to_do">To Do</option>
                      <option value="in_progress">In Progress</option>
                      <option value="completed">Completed</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Assignee
                      {user?.role === 'member' && (
                        <span className="ml-2 text-xs text-red-500 font-normal">(Manager approval required)</span>
                      )}
                    </label>
                    <select 
                      className="input-field" 
                      value={formData.assignee_id}
                      onChange={e => setFormData({...formData, assignee_id: e.target.value})}
                      required
                      disabled={user?.role === 'member'}
                    >
                      <option value="" disabled>-- Select Assignee --</option>
                      {users.map(u => (
                        <option key={u.id} value={u.id}>{u.name} ({u.email})</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Due Date
                      {selectedTask && user?.role === 'member' && (
                        <span className="ml-2 text-xs text-red-500 font-normal">(Manager approval required)</span>
                      )}
                    </label>
                    <input 
                      type="date" 
                      className="input-field" 
                      value={formData.due_date}
                      onChange={e => setFormData({...formData, due_date: e.target.value})}
                      disabled={selectedTask && user?.role === 'member'}
                    />
                  </div>
                </div>
              </form>
              
              {/* Task Extras - only show if editing an existing task */}
              {selectedTask && (
                <div className="mt-8 pt-8 border-t border-gray-100">
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    <div className="space-y-8">
                      <TaskAttachments taskId={selectedTask.id} users={users} />
                      <TaskActivity taskId={selectedTask.id} users={users} />
                    </div>
                    <div>
                      <TaskComments taskId={selectedTask.id} users={users} />
                    </div>
                  </div>
                </div>
              )}
            </div>
            
            <div className="p-6 bg-gray-50 border-t border-gray-100 flex justify-between items-center space-x-3 shrink-0">
              <div>
                {selectedTask && user?.role === 'manager' && currentTab !== 'archived' && (
                  <button type="button" onClick={handleDelete} className="px-4 py-2 text-red-600 hover:bg-red-50 rounded-xl transition-colors font-medium">
                    Delete / Archive
                  </button>
                )}
                {selectedTask && currentTab === 'archived' && (
                  <span className="text-sm font-medium text-red-500">This task is archived.</span>
                )}
              </div>
              <div className="flex space-x-3">
                <button type="button" onClick={handleCloseModal} className="px-4 py-2 text-gray-600 hover:bg-gray-200 rounded-xl transition-colors font-medium">
                  Cancel
                </button>
                <button type="submit" form="task-form" disabled={saving || currentTab === 'archived'} className="btn-primary">
                  {saving ? 'Saving...' : 'Save Task'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Tasks;
