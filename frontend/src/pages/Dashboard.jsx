import React, { useState, useEffect } from 'react';
import api from '../api';
import { BarChart as BarChartIcon, Users, CheckCircle, Clock } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';

const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/dashboard/summary')
      .then(res => {
        setStats(res.data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  if (loading) return <div className="p-8 text-center text-gray-500">Loading metrics...</div>;
  if (!stats) return <div className="p-8 text-center text-red-500">Failed to load metrics.</div>;

  const completedTasks = stats.status_counts.find(s => s.status === 'completed')?.count || 0;

  const cards = [
    { title: 'Total Tasks', value: stats.total_tasks, icon: BarChartIcon, color: 'text-blue-500', bg: 'bg-blue-50' },
    { title: 'Completed', value: completedTasks, icon: CheckCircle, color: 'text-green-500', bg: 'bg-green-50' },
    { title: 'Overdue', value: stats.overdue_tasks, icon: Clock, color: 'text-red-500', bg: 'bg-red-50' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {cards.map((c, i) => {
          const Icon = c.icon;
          return (
            <div key={i} className="glass-card p-6 flex items-center space-x-4">
              <div className={`p-4 rounded-xl ${c.bg}`}>
                <Icon className={`h-8 w-8 ${c.color}`} />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-500">{c.title}</p>
                <p className="text-3xl font-bold text-gray-900">{c.value}</p>
              </div>
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
        {/* Status Distribution Chart */}
        {stats.status_counts && (
          <div className="glass-card p-6">
            <h2 className="text-lg font-bold text-gray-900 mb-6">Task Status Distribution</h2>
            <div className="h-[300px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={stats.status_counts} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                  <XAxis 
                    dataKey="status" 
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: '#6B7280', fontSize: 12 }}
                    tickFormatter={(value) => value.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                  />
                  <YAxis 
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: '#6B7280', fontSize: 12 }}
                    allowDecimals={false}
                  />
                  <Tooltip 
                    cursor={{ fill: '#F3F4F6' }}
                    contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                  />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]} maxBarSize={50}>
                    {
                      stats.status_counts.map((entry, index) => {
                        const colors = {
                          'to_do': '#E5E7EB',
                          'in_progress': '#3B82F6',
                          'completed': '#10B981'
                        };
                        return <Cell key={`cell-${index}`} fill={colors[entry.status] || '#9CA3AF'} />;
                      })
                    }
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* User Workload Chart */}
        {stats.user_workload && (
          <div className="glass-card p-6">
            <h2 className="text-lg font-bold text-gray-900 mb-6">Team Workload (Active Tasks)</h2>
            <div className="h-[300px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={stats.user_workload} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                  <XAxis 
                    dataKey="assignee_name" 
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: '#6B7280', fontSize: 12 }}
                  />
                  <YAxis 
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: '#6B7280', fontSize: 12 }}
                    allowDecimals={false}
                  />
                  <Tooltip 
                    cursor={{ fill: '#F3F4F6' }}
                    contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                  />
                  <Bar dataKey="count" fill="#8B5CF6" radius={[4, 4, 0, 0]} maxBarSize={50} name="Active Tasks" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
