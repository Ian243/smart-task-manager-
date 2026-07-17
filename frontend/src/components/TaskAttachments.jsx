import React, { useState, useEffect, useRef } from 'react';
import api from '../api';
import { format } from 'date-fns';
import { Paperclip, Upload, File as FileIcon, Download } from 'lucide-react';

const TaskAttachments = ({ taskId, users }) => {
  const [attachments, setAttachments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef(null);

  useEffect(() => {
    fetchAttachments();
  }, [taskId]);

  const fetchAttachments = async () => {
    try {
      const res = await api.get(`/tasks/${taskId}/attachments`);
      setAttachments(res.data);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      await api.post(`/tasks/${taskId}/attachments`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      fetchAttachments();
    } catch (err) {
      console.error(err);
      alert('Failed to upload file.');
    }
    setUploading(false);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const formatSize = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const getAuthorName = (id) => {
    const u = users.find(u => u.id === id);
    return u ? u.name : 'Unknown';
  };

  const downloadUrl = (attachmentId) => {
    return `${api.defaults.baseURL || '/api/v1'}/tasks/${taskId}/attachments/${attachmentId}/download`;
  };

  if (loading) return <div className="text-sm text-gray-500 py-4">Loading attachments...</div>;

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-bold text-gray-900 flex items-center">
          <Paperclip className="h-5 w-5 mr-2 text-primary-500" />
          Attachments
        </h3>
        <div>
          <input 
            type="file" 
            className="hidden" 
            ref={fileInputRef} 
            onChange={handleUpload}
          />
          <button 
            type="button"
            disabled={uploading}
            onClick={() => fileInputRef.current?.click()}
            className="btn-primary text-xs px-3 py-1.5 flex items-center"
          >
            <Upload className="h-4 w-4 mr-1" />
            {uploading ? 'Uploading...' : 'Upload'}
          </button>
        </div>
      </div>
      
      <div className="grid grid-cols-1 gap-3 max-h-64 overflow-y-auto pr-2">
        {attachments.length === 0 ? (
          <p className="text-sm text-gray-500 italic">No attachments yet.</p>
        ) : (
          attachments.map(att => (
            <div key={att.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-100 hover:bg-gray-100 transition-colors">
              <div className="flex items-center space-x-3 overflow-hidden">
                <div className="p-2 bg-white rounded-md shrink-0">
                  <FileIcon className="h-5 w-5 text-gray-400" />
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate" title={att.original_filename}>
                    {att.original_filename}
                  </p>
                  <p className="text-xs text-gray-500 flex items-center space-x-2">
                    <span>{formatSize(att.file_size)}</span>
                    <span>&bull;</span>
                    <span>{getAuthorName(att.uploaded_by)}</span>
                    <span>&bull;</span>
                    <span>{format(new Date(att.created_at), 'MMM d, yyyy')}</span>
                  </p>
                </div>
              </div>
              <a 
                href={downloadUrl(att.id)} 
                target="_blank"
                rel="noreferrer"
                className="p-2 text-gray-400 hover:text-primary-600 transition-colors shrink-0"
                title="Download"
              >
                <Download className="h-5 w-5" />
              </a>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default TaskAttachments;
