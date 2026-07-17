import React, { useState, useEffect } from 'react';
import api from '../api';
import { format } from 'date-fns';
import { MessageSquare, Send } from 'lucide-react';

const TaskComments = ({ taskId, users }) => {
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchComments();
  }, [taskId]);

  const fetchComments = async () => {
    try {
      const res = await api.get(`/tasks/${taskId}/comments`);
      setComments(res.data);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!newComment.trim()) return;
    try {
      await api.post(`/tasks/${taskId}/comments`, { body: newComment });
      setNewComment('');
      fetchComments();
    } catch (err) {
      console.error(err);
    }
  };

  const getAuthorName = (id) => {
    const u = users.find(u => u.id === id);
    return u ? u.name : 'Unknown User';
  };

  if (loading) return <div className="text-sm text-gray-500 py-4">Loading comments...</div>;

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-bold text-gray-900 flex items-center">
        <MessageSquare className="h-5 w-5 mr-2 text-primary-500" />
        Comments
      </h3>
      
      <div className="space-y-4 max-h-64 overflow-y-auto pr-2">
        {comments.length === 0 ? (
          <p className="text-sm text-gray-500 italic">No comments yet. Be the first to start the discussion!</p>
        ) : (
          comments.map(c => (
            <div key={c.id} className="bg-gray-50 p-3 rounded-xl border border-gray-100">
              <div className="flex justify-between items-start mb-1">
                <span className="text-xs font-bold text-gray-900">{getAuthorName(c.author_id)}</span>
                <span className="text-xs text-gray-500">{format(new Date(c.created_at), 'MMM d, h:mm a')}</span>
              </div>
              <p className="text-sm text-gray-700 whitespace-pre-wrap">{c.body}</p>
            </div>
          ))
        )}
      </div>

      <form onSubmit={handleSubmit} className="flex space-x-2 mt-4">
        <input
          type="text"
          className="input-field flex-1"
          placeholder="Write a comment..."
          value={newComment}
          onChange={(e) => setNewComment(e.target.value)}
        />
        <button type="submit" disabled={!newComment.trim()} className="btn-primary px-4 py-2 shrink-0 flex items-center">
          <Send className="h-4 w-4" />
        </button>
      </form>
    </div>
  );
};

export default TaskComments;
